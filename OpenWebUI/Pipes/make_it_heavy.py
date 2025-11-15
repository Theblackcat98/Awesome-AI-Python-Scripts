"""
title: Multi-Agent Synthesis
description: Spawns multiple agents using different models, then synthesizes their responses.
author: Enhanced by Gemini
version: 1.2.0
requirements: []
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Callable, Awaitable
import asyncio
import time
import html
import re

# Import OpenWebUI utilities at the top level
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from open_webui.constants import TASKS  # <-- 1. IMPORTED TASKS
from fastapi import Request


class Pipe:
    class Valves(BaseModel):
        agent_count: int = Field(
            default=3,
            ge=1,
            le=6,
            description="Number of parallel agents to spawn (1-6)",
        )
        agent_models: List[str] = Field(
            default_factory=lambda: [
                "llama3:latest",
                "llama3:latest",
                "llama3:latest",
            ],
            description="Models to use for each agent (will cycle if fewer than agent_count)",
        )
        synthesis_model: str = Field(
            default="llama3:latest", description="Model to use for final synthesis"
        )
        aggregation_strategy: str = Field(
            default="synthesize",
            description="Aggregation method: 'synthesize', 'vote', or 'concat'",
        )
        max_tokens: int = Field(
            default=512, ge=50, le=2048, description="Maximum tokens per agent response"
        )
        agent_system_prompt: str = Field(
            default="You are a helpful assistant. Provide clear, concise answers.",
            description="Base system prompt for all agents",
        )
        agent_styles: List[str] = Field(
            default_factory=lambda: [
                "Answer directly and concisely.",
                "Provide step-by-step reasoning.",
                "Consider alternative perspectives and potential issues.",
            ],
            description="Different style prompts for agent diversity",
        )
        enable_debug: bool = Field(
            default=False, description="Include debug information in output"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.__event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None

    def pipes(self) -> list[dict]:
        """Required method to register the pipe as a model."""
        return [
            {"id": "multi-agent-synthesis", "name": "Multi-Agent Synthesis"},
        ]

    async def emit_status(self, message: str, done: bool = False):
        """Helper to send status updates to the UI."""
        if self.__event_emitter__:
            await self.__event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "description": message,
                        "done": done,
                    },
                }
            )

    async def emit_citation(self, title: str, content: str, url: str):
        """Helper to send citation data to the UI."""
        if self.__event_emitter__:
            await self.__event_emitter__(
                {
                    "type": "citation",
                    "data": {
                        "document": [content],
                        "metadata": [{"source": url, "html": False}],
                        "source": {"name": title},
                    },
                }
            )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison in voting."""
        text = html.unescape(text.strip().lower())
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        return text

    async def _call_model(
        self, messages: List[Dict], model: str, __request__: Request, __user__: Dict
    ) -> str:
        """Call a model using OpenWebUI's internal chat completion."""
        try:
            # Get proper user object if __user__ is a dict
            if isinstance(__user__, dict) and "id" in __user__:
                user_obj = Users.get_user_by_id(__user__["id"])
            else:
                user_obj = __user__

            # Create a body for the model call
            body = {
                "model": model,
                "messages": messages,
                "max_tokens": self.valves.max_tokens,
                "temperature": 0.7,
                "stream": False,
            }

            # Use OpenWebUI's internal function with proper user object
            response = await generate_chat_completion(__request__, body, user_obj)

            # Extract content from response
            if isinstance(response, dict):
                if "choices" in response and len(response["choices"]) > 0:
                    return response["choices"][0]["message"]["content"]
                elif "content" in response:
                    return response["content"]

            return str(response)

        except Exception as e:
            return f"Error calling model {model}: {str(e)}"

    async def _run_agent(
        self, agent_idx: int, query: str, __request__: Request, __user__: Dict
    ) -> Dict[str, Any]:
        """Run a single agent with its assigned style."""
        # Get model for this agent (cycle through available models)
        model = self.valves.agent_models[agent_idx % len(self.valves.agent_models)]

        # Get style for this agent (cycle through available styles)
        style = self.valves.agent_styles[agent_idx % len(self.valves.agent_styles)]

        await self.emit_status(f"Agent {agent_idx + 1} ({model}) starting...", False)

        # Prepare messages
        system_prompt = (
            f"{self.valves.agent_system_prompt}\n\nSpecific instructions: {style}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        try:
            start_time = time.time()
            content = await self._call_model(messages, model, __request__, __user__)
            duration = time.time() - start_time

            await self.emit_status(
                f"Agent {agent_idx + 1} ({model}) finished in {duration:.2f}s.", True
            )

            return {
                "agent_id": agent_idx + 1,
                "model": model,
                "style": style,
                "content": content.strip(),
                "duration": duration,
                "success": True,
            }
        except Exception as e:
            await self.emit_status(f"Agent {agent_idx + 1} ({model}) failed.", True)
            return {
                "agent_id": agent_idx + 1,
                "model": model,
                "style": style,
                "content": f"Agent failed: {str(e)}",
                "duration": 0,
                "success": False,
            }

    def _aggregate_responses(self, agent_results: List[Dict], query: str) -> str:
        """Aggregate agent responses based on the chosen strategy."""
        strategy = self.valves.aggregation_strategy.lower()
        successful_results = [r for r in agent_results if r["success"]]

        if not successful_results:
            return "All agents failed to provide responses."

        if strategy == "concat":
            # Simple concatenation with headers
            parts = []
            for result in successful_results:
                parts.append(
                    f"**Agent {result['agent_id']} ({result['model']}):**\n{result['content']}"
                )
            return "\n\n".join(parts)

        elif strategy == "vote":
            # Find most common response (normalized)
            content_map = {}
            for result in successful_results:
                normalized = self._normalize_text(result["content"])
                if normalized not in content_map:
                    content_map[normalized] = []
                content_map[normalized].append(result["content"])

            if content_map:
                # Get the most frequent response
                most_common = max(content_map.items(), key=lambda x: len(x[1]))
                if len(most_common[1]) > 1:
                    return most_common[1][0]  # Return original text of most common

            # If no clear winner, fall back to synthesis
            strategy = "synthesize"

        if strategy == "synthesize":
            # Create synthesis prompt
            synthesis_prompt = (
                "You are tasked with synthesizing multiple AI responses into one coherent, "
                "accurate, and well-structured answer. Consider all perspectives and create "
                "a unified response that incorporates the best insights from each.\n\n"
                "Original question:\n"
                f"{query}\n\n"
                "AI Agent Responses:\n\n"
            )

            for result in successful_results:
                synthesis_prompt += (
                    f"Agent {result['agent_id']} response:\n{result['content']}\n\n"
                )

            synthesis_prompt += (
                "Please provide a synthesized response that:\n"
                "1. Combines the best insights from all responses\n"
                "2. Resolves any contradictions\n"
                "3. Is well-structured and coherent\n"
                "4. Directly addresses the original question\n\n"
                "Synthesized response:"
            )

            return synthesis_prompt

        # Default fallback
        return successful_results[0]["content"]

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __request__: Optional[Request] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __task__: Optional[TASKS] = None,  # <-- 2. ADDED __task__ PARAMETER
    ) -> str:
        """Main pipe function that orchestrates multi-agent processing."""

        self.__event_emitter__ = __event_emitter__

        # 3. --- ADDED GUARD CLAUSE ---
        # Handle non-chat tasks (like title generation) by just calling the synthesis model directly
        if __task__ and __task__ != TASKS.DEFAULT:
            await self.emit_status(f"Handling task: {__task__}", False)
            
            # We'll just use the synthesis model for a fast response
            synthesis_model = self.valves.synthesis_model
            messages = body.get("messages", [])
            
            # Add a simple system prompt if one isn't present
            if not any(msg["role"] == "system" for msg in messages):
                 messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})

            try:
                response = await self._call_model(
                    messages,
                    synthesis_model,
                    __request__,
                    __user__,
                )
                await self.emit_status(f"Task {__task__} complete.", True)
                return response
            except Exception as e:
                await self.emit_status(f"Task {__task__} failed: {str(e)}", True)
                return f"Error during {__task__} task: {str(e)}"
        # --- END GUARD CLAUSE ---

        # Regular multi-agent logic only runs for default chat tasks
        await self.emit_status("Initializing Multi-Agent Synthesis...", False)

        if not __request__ or not __user__:
            await self.emit_status("Error: Missing required request context.", True)
            return "Error: Missing required request context for model execution."

        start_time = time.time()

        try:
            # Extract user query
            messages = body.get("messages", [])
            if not messages:
                await self.emit_status("Error: No messages provided.", True)
                return "No messages provided."

            # Get the last user message
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg
                    break

            if not user_message or not user_message.get("content", "").strip():
                await self.emit_status("Error: No user query found.", True)
                return "No user query found."

            query = user_message["content"].strip()

            # Run agents in parallel
            await self.emit_status(f"Spawning {self.valves.agent_count} agents...", False)
            agent_tasks = []
            for i in range(self.valves.agent_count):
                task = self._run_agent(i, query, __request__, __user__)
                agent_tasks.append(task)

            # Wait for all agents to complete
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # Handle any exceptions from gather
            processed_results = []
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "agent_id": i + 1,
                            "model": "unknown",
                            "style": "unknown",
                            "content": f"Agent failed with exception: {str(result)}",
                            "duration": 0,
                            "success": False,
                        }
                    )
                else:
                    processed_results.append(result)

            # Emit citations for successful agent responses
            for result in processed_results:
                if result["success"]:
                    await self.emit_citation(
                        title=f"Agent {result['agent_id']} ({result['model']})",
                        content=result["content"],
                        url=f"agent-{result['agent_id']}-response",
                    )

            # Aggregate responses
            aggregation_strategy = self.valves.aggregation_strategy.lower()
            if aggregation_strategy == "synthesize":
                await self.emit_status(
                    f"Synthesizing responses with {self.valves.synthesis_model}...",
                    False,
                )
                synthesis_prompt = self._aggregate_responses(processed_results, query)

                # Call synthesis model
                synthesis_messages = [
                    {
                        "role": "system",
                        "content": "You are an expert at synthesizing multiple AI responses into coherent answers.",
                    },
                    {"role": "user", "content": synthesis_prompt},
                ]

                try:
                    final_response = await self._call_model(
                        synthesis_messages,
                        self.valves.synthesis_model,
                        __request__,
                        __user__,
                    )
                except Exception as e:
                    final_response = (
                        f"Synthesis failed: {str(e)}\n\n"
                        "Falling back to concatenated responses:\n\n"
                    )
                    final_response += self._aggregate_responses(
                        processed_results, query
                    )
            else:
                if aggregation_strategy == "vote":
                    await self.emit_status("Tallying agent votes...", False)
                else:  # concat
                    await self.emit_status("Concatenating agent responses...", False)

                final_response = self._aggregate_responses(processed_results, query)

            # Add debug information if enabled
            if self.valves.enable_debug:
                total_time = time.time() - start_time
                debug_info = f"\n\n---\n**Debug Info:**\n"
                debug_info += f"- Total processing time: {total_time:.2f}s\n"
                debug_info += f"- Agents used: {self.valves.agent_count}\n"
                debug_info += f"- Successful agents: {len([r for r in processed_results if r['success']])}\n"
                debug_info += (
                    f"- Aggregation strategy: {self.valves.aggregation_strategy}\n"
                )
                final_response += debug_info

            await self.emit_status("Multi-Agent Synthesis complete.", True)
            return final_response

        except Exception as e:
            await self.emit_status(f"Error: {str(e)}", True)
            return f"Error in multi-agent processing: {str(e)}"