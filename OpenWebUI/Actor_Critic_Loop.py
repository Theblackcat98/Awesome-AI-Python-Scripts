# Filename: actor_critic_pipe.py
# Location: open-webui/backend/apps/pipes/

import os
import asyncio
from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field

# Ensure langchain_openai is available in your OpenWebUI environment
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
except ImportError:
    raise ImportError(
        "Dependencies not found. Please ensure langchain-openai is installed in the OpenWebUI environment."
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
        # The agent's name that will appear in the UI
        AGENT_NAME: str = Field(
            default="Critique & Revise Agent",
            description="The name of the agent in the model selector.",
        )
        # The ID for the agent
        AGENT_ID: str = Field(
            default="critique-revise-agent",
            description="The unique ID for the agent pipe.",
        )
        # **FIXED**: Make the API URL a configurable valve
        OLLAMA_API_BASE_URL: str = Field(
            default="http://localhost:11434/v1",
            description="The base URL for the local Ollama/OpenAI-compatible API.",
        )
        WORKER_MODEL_ID: str = Field(
            default="llama3:latest",
            description="The ID of the model that generates answers (The Actor).",
        )
        EVALUATOR_MODEL_ID: str = Field(
            default="gemma:latest",
            description="The ID of the model that critiques answers (The Critic).",
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
        self.worker_llm = None
        self.evaluator_llm = None
        self.is_setup = False

    def pipes(self) -> list[dict[str, str]]:
        return [{"id": self.valves.AGENT_ID, "name": self.valves.AGENT_NAME}]

    def setup(self):
        """Initializes the LLM clients using LangChain."""
        if self.is_setup:
            return

        # **FIXED**: Use the URL from Valves instead of an environment variable
        base_url = self.valves.OLLAMA_API_BASE_URL
        api_key = "ollama"  # Standard placeholder for local models

        self.worker_llm = ChatOpenAI(
            model=self.valves.WORKER_MODEL_ID, api_key=api_key, base_url=base_url
        )
        self.evaluator_llm = ChatOpenAI(
            model=self.valves.EVALUATOR_MODEL_ID, api_key=api_key, base_url=base_url
        )
        self.is_setup = True

    async def pipe(
        self,
        body: dict,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        *args,
        **kwargs,
    ):
        """
        The main logic for the Worker-Evaluator loop.
        This is an AsyncGenerator that yields the final response.
        """
        try:
            self.setup()

            user_query = ""
            if body.get("messages") and "content" in body["messages"][-1]:
                user_query = body["messages"][-1]["content"]

            if not user_query:
                yield "I didn't receive a question. Please ask something."
                return

            await send_status_message(
                __event_emitter__, "Initializing critique-revise process...", False
            )

            final_answer = f"Could not generate a satisfactory answer after {self.valves.MAX_REVISIONS} revisions."
            revision_feedback = ""

            for i in range(self.valves.MAX_REVISIONS + 1):
                attempt_num = i + 1
                await send_status_message(
                    __event_emitter__,
                    f"Attempt {attempt_num}: Worker LLM is generating an answer.",
                    False,
                )

                worker_system_prompt = "You are a helpful assistant. Your goal is to provide a clear, accurate, and concise answer to the user's query."
                if revision_feedback:
                    worker_system_prompt += f"\n\nIMPORTANT: Your previous attempt was not satisfactory. You MUST revise it based on the following feedback:\n{revision_feedback}"

                worker_messages = [
                    SystemMessage(content=worker_system_prompt),
                    HumanMessage(content=user_query),
                ]

                worker_response = await self.worker_llm.ainvoke(worker_messages)
                current_answer = worker_response.content

                if i == self.valves.MAX_REVISIONS:
                    final_answer = current_answer
                    await send_status_message(
                        __event_emitter__,
                        "Max revisions reached. Accepting final answer.",
                        True,
                    )
                    break

                await send_status_message(
                    __event_emitter__,
                    f"Attempt {attempt_num}: Evaluator LLM is reviewing the answer.",
                    False,
                )

                evaluator_prompt = f"""You are a strict but fair evaluator. Your task is to critique an answer based on a user's question.
Your response MUST begin with one of two exact phrases:
1. 'SATISFACTORY' if the answer is high-quality, accurate, and directly addresses the user's question.
2. 'NOT SATISFACTORY:' if the answer has flaws. If so, you must provide a brief, constructive reason for the failure.

Original Question: "{user_query}"
Answer to Evaluate: "{current_answer}"

What is your evaluation?
"""
                evaluator_messages = [HumanMessage(content=evaluator_prompt)]
                evaluator_response = await self.evaluator_llm.ainvoke(
                    evaluator_messages
                )
                evaluation = evaluator_response.content.strip()

                if evaluation.upper().startswith("SATISFACTORY"):
                    await send_status_message(
                        __event_emitter__,
                        f"Attempt {attempt_num}: Evaluation PASSED!",
                        True,
                    )
                    final_answer = current_answer
                    break
                else:
                    await send_status_message(
                        __event_emitter__,
                        f"Attempt {attempt_num}: Evaluation FAILED. Preparing for revision.",
                        False,
                    )
                    revision_feedback = evaluation
                    await asyncio.sleep(2)

            yield final_answer

        except Exception as e:
            print(f"An error occurred in the critique-revise pipe: {e}")
            yield f"I'm sorry, an error occurred in my internal review process. Please try again. Error: {e}"
