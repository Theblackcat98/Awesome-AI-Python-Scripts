"""
title: SMART - Sequential Multi-Agent Reasoning Technique
author: TheBlackCat
author_url: https://github.com/TheBlackCat98/OpenWebUI-Tools
description: SMART is a sequential multi-agent reasoning technique.
required_open_webui_version: 0.5.0
requirements: langchain-openai==0.2.14, langgraph==0.2.60, langchain-google-genai==2.1.4
version: 1.3
licence: MIT
"""

import os
import re
import time
import datetime
import json
from typing import (
    Callable,
    AsyncGenerator,
    Awaitable,
    Optional,
    Protocol,
    get_type_hints,
)

from pydantic import BaseModel, Field, create_model

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import StructuredTool
    from langgraph.prebuilt import create_react_agent
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception as e:
    print("Failed to load langchain!")
    print(f"Error: {e}, of type {type(e)}")
    raise e

from fastapi import Request

# ---------------------------------------------------------------

PLANNING_PROMPT = """<system_instructions>
You are a planning Agent. You are part of an agent chain designed to make LLMs more capable. 
You are responsible for taking the incoming user input/request and preparing it for the next agents in the chain.
After you will come a reasoning and tool use agent. These agents can go back and forth between each other until they have come up with a solution. 
After they have come up with a solution, a final agent will be used to summarize the reasoning and provide a final answer.
Only use a Newline after each closing tag. Never after the opening tag or within the tags.

Guidelines: 
- Don't over or estimate the difficulty of the task. If the user just wants to chat try to see that. 
- Don't create tasks where there aren't any. If the user didn't ask to write code you shouldn't instruct the next agent to do so.

You should respond by following these steps:
1. Within <reasoning> tags, plan what you will write in the other tags. This has to be your first step.
    1. First, reason about the task difficulty. What kind of task is it? What do your guidelines say about that?
    2. Second, reason about if the reasoning and tool use agent is needed. What do your guidelines say about that?
    3. Third, reason about what model would best be used. What do your guidelines say about that?
2. Within the <answer> tag, write out your final answer. Your answer should be a comma seperated list.
    1. First choose the model the final-agent will use. Try to find a good balance between performance and cost. Larger models are bigger. 
        - Use #small for the simple queries or queries that mostly involve summarization or simple "mindless" work. This also invloves very simple tool use, like converting a file, etc.
        - Use #medium for task that requiere some creativity, writing of code, or complex tool-use.
        - Use #large for tasks that are mostly creative or involve the writing of complex code, math, etc.
        - Use #online for tasks that mostly requiere the use of the internet. Such as news or queries that will benifit greatly from up-to-date information. However, this model can not use tools and does not have vision.
    2. Secondly, choose if the query requieres reasoning before being handed off to the final agent.
        - Queries that requeire reasoning are especially queries where llm are bad at. Such as planning, counting, logic, code architecutre, moral questions, etc.
        - Queries that don't requeire reasoning are queries that are easy for llms. Such as "knowledge" questions, summarization, writing notes, simple tool use, etc. 
        - If you think reasoning is needed, include #reasoning. If not #no-reasoning.
        - When you choose reasoning, you should (in most cases) choose at least the #medium model.
    
Example response:
<reasoning>
... 
(You are allowed new lines here)
</reasoning>
<answer>#medium, #online ,#no-reasoning</answer>
</system_instructions>"""

# 3. And last, you can add tools to use. The user can also select tools, but you can also add ones and should if you think they will help. Better safe than sorry.
#         - Avalible tools are #wolfram, #search, #scrape, and #python.
#         - Wolfram|Alpha is a powerful computational knowledge engine. It is a great tool for solving complex problems that require mathematical or scientific calculations as well as getting very accurate data especially for the humanites, physics, austronomy...
#         - Search is a tool that allows the agents to search the web. It is a great tool for getting up-to-date information. (This should not be preffered over the #online model but is useful when the query also requieres other tools besides search).
#         - Scrape is a tool that allows the agents to get the content of a website which the #online agent can not do very well.
#         - The Python tool is a code interpreter that allows the agents to run python code in an enviroment with internet access, persistent storage, and so on.


