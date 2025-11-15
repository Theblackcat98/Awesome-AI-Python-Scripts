"""
title: Actor-Critic Loop
author: TheBlackCat99
author_url: https://github.com/TheBlackCat98/OpenWebUI-Tools
description: Implements a Worker-Evaluator (Actor-Critic) loop for OpenWebUI.
required_open_webui_version: 0.5.0
requirements: langchain-openai>=0.1.0
version: 1.0
license: MIT
"""

# Filename: actor_critic_pipe.py
# Location: open-webui/backend/apps/pipes/

import os
import asyncio
from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field

# Import OpenWebUI's built-in functions
try:
    from open_webui.main import generate_chat_completions
    from open_webui.models.users import User
except ImportError as e:
    print(f"Warning: Could not import OpenWebUI functions: {e}")
    # Fallback to langchain if OpenWebUI functions are not available
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
    except ImportError:
        raise ImportError(
            "Dependencies not found. Please ensure either OpenWebUI or langchain-openai is installed."
        )


# Helper function to send status updates to the OpenWebUI frontend
async def send_status_message(
    __event_emitter__: Optional[Callable[[dict], Awaitable[None]]],
    status: str,
    done: bool = False,
):
    if __event_emitter__:
        await __event_emitter__(
            {"type": "status", "data": {"description": status, "done": done}}
        )


