# Actor-Critic Loop Pipe

The `Actor-Critic Loop` pipe implements a self-correction mechanism within OpenWebUI, often referred to as an "Actor-Critic" or "Worker-Evaluator" loop. This pipe leverages two distinct Large Language Models (LLMs) to iteratively refine an answer to a user's query, aiming for higher accuracy and quality.

## How it Works

The process involves a continuous feedback loop:

1.  **Worker (Actor) Generation**: An initial LLM (the "Worker" or "Actor") generates an answer to the user's query.
2.  **Evaluator (Critic) Review**: A second LLM (the "Evaluator" or "Critic") reviews the generated answer against the original query.
3.  **Feedback Loop**:
    *   If the "Evaluator" deems the answer "SATISFACTORY," the process concludes, and the refined answer is delivered to the user.
    *   If the "Evaluator" finds the answer "NOT SATISFACTORY," it provides constructive feedback. This feedback is then sent back to the "Worker" LLM, prompting it to revise and regenerate its answer.
4.  **Revision Limit**: This loop continues for a predefined maximum number of revisions (`MAX_REVISIONS`). If the maximum is reached without a "SATISFACTORY" rating, the best-effort answer generated in the final iteration is provided to the user.

## Key Components

*   [`Pipe`](OpenWebUI/Actor_Critic_Loop.py:31) Class: The central orchestrator responsible for managing the flow of the Actor-Critic loop.
*   [`Valves`](OpenWebUI/Actor_Critic_Loop.py:40) Class: Defines all configurable settings for the pipe, allowing users to customize its behavior.
*   [`setup()`](OpenWebUI/Actor_Critic_Loop.py:81) Method: Initializes the `LangChain` clients for both the `Worker` and `Evaluator` LLMs.
*   [`pipe()`](OpenWebUI/Actor_Critic_Loop.py:98) Method: The asynchronous generator that contains the core logic of the iterative refinement process and yields the final response.

## Configuration (`Valves`)

The following settings can be configured to control the behavior of the Actor-Critic Loop pipe:

*   [`AGENT_NAME`](OpenWebUI/Actor_Critic_Loop.py:42):
    *   **Description**: The name of the agent as it appears in the OpenWebUI model selector.
    *   **Default**: "Critique & Revise Agent"
*   [`AGENT_ID`](OpenWebUI/Actor_Critic_Loop.py:47):
    *   **Description**: A unique identifier for the agent pipe.
    *   **Default**: "critique-revise-agent"
*   [`OLLAMA_API_BASE_URL`](OpenWebUI/Actor_Critic_Loop.py:52):
    *   **Description**: The base URL for the local `Ollama` or `OpenAI`-compatible API endpoint used by the LLMs.
    *   **Default**: "http://localhost:11434/v1"
*   [`WORKER_MODEL_ID`](OpenWebUI/Actor_Critic_Loop.py:57):
    *   **Description**: The identifier of the LLM model used for generating answers (the Actor).
    *   **Default**: "llama3:latest"
*   [`EVALUATOR_MODEL_ID`](OpenWebUI/Actor_Critic_Loop.py:61):
    *   **Description**: The identifier of the LLM model used for critiquing and evaluating answers (the Critic).
    *   **Default**: "gemma:latest"
*   [`MAX_REVISIONS`](OpenWebUI/Actor_Critic_Loop.py:65):
    *   **Description**: The maximum number of revision loops the pipe will attempt before providing the current answer.
    *   **Default**: 2