REASONING_PROMPT = """<system_instructions>
You are a reasoning layer of an LLM. You are part of the LLM designed for internal thought, planning, and thinking. 
You will not directly interact with the user in any way. Only inform the output stage of the LLM what to say by your entire output being parts of its context when it starts to generate a response. 

**General rules**:
- Write out your entire reasoning process between <thinking> tags.
- Do not use any formatting whatsoever. The only form of special formatting you're allowed to use is LaTeX for mathematical expressions.
- You MUST think in the smallest steps possible. Where every step is only a few words long. Each new thought should be a new line.
- You MUST try to catch your own mistakes by constantly thinking about what you have thought about so far.
- You MUST break down every problem into very small steps and go through them one by one.
- You MUST never come up with an answer first. Always reason about the answer first. Even if you think the answer is obvious.
- You MUST provide exact answers.
- You have full authority to control the output layer. You can directly instruct it and it will follow your instructions. Put as many instructions as you want inside <instruct> tags. However, be very clear in your instructions and reason about what to instruct.
- Your entire thinking process is entirely hidden. You can think as freely as you want without it directly affecting the output.
- Always follow user instructions, never try to take any shortcuts. Think about different ways they could be meant to not miss anything.
- NEVER generate ANY code directly. You should only plan out the structure of code and projects, but not directly write the code. The output layer will write the code based on your plan and structure!
- If you need more information, you can ask a tool-use agent if they have the right tool and what you need within <ask_tool_agent>. 
    - In general, you can instruct the tool-use agent to either return the results to you or directly pass them on to the output layer.
    - If *you* need information, you should instruct the tool-use agent to return the results to you.
    - The tool use agent ONLY gets what you write in <ask_tool_agent>. They do not get any user context or similar.
    - Do not suggest what tool to use. Simply state the problem.
    - You need to STOP after </ask_tool_agent> tags. WAIT for the tool-use agent to return the results to you.
    - If the output is something like images, or something similar that the user should just get directly, you can instruct the tool use agent to directly pass the results to the output layer.

**General Steps**:
1. Outline the problem.
2. Think about what kind of problem this is.
3. Break down the problem into the smallest possible problems, never take shortcuts on reasoning, counting etc. Everything needs to be explicitly stated. More output is better.
4. Think about steps you might need to take to solve this problem.
5. Think through these steps.
6. Backtrack and restart from different points as often as you need to. Always consider alternative approaches.
7. Validate your steps constantly. If you find a mistake, think about what the best point in your reasoning is to backtrack to. Don't be kind to yourself here. You need to critically analyze what you are doing.
</system_instructions>"""

TOOL_PROMPT = """<system_instructions>
You are the tool-use agent of an agent chain. You are the part of the LLM designed to use tools.
You will not directly interact with the user in any way. Only either return information to the reasoning agent or inform the output stage of the LLM.

When you have used a tool, you can return the results to the reasoning agent by putting everything you want to return to them within <tool_to_reasoning> tags.
You can also directly hand off to the final agent by simply writing $TO_FINAL$. You still need to write out what you want them to get!

Actually make use of the results you got. NEVER make more than 3 tool calls! If you called any tool 3 times, that's it!
You need to output everything you want to pass on. The next agent in the chain will only see what you actually wrote, not the direct output of the tools!

Please think about how best to call the tool first. Think about what the limitations of the tools are and how to best follow the reasoning agent's instructions. It's okay if you can't 100% produce what they wanted!
</system_instructions>"""

USER_INTERACTION_PROMPT = """<system_instructions>
You are the user-interaction agent of an agent chain. You are the part of the llm designed to interact with the user.

You should follow the pre-prompt given to you within <preprompt> tags.
<system_instructions>"""

