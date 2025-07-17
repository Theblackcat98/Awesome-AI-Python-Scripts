# SMART - Sequential Multi-Agent Reasoning Technique
#### Forked from SMART

**Original Author:**: MartianInGreen
**Author:** TheBlackCat

SMART is a sophisticated pipeline for OpenWebUI that enhances LLM capabilities by employing a multi-agent reasoning process. It dynamically selects models, performs planning, and optionally uses a dedicated reasoning step to provide more accurate and context-aware responses.

## Features

-   **Multi-Agent Architecture**:
    -   **Planning Agent**: Analyzes user input and determines the optimal model and whether reasoning is needed.
    -   **Reasoning Agent (Optional)**: If complex reasoning is required, a dedicated agent using a large model performs in-depth thinking.
    -   **Tool-Use Agent (Optional)**: Can leverage OpenWebUI tools if the reasoning agent requests it.
    -   **User Interaction Agent**: Formulates the final response based on the preceding steps.
-   **Dynamic Model Selection**:
    -   Chooses between small, medium (large), and huge models based on task complexity.
    -   Supports user overrides for model size and reasoning via hashtags (e.g., `#!!` for medium, `#*yes` for reasoning).
-   **Flexible Model Providers**:
    -   **Local Models (Default)**: Integrates with local LLM servers like Ollama or LM Studio (via OpenAI-compatible API).
    -   **Google Gemini**: Supports using Google's Gemini models (Flash, Pro) via API key.
-   **Efficient Processing**:
    -   Input messages are truncated to manage context length for the planning agent.
    -   Asynchronous streaming for responsive output.
-   **Event Emission**: Provides status updates and citations throughout the process for better transparency.

## Requirements

-   OpenWebUI version 0.5.0 or higher.
-   Required Python packages:
    -   `langchain-openai==0.2.14`
    -   `langgraph==0.2.60`
    -   `langchain-google-genai==0.1.4`
    -   `fastapi`

## Configuration

SMART is configured through environment variables, which map to the `Pipe.Valves` class in our `SMART` function.

### Key Configuration Options:

**General:**

-   `MODEL_PREFIX`: Prefix for the model ID (default: `SMART`).
-   `AGENT_NAME`: Display name of the agent (default: `Smart/Core`).
-   `AGENT_ID`: Unique ID for the agent (default: `smart-core`).

**Local Model Configuration:**

-   `USE_LOCAL_MODELS`: Set to `true` (default) or `false`.
-   `LOCAL_API_BASE_URL`: Base URL for your local OpenAI-compatible server (default: `http://localhost:11434/v1`).
-   `LOCAL_API_KEY`: API key for your local server, if required (default: empty, uses `sk-no-key-required`).
-   `LOCAL_SMALL_MODEL`: Model ID for small tasks (default: `llama3.1`).
-   `LOCAL_LARGE_MODEL`: Model ID for large/reasoning tasks (default: `phi4-reasoning:plus`).
-   `LOCAL_HUGE_MODEL`: Model ID for very complex tasks (default: `qwen3`).

**Gemini Configuration:**

-   `USE_GEMINI`: Set to `true` or `false` (default: `false`).
-   `GEMINI_API_KEY`: Your Google Gemini API key (required if `USE_GEMINI` is `true`).
-   `GEMINI_SMALL_MODEL`: Gemini model for small tasks (default: `gemini-2.0-flash`).
-   `GEMINI_LARGE_MODEL`: Gemini model for large/reasoning tasks (default: `gemini-2.5-pro`).
-   `GEMINI_HUGE_MODEL`: Gemini model for very complex tasks (default: `gemini-2.5-pro`).

**Note:** At least one model provider (`USE_LOCAL_MODELS` or `USE_GEMINI`) must be enabled. If both are enabled, Gemini will be preferred.

## How it Works

1.  **Planning**:
    -   The `planning_model` (typically the `SMALL_MODEL`) receives the user's prompt and conversation history.
    -   It outputs a comma-separated list indicating:
        -   The recommended model size for the final answer (`#small`, `#medium`, `#large`, `#online`).
        -   Whether a dedicated reasoning step is needed (`#reasoning` or `#no-reasoning`).
2.  **User Overrides**: The system checks the last user message for hashtags that can override the planning agent's decisions (e.g., `#!` for small, `#!!` for medium, `#!!!` for large, `#*yes` for force reasoning, `#*no` for skip reasoning).
3.  **Reasoning (If Needed)**:
    -   If `#reasoning` is indicated, the `reasoning_model` (always the `LARGE_MODEL` of the selected provider) processes the context.
    -   It generates internal thoughts and can request tool usage via `<ask_tool_agent>` tags.
    -   If tools are requested and available:
        -   The `tool_agent_model` (also the `LARGE_MODEL`) processes the request and interacts with OpenWebUI's tools.
        -   Tool outputs are fed back into the reasoning process.
4.  **Final Response Generation**:
    -   The `model_to_use` (determined by the planning agent or user override) generates the final response.
    -   If reasoning occurred, the reasoning output and any tool agent output are injected into the context for the final model.
    -   The response is streamed back to the user.

## Prompts

The agent uses several internal system prompts:

-   `PLANNING_PROMPT`: Guides the planning agent.
-   `REASONING_PROMPT`: Guides the reasoning agent's internal thought process.
-   `TOOL_PROMPT`: Guides the tool-use agent.
-   `USER_INTERACTION_PROMPT`: Prepended to the main model's system prompt to ensure it follows instructions from the reasoning agent.

This structured approach allows SMART to tackle complex queries more effectively than a single LLM call. 