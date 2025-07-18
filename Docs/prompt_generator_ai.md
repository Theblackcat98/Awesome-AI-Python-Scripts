# Prompt Generator AI

This Python script (`prompt_generator_ai.py`) is a utility designed to generate prompt templates using the Google Gemini AI model. It takes a task description as a command-line argument, constructs a metaprompt, sends it to the Gemini API, and then extracts and saves the generated prompt to a Markdown file with a dated filename (e.g., `prompt_YYYY-MM-DD.md`).

## Usage

To use this script, run it from your terminal and provide the task description as a command-line argument. Ensure you have your `GEMINI_API_KEY` configured as an environment variable.

```bash
python Utility_Python_Scripts/prompt_generator_ai.py "Your task description here"
```

Replace `"Your task description here"` with the actual task you want the AI to generate a prompt for.

## Configuration

The script requires access to the Google Gemini API. Your API key must be set as an environment variable named `GEMINI_API_KEY`. It is recommended to store this key in a `.env` file in the root directory of your project.

Example `.env` file content:

```
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

The script uses `dotenv` to load environment variables, so ensure the `.env` file is correctly set up.

## Core Components

This section details the main variables and functions within the `prompt_generator_ai.py` script.

### `metaprompt`

A multi-line string variable that contains the foundational instruction set for the Google Gemini AI model. This metaprompt defines how the AI should interpret tasks and generate new prompt templates, including examples of task instructions and their corresponding prompt structures. It acts as a guide for the AI to understand the desired behavior for generating effective prompts.

### `extract_between_tags(tag, string, strip)`

This helper function [`extract_between_tags(tag, string, strip)`](Utility_Python_Scripts/prompt_generator_ai.py:216) extracts content from within specified XML-like tags within a given string.
- `tag`: The name of the XML tag (e.g., "Instructions").
- `string`: The input string to search within.
- `strip`: A boolean indicating whether to strip whitespace from the extracted content.

### `remove_empty_tags(text)`

This helper function [`remove_empty_tags(text)`](Utility_Python_Scripts/prompt_generator_ai.py:224) removes instances of empty XML-like tags (e.g., `<tag></tag>`) from a string. It helps clean up the AI's response by removing superfluous empty tag structures.

### `strip_last_sentence(text)`

This helper function [`strip_last_sentence(text)`](Utility_Python_Scripts/prompt_generator_ai.py:229) removes the last sentence from a block of text if it specifically starts with "Let me know". This is used for a specific cleaning logic related to the AI's output.

### `extract_prompt(metaprompt_response)`

This function [`extract_prompt(metaprompt_response)`](Utility_Python_Scripts/prompt_generator_ai.py:241) is responsible for parsing the raw response from the Google Gemini AI model and extracting the clean, final prompt template. It utilizes `extract_between_tags` and `remove_empty_tags` for this purpose.

### `pretty_print(message)`

This helper function [`pretty_print(message)`](Utility_Python_Scripts/prompt_generator_ai.py:255) takes a long string message and formats it for improved readability in the console output. It breaks down paragraphs and wraps lines to a specified width.

### `main()`

The `main()` function [`main()`](Utility_Python_Scripts/prompt_generator_ai.py:268) is the entry point of the script and orchestrates its primary functionality. Its execution flow includes:
1.  **API Key Check:** Verifies that the `GEMINI_API_KEY` environment variable is set.
2.  **Command-line Argument Parsing:** Retrieves the task description provided by the user.
3.  **Model Configuration:** Initializes the Google Gemini AI model (`gemini-2.5-flash`).
4.  **Prompt Preparation and Request:** Replaces the `{{TASK}}` placeholder in the `metaprompt` with the user's task and sends the request to the AI model.
5.  **Prompt Extraction:** Calls `extract_prompt` to get the cleaned prompt template from the AI's response.
6.  **File Output:** If a valid prompt is extracted, it saves the generated prompt to a new Markdown file named `prompt_YYYY-MM-DD.md` in the current directory.

## Error Handling

The script incorporates several error handling mechanisms to provide informative feedback to the user:
-   **Missing API Key:** Exits with an error if `GEMINI_API_KEY` is not found in the environment variables.
-   **Missing Command-line Argument:** Provides usage instructions and exits if no task description is provided.
-   **AI Model Errors:** Catches and reports exceptions that occur during the call to the generative AI model.
-   **File Writing Errors:** Handles `IOError` exceptions that might occur when attempting to write the generated prompt to a file.
-   **Invalid AI Response:** If the script fails to extract a valid prompt from the AI's response, it prints an error message and the full, unparsed response for debugging.