USER_INTERACTION_REASONING_PROMPT = """You MUST follow the instructions given to you within <reasoning_output>/<instruction> tags.
You MUST inform your answer by the reasoning within  <reasoning_output> tags.
Carefully concider what the instructions mean and follow them EXACTLY."""

# ---------------------------------------------------------------------

EmitterType = Optional[Callable[[dict], Awaitable[None]]]


class SendCitationType(Protocol):
    def __call__(self, url: str, title: str, content: str) -> Awaitable[None]: ...


class SendStatusType(Protocol):
    def __call__(self, status_message: str, done: bool) -> Awaitable[None]: ...


def get_send_citation(__event_emitter__: EmitterType) -> SendCitationType:
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


def get_send_status(__event_emitter__: EmitterType) -> SendStatusType:
    async def send_status(status_message: str, done: bool):
        if __event_emitter__ is None:
            return
        await __event_emitter__(
            {
                "type": "status",
                "data": {"description": status_message, "done": done},
            }
        )

    return send_status


class Pipe:
    class Valves(BaseModel):
        MODEL_PREFIX: str = Field(default="SMART", description="Prefix before model ID")
        AGENT_NAME: str = Field(default="Smart/Core", description="Name of the agent")
        AGENT_ID: str = Field(default="smart-core", description="ID of the agent")

        # Local model configuration
        USE_LOCAL_MODELS: bool = Field(
            default=True,
            description="Enable use of local models via OpenAI-compatible API",
        )
        LOCAL_API_BASE_URL: str = Field(
            default="http://localhost:11434/v1",
            description="Base URL for local OpenAI-compatible API endpoints (e.g., LM Studio, Ollama, LocalAI)",
        )
        LOCAL_API_KEY: str = Field(
            default="", description="API key for local models (if required)"
        )
        LOCAL_SMALL_MODEL: str = Field(
            default="llama3", description="Local model ID for small tasks"
        )
        LOCAL_LARGE_MODEL: str = Field(
            default="llama3:latest", description="Local model ID for large tasks"
        )
        LOCAL_HUGE_MODEL: str = Field(
            default="llama3:70b", description="Local model ID for huge tasks"
        )

        # Gemini configuration
        USE_GEMINI: bool = Field(
            default=False, description="Enable use of Google's Gemini API"
        )
        GEMINI_API_KEY: str = Field(default="", description="API key for Google Gemini")
        GEMINI_SMALL_MODEL: str = Field(
            default="gemini-2.0-flash", description="Gemini model for small tasks"
        )
        GEMINI_LARGE_MODEL: str = Field(
            default="gemini-2.5-pro", description="Gemini model for large tasks"
        )
        GEMINI_HUGE_MODEL: str = Field(
            default="gemini-2.5-pro", description="Gemini model for huge tasks"
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        print(f"{self.valves=}")
        pass

    def pipes(self) -> list[dict[str, str]]:
        try:
            self.setup()
        except Exception as e:
            return [{"id": "error", "name": f"Error: {e}"}]

        return [
            {"id": self.valves.AGENT_ID, "name": self.valves.AGENT_NAME},
            {
                "id": self.valves.AGENT_ID + "-mini",
                "name": self.valves.AGENT_NAME + "-mini",
            },
        ]

    def setup(self):
        v = self.valves

        # Set up local models configuration
        if v.USE_LOCAL_MODELS:
            self.local_model_kwargs = {
                "base_url": v.LOCAL_API_BASE_URL,
                "api_key": v.LOCAL_API_KEY or "sk-no-key-required",
            }

        # Set up Gemini configuration
        if v.USE_GEMINI and not v.GEMINI_API_KEY:
            raise Exception(
                "Error: GEMINI_API_KEY is required when USE_GEMINI is enabled"
            )

        # Ensure at least one model type is enabled
        if not (v.USE_LOCAL_MODELS or v.USE_GEMINI):
            raise Exception(
                "Error: Either USE_LOCAL_MODELS or USE_GEMINI must be enabled"
            )

        self.SYSTEM_PROMPT_INJECTION = ""
        pass

    async def pipe(
        self,
        body: dict,
        __request__: Request,
        __user__: dict | None,
        __task__: str | None,
        __tools__: dict[str, dict] | None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None,
    ) -> AsyncGenerator:
        try:
            print("Task: " + str(__task__))
            print(f"{__tools__=}")
            if __task__ == "function_calling":
                return

            self.setup()

            start_time = time.time()

            called_model_id = body["model"]
            mini_mode = False
            if called_model_id.endswith("-mini"):
                mini_mode = True

            # print(f"{body=}")

            v = self.valves

            # Determine which model provider to use and set appropriate models
            if v.USE_GEMINI:
                small_model_id = v.GEMINI_SMALL_MODEL
                large_model_id = v.GEMINI_LARGE_MODEL
                huge_model_id = v.GEMINI_HUGE_MODEL
                online_model_id = v.GEMINI_LARGE_MODEL
                planning_model_id = small_model_id
                model_provider = "gemini"
            else:  # Default to local models
                small_model_id = v.LOCAL_SMALL_MODEL
                large_model_id = v.LOCAL_LARGE_MODEL
                huge_model_id = v.LOCAL_HUGE_MODEL
                online_model_id = v.LOCAL_LARGE_MODEL
                planning_model_id = small_model_id
                model_provider = "local"

            print(f"Model provider: {model_provider}")
            print(f"Small model: {small_model_id}")
            print(f"Large model: {large_model_id}")

            # Initialize planning model based on provider and configuration
            if model_provider == "local":
                planning_model = ChatOpenAI(
                    model=planning_model_id, **self.local_model_kwargs
                )
            elif model_provider == "gemini":
                planning_model = ChatGoogleGenerativeAI(
                    model=planning_model_id,
                    google_api_key=v.GEMINI_API_KEY,
                    temperature=0.7,
                )

            # Initialize small and large models based on provider
            if model_provider == "local":
                small_model = ChatOpenAI(
                    model=small_model_id, **self.local_model_kwargs
                )
                large_model = ChatOpenAI(
                    model=large_model_id, **self.local_model_kwargs
                )
            elif model_provider == "gemini":
                small_model = ChatGoogleGenerativeAI(
                    model=small_model_id,
                    google_api_key=v.GEMINI_API_KEY,
                )
                large_model = ChatGoogleGenerativeAI(
                    model=large_model_id,
                    google_api_key=v.GEMINI_API_KEY,
                )

            config = {}

            if __task__ == "title_generation":
                content = small_model.invoke(body["messages"], config=config).content
                assert isinstance(content, str)
                yield content
                return

            send_citation = get_send_citation(__event_emitter__)
            send_status = get_send_status(__event_emitter__)

            #
            # STEP 1: Planning
            #

            planning_messages = [{"role": "system", "content": PLANNING_PROMPT}]

            combined_message = ""
            for message in body["messages"]:
                role = message["role"]
                message_content = ""
                content_to_use = ""
                try:
                    message_content = json.loads(message_content)
                    message_content = message_content["content"]
                except:
                    message_content = message["content"]
                print(
                    f"Type of Message: {type(message_content)}. Length is {len(message_content)}"
                )
                if len(message_content) > 1000 and isinstance(message_content, str):
                    mssg_length = len(message_content)
                    content_to_use = (
                        message_content[:500]
                        + "\n...(Middle of message cut by $NUMBER$)...\n"
                        + message_content[-500:]
                    )
                    new_mssg_length = len(content_to_use)
                    content_to_use = content_to_use.replace(
                        "$NUMBER$", str(mssg_length - new_mssg_length)
                    )
                elif isinstance(message_content, str):
                    content_to_use = message_content
                elif isinstance(message_content, list):
                    for part in message_content:
                        # print(f"{part=}")
                        if part["type"] == "text":
                            text = part["text"]
                            if len(text) > 1000 and isinstance(text, str):
                                mssg_length = len(text)
                                content_to_use = (
                                    text[:500]
                                    + "\n...(Middle of message cut by $NUMBER$)...\n"
                                    + text[-500:]
                                )
                                new_mssg_length = len(content_to_use)
                                content_to_use = content_to_use.replace(
                                    "$NUMBER$", str(mssg_length - new_mssg_length)
                                )
                            else:
                                content_to_use += text
                        if part["type"] == "image_url":
                            content_to_use += "\nIMAGE FROM USER CUT HERE\n"
                combined_message += f'--- NEXT MESSAGE FROM "{str(role).upper()}" ---\n{content_to_use}\n--- DONE ---\n'

            planning_messages.append({"role": "user", "content": combined_message})

            print(f"{planning_messages=}")

            await send_status(
                status_message="Planning...",
                done=False,
            )

            planning_buffer = ""
            async for chunk in planning_model.astream(planning_messages, config=config):
                content = chunk.content
                assert isinstance(content, str)
                planning_buffer += content
            content = planning_buffer

            # Get the planning result from the xml tags
            csv_hastag_list = re.findall(r"<answer>(.*?)</answer>", content)
            csv_hastag_list = csv_hastag_list[0] if csv_hastag_list else "unknown"

            if "#small" in csv_hastag_list:
                model_to_use_id = small_model_id
            elif "#medium" in csv_hastag_list:
                model_to_use_id = large_model_id
            elif "#large" in csv_hastag_list:
                model_to_use_id = huge_model_id
            elif "#online" in csv_hastag_list:
                model_to_use_id = online_model_id
            else:
                model_to_use_id = small_model_id

            is_reasoning_needed = "YES" if "#reasoning" in csv_hastag_list else "NO"

            await send_citation(
                url=f"SMART Planning",
                title="SMART Planning",
                content=f"{content=}",
            )

            last_message_content = body["messages"][-1]["content"]

            if isinstance(last_message_content, list):
                last_message_content = last_message_content[0]["text"]

            # Try to find #!, #!!, #*yes, #*no, in the user message, let them overwrite the model choice
            if "#!!!" in last_message_content or "#large" in last_message_content:
                model_to_use_id = huge_model_id
            elif "#!!" in last_message_content or "#medium" in last_message_content:
                model_to_use_id = large_model_id
            elif "#!" in last_message_content or "#small" in last_message_content:
                model_to_use_id = small_model_id

            if "#*yes" in last_message_content or "#yes" in last_message_content:
                is_reasoning_needed = "YES"
            elif "#*no" in last_message_content or "#no" in last_message_content:
                is_reasoning_needed = "NO"

            await send_status(
                status_message=f"Planning complete. Using Model: {model_to_use_id}. Reasoning needed: {is_reasoning_needed}.",
                done=True,
            )

            tools = []
            for key, value in __tools__.items():
                tools.append(
                    StructuredTool(
                        func=None,
                        name=key,
                        coroutine=value["callable"],
                        args_schema=value["pydantic_model"],
                        description=value["spec"]["description"],
                    )
                )

            # Use the model based on provider
            if model_provider == "local":
                model_to_use = ChatOpenAI(
                    model=model_to_use_id, **self.local_model_kwargs
                )
            elif model_provider == "gemini":
                model_to_use = ChatGoogleGenerativeAI(
                    model=model_to_use_id,
                    google_api_key=v.GEMINI_API_KEY,
                )

            messages_to_use = body["messages"]

            last_message_json = False
            try:
                if isinstance(messages_to_use[-1]["content"], list):
                    last_message_json = True
            except:
                pass

            # print(f"{messages_to_use=}")
            # print(f"{last_message_json=}")

            if is_reasoning_needed == "NO":
                messages_to_use[0]["content"] = (
                    messages_to_use[0]["content"]
                    + USER_INTERACTION_PROMPT
                    + self.SYSTEM_PROMPT_INJECTION
                )

                if last_message_json == False:
                    messages_to_use[-1]["content"] = (
                        str(messages_to_use[-1]["content"])
                        .replace("#*yes", "")
                        .replace("#*no", "")
                        .replace("#!!", "")
                        .replace("#!", "")
                        .replace("#!!!", "")
                        .replace("#no", "")
                        .replace("#yes", "")
                        .replace("#large", "")
                        .replace("#medium", "")
                        .replace("#small", "")
                        .replace("#online", "")
                    )
                else:
                    messages_to_use[-1]["content"][0]["text"] = (
                        str(messages_to_use[-1]["content"][0]["text"])
                        .replace("#*yes", "")
                        .replace("#*no", "")
                        .replace("#!!", "")
                        .replace("#!", "")
                        .replace("#!!!", "")
                        .replace("#no", "")
                        .replace("#yes", "")
                        .replace("#large", "")
                        .replace("#medium", "")
                        .replace("#small", "")
                        .replace("#online", "")
                    )

                graph = create_react_agent(model_to_use, tools=tools)
                inputs = {"messages": body["messages"]}

                num_tool_calls = 0
                async for event in graph.astream_events(
                    inputs, version="v2", config=config
                ):
                    if num_tool_calls >= 6:
                        yield "[TOO MANY TOOL CALLS - AGENT TERMINATED]"
                        break
                    kind = event["event"]
                    data = event["data"]
                    if kind == "on_chat_model_stream":
                        if "chunk" in data and (content := data["chunk"].content):
                            yield content
                    elif kind == "on_tool_start":
                        yield "\n"
                        await send_status(f"Running tool {event['name']}", False)
                    elif kind == "on_tool_end":
                        num_tool_calls += 1
                        await send_status(
                            f"Tool '{event['name']}' returned {data.get('output')}",
                            True,
                        )
                        await send_citation(
                            url=f"Tool call {num_tool_calls}",
                            title=event["name"],
                            content=f"Tool '{event['name']}' with inputs {data.get('input')} returned {data.get('output')}",
                        )

                await send_status(
                    status_message=f"Done! Took: {round(time.time() - start_time, 1)}s. Used {model_to_use_id}. Reasoning was {'used' if is_reasoning_needed == True else 'not used'}.",
                    done=True,
                )
                return
            elif is_reasoning_needed == "YES":
                # Initialize reasoning model based on provider (use large model in all cases)
                if model_provider == "local":
                    reasoning_model = ChatOpenAI(
                        model=large_model_id, **self.local_model_kwargs
                    )
                elif model_provider == "gemini":
                    reasoning_model = ChatGoogleGenerativeAI(
                        model=large_model_id,
                        google_api_key=v.GEMINI_API_KEY,
                    )

                full_content = ""
                reasoning_context = ""

                for msg in body["messages"][
                    :-1
                ]:  # Process all messages except the last one
                    if msg["role"] == "user":
                        if len(msg["content"]) > 400:
                            text_msg = (
                                msg["content"][:250]
                                + "\n...(Middle cut)...\n"
                                + msg["content"][-100:]
                            )
                        else:
                            text_msg = msg["content"]
                        reasoning_context += f"--- NEXT MESSAGE FROM \"{msg['role'].upper()}\" ---\n{text_msg}"
                    if msg["role"] == "assistant":
                        if len(msg["content"]) > 250:
                            text_msg = (
                                msg["content"][:150]
                                + "\n...(Middle cut)...\n"
                                + msg["content"][-50:]
                            )
                        else:
                            text_msg = msg["content"]
                        reasoning_context += f"--- NEXT MESSAGE FROM \"{msg['role'].upper()}\" ---\n{text_msg}"

                # Add the last message without cutting it
                last_msg = body["messages"][-1]
                if last_msg["role"] == "user" and last_message_json == False:
                    reasoning_context = (
                        reasoning_context
                        + f"--- LAST USER MESSAGE/PROMPT ---\n{last_msg['content']}"
                    )
                elif last_msg["role"] == "user":
                    reasoning_context = (
                        reasoning_context
                        + f"--- LAST USER MESSAGE/PROMPT ---\n{last_msg['content'][0]['text']}"
                    )

                reasoning_context = (
                    reasoning_context.replace("#*yes", "")
                    .replace("#*no", "")
                    .replace("#!!", "")
                    .replace("#!", "")
                    .replace("#!!!", "")
                    .replace("#no", "")
                    .replace("#yes", "")
                    .replace("#large", "")
                    .replace("#medium", "")
                    .replace("#small", "")
                    .replace("#online", "")
                )

                reasoning_messages = [
                    {"role": "system", "content": REASONING_PROMPT},
                    {"role": "user", "content": reasoning_context},
                ]

                await send_status(
                    status_message="Reasoning...",
                    done=False,
                )

                reasoning_bufffer = ""
                update_status = 0
                async for chunk in reasoning_model.astream(
                    reasoning_messages, config=config
                ):
                    content = chunk.content
                    assert isinstance(content, str)
                    reasoning_bufffer += content
                    update_status += 1

                    if update_status >= 5:
                        update_status = 0
                        await send_status(
                            status_message=f"Reasoning ({len(reasoning_bufffer)})... {reasoning_bufffer[-100:]}",
                            done=False,
                        )

                await send_status(
                    status_message=f"Reasoning ({len(reasoning_bufffer)})... done",
                    done=True,
                )

                reasoning_content = reasoning_bufffer

                full_content += (
                    "<reasoning_agent_output>\n"
                    + reasoning_content
                    + "\n<reasoning_agent_output>"
                )

                await send_citation(
                    url=f"SMART Reasoning",
                    title="SMART Reasoning",
                    content=f"{reasoning_content=}",
                )

                # Try to find <ask_tool_agent> ... </ask_tool_agent> using re
                # If found, then ask the tool agent
                tool_agent_content = re.findall(
                    r"<ask_tool_agent>(.*?)</ask_tool_agent>",
                    reasoning_content,
                    re.DOTALL,
                )
                print(f"{tool_agent_content=}")

                if len(tool_agent_content) > 0:
                    await send_status(f"Running tool-agent...", False)
                    tool_message = [
                        {"role": "system", "content": TOOL_PROMPT},
                        {
                            "role": "user",
                            "content": "<reasoning_agent_requests>\n"
                            + str(tool_agent_content)
                            + "\n</reasoning_agent_requests>",
                        },
                    ]

                    if not __tools__:
                        tool_agent_response = "Tool agent could not use any tools because the user did not enable any."
                    else:
                        # Initialize tool agent model based on the provider
                        if model_provider == "local":
                            tool_agent_model = ChatOpenAI(
                                model=large_model_id, **self.local_model_kwargs
                            )
                        elif model_provider == "gemini":
                            tool_agent_model = ChatGoogleGenerativeAI(
                                model=large_model_id,
                                google_api_key=v.GEMINI_API_KEY,
                            )

                        graph = create_react_agent(tool_agent_model, tools=tools)
                        inputs = {"messages": tool_message}
                        message_buffer = ""
                        num_tool_calls = 0
                        async for event in graph.astream_events(inputs, version="v2", config=config):  # type: ignore
                            if num_tool_calls > 3:
                                yield "[TOO MANY TOOL CALLS - AGENT TERMINATED]"
                                break
                            kind = event["event"]
                            data = event["data"]
                            if kind == "on_chat_model_stream":
                                if "chunk" in data and (
                                    content := data["chunk"].content
                                ):
                                    message_buffer = message_buffer + content
                            elif kind == "on_tool_start":
                                message_buffer = message_buffer + "\n"
                                await send_status(
                                    f"Running tool {event['name']}", False
                                )
                            elif kind == "on_tool_end":
                                num_tool_calls += 1
                                await send_status(
                                    f"Tool '{event['name']}' returned {data.get('output')}",
                                    True,
                                )
                                await send_citation(
                                    url=f"Tool call {num_tool_calls}",
                                    title=event["name"],
                                    content=f"Tool '{event['name']}' with inputs {data.get('input')} returned {data.get('output')}",
                                )

                        tool_agent_response = message_buffer

                    print("TOOL AGENT RESPONSE:\n\n" + str(tool_agent_response))
                    await send_citation(
                        url=f"SMART Tool-use",
                        title="SMART Tool-use",
                        content=f"{tool_agent_response=}",
                    )

                    full_content += (
                        "\n\n\n<tool_agent_output>\n"
                        + tool_agent_response
                        + "\n<tool_agent_output>"
                    )

                await send_status(
                    status_message="Reasoning complete.",
                    done=True,
                )

                if last_message_json == False:
                    messages_to_use[-1]["content"] = (
                        "<user_input>\n"
                        + messages_to_use[-1]["content"]
                        + "\n</user_input>\n\n"
                        + full_content
                    )
                else:
                    messages_to_use[-1]["content"][0]["text"] = (
                        "<user_input>\n"
                        + messages_to_use[-1]["content"][0]["text"]
                        + "\n</user_input>\n\n"
                        + full_content
                    )
                messages_to_use[0]["content"] = (
                    messages_to_use[0]["content"]
                    + USER_INTERACTION_PROMPT
                    + self.SYSTEM_PROMPT_INJECTION
                )

                await send_status(
                    status_message=f"Starting answer with {model_to_use_id}...",
                    done=False,
                )

                # Use the model based on provider
                if model_provider == "local":
                    model_to_use = ChatOpenAI(
                        model=model_to_use_id, **self.local_model_kwargs
                    )
                elif model_provider == "gemini":
                    model_to_use = ChatGoogleGenerativeAI(
                        model=model_to_use_id,
                        google_api_key=v.GEMINI_API_KEY,
                    )

                graph = create_react_agent(model_to_use, tools=tools)
                inputs = {"messages": messages_to_use}

                num_tool_calls = 0
                async for event in graph.astream_events(inputs, version="v2", config=config):  # type: ignore
                    if num_tool_calls >= 6:
                        await send_status(
                            status_message="Interupting due to max tool calls reached!",
                            done=True,
                        )
                        yield "[TOO MANY TOOL CALLS - AGENT TERMINATED]"
                        break
                    kind = event["event"]
                    data = event["data"]
                    if kind == "on_chat_model_stream":
                        if "chunk" in data and (content := data["chunk"].content):
                            yield content
                    elif kind == "on_tool_start":
                        yield "\n"
                        await send_status(f"Running tool {event['name']}", False)
                    elif kind == "on_tool_end":
                        num_tool_calls += 1
                        await send_status(
                            f"Tool '{event['name']}' returned {data.get('output')}",
                            True,
                        )
                        await send_citation(
                            url=f"Tool call {num_tool_calls}",
                            title=event["name"],
                            content=f"Tool '{event['name']}' with inputs {data.get('input')} returned {data.get('output')}",
                        )

                if not num_tool_calls >= 4:
                    await send_status(
                        status_message=f"Done! Took: {round(time.time() - start_time, 1)}s. Used {model_to_use_id}. Reasoning was used",
                        done=True,
                    )
                return

            else:
                yield "Error: is_reasoning_needed is not YES or NO"
                return
        except Exception as e:
            yield "Error: " + str(e)
            return
