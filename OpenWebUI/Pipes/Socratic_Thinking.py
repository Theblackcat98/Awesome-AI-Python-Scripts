"""
title: Socratic Thinking
author: TheBlackCat99
author_url: https://github.com/TheBlackCat98/OpenWebUI-Tools
description: A pipe that uses a generator-evaluator loop to refine answers through self-correction, mimicking the Socratic method.
required_open_webui_version: 0.5.0
requirements:
version: 1.4
licence: MIT
"""

import os
import re
import asyncio
from typing import Callable, Awaitable, Protocol

from pydantic import BaseModel, Field

from open_webui.main import generate_chat_completions
from open_webui.models.users import User

# --- Constants for Prompts ---

GENERATOR_PROMPT_TEMPLATE = """
You are a helpful and brilliant expert assistant. Your goal is to provide the most accurate, comprehensive, and well-reasoned answer to the user's query.

Analyze the user's query carefully and generate a clear and detailed response.

**User Query:**
{query}
{feedback}
"""

EVALUATOR_PROMPT_TEMPLATE = """
You are a meticulous and impartial critic. Your role is to evaluate a generated answer based on its accuracy, completeness, relevance, and clarity in relation to the original user query. You must be strict and objective.

**Original User Query:**
{query}

**Generated Answer to Evaluate:**
{answer}

---
**Evaluation Task:**

1.  Compare the "Generated Answer" against the "Original User Query".
2.  If the answer is fully satisfactory, accurate, and completely addresses the query without any errors or significant omissions, respond with ONLY the word: `PASS`.
3.  If the answer is flawed in any way (e.g., inaccurate, incomplete, irrelevant, unclear, contains hallucinations), respond with the word `FAIL` on the first line, followed by a concise, constructive critique on the next lines. The critique should explain EXACTLY what is wrong and provide clear guidance on how to improve the answer.

**Example of a failed evaluation:**
FAIL
The answer incorrectly identifies the capital of Australia. It also fails to mention the primary export products, which was implicitly part of the "economic overview" requested by the user. The explanation of the political system is too simplistic.
"""


class SendCitationType(Protocol):
    def __call__(self, url: str, title: str, content: str) -> Awaitable[None]: ...


def get_send_citation(__event_emitter__: Callable[[dict], Awaitable[None]] | None) -> SendCitationType:
    async def send_citation(url: str, title: str, content: str):
        if __event_emitter__ is None:
            return
        await __event_emitter__(
            {
                "type": "citation",
                "data": {
                    "document": [content],
                    "metadata": [{"source": url, "html": False}],
                    "source": {"name": title},
                },
            }
        )
    return send_citation