class Pipe:
    """
    An OpenWebUI Pipe that implements a Worker-Evaluator (Actor-Critic) loop.
    1. A "Worker" LLM generates an answer to the user's query.
    2. An "Evaluator" LLM reviews the answer.
    3. If the answer is satisfactory, it's sent to the user.
    4. If not, the feedback is given back to the Worker for revision.
    """

    class Valves(BaseModel):
        # Agent configuration
        AGENT_NAME: str = Field(
            default="Critique & Revise Agent",
            description="The name of the agent in the model selector.",
        )
        AGENT_ID: str = Field(
            default="critique-revise-agent",
            description="The unique ID for the agent pipe.",
        )
        
        # Model configuration
        USE_LOCAL_MODELS: bool = Field(
            default=True,
            description="Enable use of local models via OpenAI-compatible API",
        )
        LOCAL_API_BASE_URL: str = Field(
            default="http://localhost:11434/v1",
            description="Base URL for local OpenAI-compatible API (e.g., Ollama, LocalAI)",
        )
        LOCAL_API_KEY: str = Field(
            default="", 
            description="API key for local models (if required)"
        )
        WORKER_MODEL_ID: str = Field(
            default="gpt-oss:latest",
            description="Model ID for the worker (Actor) that generates answers.",
        )
        EVALUATOR_MODEL_ID: str = Field(
            default="gpt-oss:latest",
            description="Model ID for the evaluator (Critic) that reviews answers.",
        )
        MAX_REVISIONS: int = Field(
            default=2,
            description="Maximum number of revision loops before giving up.",
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        # Store context from the request for helper methods
        self.__user__ = None
        self.__request__ = None
        self.__event_emitter__ = None

    def pipes(self) -> list[dict[str, str]]:
        return [{"id": self.valves.AGENT_ID, "name": self.valves.AGENT_NAME}]

    async def _generate_completion(self, model: str, messages: list, temperature: float = 0.7) -> str:
        """A helper function to call the LLM and get a response using OpenWebUI's API."""
        try:
            form_data = {
                "model": model,
                "messages": messages,
                "stream": False,
                "temperature": temperature,
            }

            response_data = await generate_chat_completions(
                self.__request__,
                form_data,
                user=self.__user__,
            )
            return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error in _generate_completion: {str(e)}")
            raise

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]],
        __request__: object,
        # These are unused but part of the required signature for some pipes
        __event_call__=None,
        __task__=None,
        __model__=None,
    ):
        """
        The main logic for the Worker-Evaluator loop.
        This is an AsyncGenerator that yields the final response.
        """
        try:
            # Store context from the request for helper methods
            self.__user__ = User(**__user__) if __user__ else None
            self.__request__ = __request__
            self.__event_emitter__ = __event_emitter__

            user_query = ""
            if body.get("messages") and "content" in body["messages"][-1]:
                user_content = body["messages"][-1]["content"]
                if isinstance(user_content, list):
                    # Handle the case where content is a list (e.g., with images)
                    for item in user_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            user_query = item["text"]
                            break
                else:
                    user_query = user_content

            if not user_query:
                yield "I didn't receive a question. Please ask something."
                return

            await self._send_status("Initializing critique-revise process...", False)

            final_answer = f"Could not generate a satisfactory answer after {self.valves.MAX_REVISIONS} revisions."
            revision_feedback = ""

            for i in range(self.valves.MAX_REVISIONS + 1):
                attempt_num = i + 1
                await self._send_status(
                    f"Attempt {attempt_num}: Generating answer...",
                    False
                )

                # Prepare the prompt for the worker model
                worker_prompt = """You are a helpful assistant. Your goal is to provide a clear, accurate, and concise answer to the user's query."""
                
                if revision_feedback:
                    worker_prompt += f"\n\nIMPORTANT: Your previous attempt was not satisfactory. You MUST revise it based on the following feedback:\n{revision_feedback}"
                
                worker_prompt += f"\n\nUser's query: {user_query}"
                
                worker_messages = [
                    {"role": "system", "content": worker_prompt},
                    {"role": "user", "content": user_query}
                ]

                # Generate the worker's response
                current_answer = await self._generate_completion(
                    model=self.valves.WORKER_MODEL_ID,
                    messages=worker_messages,
                    temperature=0.7
                )

                if i == self.valves.MAX_REVISIONS:
                    final_answer = current_answer
                    await self._send_status("Max revisions reached. Accepting final answer.", True)
                    break

                # Have the evaluator review the response
                await self._send_status(f"Attempt {attempt_num}: Evaluating answer...", False)

                evaluator_prompt = f"""You are a strict but fair evaluator. Your task is to critique an answer based on a user's question.
Your response MUST begin with one of two exact phrases:
1. 'SATISFACTORY' if the answer is high-quality, accurate, and directly addresses the user's question.
2. 'NOT SATISFACTORY:' if the answer has flaws. If so, you must provide a brief, constructive reason for the failure.

Original Question: "{user_query}"
Answer to Evaluate: "{current_answer}"

What is your evaluation?
"""
                evaluation = await self._generate_completion(
                    model=self.valves.EVALUATOR_MODEL_ID,
                    messages=[{"role": "user", "content": evaluator_prompt}],
                    temperature=0.1  # Use low temperature for more consistent evaluations
                )

                if evaluation.upper().startswith("SATISFACTORY"):
                    await self._send_status(f"Attempt {attempt_num}: Evaluation PASSED!", True)
                    final_answer = current_answer
                    break
                else:
                    await self._send_status(
                        f"Attempt {attempt_num}: Evaluation FAILED. Preparing for revision.",
                        False
                    )
                    revision_feedback = evaluation
                    await asyncio.sleep(1)

            yield final_answer

        except Exception as e:
            error_msg = f"An error occurred in the critique-revise pipe: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            # More user-friendly error message
            if "Connection" in str(e) or "timeout" in str(e).lower():
                error_msg = """
                I couldn't connect to the AI model service. Please check:
                1. Make sure the model service is running and accessible
                2. Check if the model names are correct
                3. Verify your internet connection if using a cloud-based model
                
                Technical details: {}
                """.format(str(e))
            
            yield error_msg
    
    async def _send_status(self, message: str, done: bool = False):
        """Helper method to send status updates."""
        if self.__event_emitter__:
            await self.__event_emitter__({
                "type": "status",
                "data": {"description": message, "done": done}
            })
