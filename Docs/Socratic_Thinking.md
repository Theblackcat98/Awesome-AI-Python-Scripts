# Socratic Thinking Pipe

The `Socratic Thinking` pipe for OpenWebUI implements a self-correction and refinement mechanism that mimics the Socratic method of questioning and improving. It utilizes two distinct Large Language Models (LLMs): one for generating an initial answer and another for critically evaluating it. This iterative process aims to produce more accurate, comprehensive, and well-reasoned responses.

## How it Works

The pipe operates on a loop of generation and evaluation:

1.  **Answer Generation**: The `GENERATOR_MODEL` (the "Generator") produces an initial answer to the user's query. It also takes into account any previous feedback it has received.
2.  **Answer Evaluation**: The `EVALUATOR_MODEL` (the "Evaluator") then rigorously critiques the generated answer. It assesses its accuracy, completeness, relevance, and clarity against the original user query.
3.  **Feedback and Refinement**:
    *   If the "Evaluator" determines the answer is fully satisfactory, it responds with `PASS`. The process then concludes, and the answer is returned to the user.
    *   If the answer is flawed, the "Evaluator" responds with `FAIL` and provides a concise, constructive critique. This critique is then fed back to the "Generator" model, prompting it to revise its answer in the next iteration.
4.  **Loop Limit**: This generation-evaluation-refinement cycle repeats up to a predefined maximum number of times (`MAX_LOOPS`). If the maximum loops are reached without a satisfactory answer, the best-effort answer from the final attempt is returned, along with a warning.

## Key Components

*   [`Pipe`](OpenWebUI/Socratic_Thinking.py:55) Class: The main class that orchestrates the entire Socratic Thinking process.
*   [`Valves`](OpenWebUI/Socratic_Thinking.py:62) Class: Defines all user-configurable settings for the pipe, such as the models to use and the number of loops.
*   [`_generate_completion()`](OpenWebUI/Socratic_Thinking.py:108) Method: A helper function that encapsulates the logic for calling the underlying LLM via `generate_chat_completions`.
*   [`_generate_answer()`](OpenWebUI/Socratic_Thinking.py:127) Method: Calls the configured `GENERATOR_MODEL` to produce an answer, incorporating any feedback from previous evaluations.
*   [`_evaluate_answer()`](OpenWebUI/Socratic_Thinking.py:148) Method: Calls the configured `EVALUATOR_MODEL` to critique an answer and determine if it passes or fails, providing detailed feedback if it fails.
*   [`emit_status()`](OpenWebUI/Socratic_Thinking.py:160) & [`emit_message()`](OpenWebUI/Socratic_Thinking.py:170) Methods: Helper functions to send status updates and chat messages back to the OpenWebUI frontend, providing real-time feedback to the user on the pipe's progress.
*   [`pipe()`](OpenWebUI/Socratic_Thinking.py:180) Method: The main entry point for the pipe, which receives the user's request and executes the Socratic loop.

## Configuration (`Valves`)

The following settings can be configured to control the behavior of the Socratic Thinking pipe:

*   [`ENABLED`](OpenWebUI/Socratic_Thinking.py:66):
    *   **Description**: A boolean flag to enable or disable the Socratic Thinking pipe.
    *   **Default**: `True`
*   [`GENERATOR_MODEL`](OpenWebUI/Socratic_Thinking.py:70):
    *   **Description**: The identifier of the LLM model that will be used to generate the initial and refined answers.
    *   **Default**: `gemma:7b`
*   [`EVALUATOR_MODEL`](OpenWebUI/Socratic_Thinking.py:75):
    *   **Description**: The identifier of a (typically smaller and faster) LLM model used to critique the generator's answers.
    *   **Default**: `gemma:2b`
*   [`MAX_LOOPS`](OpenWebUI/Socratic_Thinking.py:80):
    *   **Description**: The maximum number of refinement loops the pipe will attempt. A higher number allows for more self-correction but may increase processing time.
    *   **Default**: `3` (Min: 1, Max: 5)
*   [`TEMPERATURE`](OpenWebUI/Socratic_Thinking.py:86):
    *   **Description**: The temperature setting for the `GENERATOR_MODEL`. Higher values lead to more creative responses, lower values to more deterministic ones. The `EVALUATOR_MODEL` uses a fixed low temperature (0.1) for consistent evaluation.
    *   **Default**: `0.7` (Min: 0.0, Max: 2.0)