class Pipe:
    """
    This pipe implements the "Socratic Thinking" method, where one LLM generates an answer
    and another LLM evaluates it. If the evaluation fails, the feedback is used to
    regenerate the answer, creating a loop of self-correction.
    """

    # `Valves` are the user-configurable settings for this pipe.
    class Valves(BaseModel):
        ENABLED: bool = Field(
            default=True,
            description="Enable or disable the Socratic Thinking pipe.",
        )
        GENERATOR_MODEL: str = Field(
            default="gpt-oss:latest",
            description="The model used to generate the initial and refined answers.",
        )
        EVALUATOR_MODEL: str = Field(
            default="gpt-oss:latest",
            description="A smaller, faster model used to critique the generator's answers.",
        )
        MAX_LOOPS: int = Field(
            default=3,
            ge=1,
            le=5,
            description="The maximum number of refinement loops before returning the best-effort answer.",
        )
        TEMPERATURE: float = Field(
            default=0.7,
            ge=0.0,
            le=2.0,
            description="The temperature for the generator model to control creativity.",
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()
        # These will be populated by the `pipe` method
        self.__user__: User | None = None
        self.__request__: object | None = None
        self.__event_emitter__: Callable[[dict], Awaitable[None]] | None = None
        self.send_citation: SendCitationType | None = None

    def pipes(self) -> list[dict[str, str]]:
        """
        This method returns a list of models that this pipe provides.
        """
        return [
            {
                "id": "socratic-thinking",
                "name": "Socratic Thinking",
            }
        ]

    async def _generate_completion(
        self, model: str, messages: list, temperature: float
    ) -> str:
        """A helper function to call the LLM and get a response."""

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

    async def _generate_answer(self, query: str, feedback: str, loop_count: int) -> str:
        """Calls the generator model to produce an answer."""
        await self.emit_status(
            f"Thinking... (Attempt {loop_count}/{self.valves.MAX_LOOPS})", done=False
        )

        feedback_section = ""
        if feedback:
            feedback_section = f"\n**Feedback on Previous Attempt:**\n{feedback}"

        prompt = GENERATOR_PROMPT_TEMPLATE.format(
            query=query, feedback=feedback_section
        )
        messages = [{"role": "user", "content": prompt}]

        # Send generator prompt to citations
        if self.send_citation:
            await self.send_citation(
                url=f"socratic-thinking-loop-{loop_count}",
                title=f"Generator Prompt (Loop {loop_count})",
                content=prompt
            )

        answer = await self._generate_completion(
            self.valves.GENERATOR_MODEL, messages, self.valves.TEMPERATURE
        )

        # Send generator response to citations
        if self.send_citation:
            await self.send_citation(
                url=f"socratic-thinking-loop-{loop_count}",
                title=f"Generator Response (Loop {loop_count})",
                content=answer
            )
        return answer

    async def _evaluate_answer(self, query: str, answer: str, loop_count: int = 1) -> str:
        """Calls the evaluator model to critique an answer."""
        await self.emit_status("Evaluating answer...", done=False)

        prompt = EVALUATOR_PROMPT_TEMPLATE.format(query=query, answer=answer)
        messages = [{"role": "user", "content": prompt}]
        
        # Send evaluator prompt to citations
        if self.send_citation:
            await self.send_citation(
                url=f"socratic-thinking-loop-{loop_count}",
                title=f"Evaluator Prompt (Loop {loop_count})",
                content=prompt
            )

        # Use a low temperature for the evaluator to get consistent, objective feedback
        evaluation = await self._generate_completion(
            self.valves.EVALUATOR_MODEL, messages, 0.1
        )
        
        # Send evaluator response to citations
        if self.send_citation:
            await self.send_citation(
                url=f"socratic-thinking-loop-{loop_count}",
                title=f"Evaluator Response (Loop {loop_count})",
                content=evaluation
            )
            
        return evaluation.strip()

    async def emit_status(self, message: str, done: bool):
        """Emits a status update to the user interface."""
        if self.__event_emitter__:
            await self.__event_emitter__(
                {
                    "type": "status",
                    "data": {"description": message, "done": done},
                }
            )

    async def emit_message(self, message: str):
        """Emits a chat message to the user interface."""
        if self.__event_emitter__:
            await self.__event_emitter__(
                {
                    "type": "message",
                    "data": {"content": message},
                }
            )

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None,
        __request__: object,
        # These are unused but part of the required signature for some pipes
        __event_call__=None,
        __task__=None,
        __model__=None,
    ) -> str:
        """
        The main execution method for the Socratic Thinking pipe.
        """
        if not self.valves.ENABLED:
            return ""

        # Store context from the request for helper methods
        self.__user__ = User(**__user__)
        self.__request__ = __request__
        self.__event_emitter__ = __event_emitter__
        
        # Initialize citation sender
        self.send_citation = get_send_citation(__event_emitter__)

        messages = body.get("messages", [])
        if not messages:
            return ""

        user_query = messages[-1].get("content", "").strip()
        if not user_query:
            return ""

        current_answer = ""
        feedback_history = ""

        for i in range(self.valves.MAX_LOOPS):
            loop_count = i + 1

            # 1. Generate an answer
            current_answer = await self._generate_answer(
                user_query, feedback_history, loop_count
            )

            # 2. Evaluate the answer
            evaluation = await self._evaluate_answer(user_query, current_answer, loop_count)

            # 3. Decide whether to pass or refine
            # --- START OF CORRECTION ---
            # Use regex to find the word 'PASS' case-insensitively. This is more robust
            # than checking if the string starts with 'PASS'.
            is_pass = re.search(r"\bPASS\b", evaluation, re.IGNORECASE)

            if is_pass:
                await self.emit_status(
                    "Evaluation passed. Finalizing answer.", done=True
                )
                await self.emit_message(current_answer)
                return ""  # Success, end the process

            # If 'PASS' is not found, the entire evaluation is treated as the critique.
            # This is more effective as it includes the model's own reasoning.
            critique = evaluation
            feedback_history += (
                f"\n\n--- Critique on Attempt #{loop_count} ---\n{critique}"
            )

            # --- END OF CORRECTION ---

            # Inform the user about the refinement process
            await self.emit_message(
                f"**Critique on Attempt #{loop_count}:**\n> {critique}\n\n*Refining the answer based on this feedback...*\n"
            )

        # If the loop finishes, it means MAX_LOOPS was reached
        await self.emit_status(
            "Max refinement attempts reached. Providing the best-effort answer.",
            done=True,
        )
        warning_message = (
            "**Warning:** The following answer is the model's best attempt but could not be fully validated "
            f"after {self.valves.MAX_LOOPS} refinement cycles.\n\n---\n\n"
        )
        await self.emit_message(warning_message + current_answer)

        return ""
