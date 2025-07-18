# Poem to Image Generator (`poem_to_image2.py`)

This documentation provides a comprehensive overview of the `poem_to_image2.py` script, which automates the process of generating images from poems using Google's Gemini and Imagen APIs.

## 1. Purpose

The `poem_to_image2.py` script is designed to transform textual poems into visual images. It leverages large language models to first generate a descriptive image prompt based on a given poem, and then uses a text-to-image model (Imagen) to create a corresponding visual representation. The script processes poems from a structured JSON input file, saves the generated prompts, and stores the resulting images in a designated output directory.

## 2. Configuration

The script uses the following key configuration elements:

*   ### `GEMINI_API_KEY`
    *   **Source:** Loaded from an environment variable named `GOOGLE_API_KEY` using the `python-dotenv` library.
    *   **Purpose:** This API key is crucial for authenticating and authorizing requests to the Google Gemini API (for prompt generation) and the Google Imagen API (for image generation).
    *   **Setup:** Before running the script, ensure you have obtained a `GOOGLE_API_KEY` from Google AI Studio or Google Cloud Console and set it as an environment variable, ideally within a `.env` file in the project root or the script's directory.

*   ### `OUTPUT_DIR`
    *   **Value:** A constant string set to `"poem_images"`.
    *   **Purpose:** This specifies the directory where all generated image files (in PNG format) and their corresponding text prompts (in TXT format) will be saved. The script automatically creates this directory if it does not already exist during execution.

## 3. Functions

The script is structured with several functions, each responsible for a specific part of the poem-to-image generation pipeline:

*   ### `load_poems_from_json(file_path: str) -> list`
    *   **Purpose:** Reads and parses a JSON file expected to contain a list of poem objects. Each poem object should be a dictionary.
    *   **Arguments:**
        *   `file_path` (`str`): The absolute or relative path to the JSON input file (e.g., `allpoems.json`).
    *   **Returns:**
        *   `list`: A list of dictionaries, where each dictionary represents a poem. Returns an empty list if the specified file is not found or if the file content is not valid JSON.

*   ### `generate_prompt_from_poem(title: str, poem: str) -> str | None`
    *   **Purpose:** Generates a detailed and descriptive image prompt from a given poem's title and content. It uses the Google Gemini API (`gemini-2.5-flash` model) to achieve this. The generation process is guided by a system instruction (meta-prompt) loaded from the `image_gen_prompt.md` file and a templated user prompt.
    *   **Arguments:**
        *   `title` (`str`): The title of the poem.
        *   `poem` (`str`): The full text content of the poem.
    *   **Returns:**
        *   `str`: The generated image prompt string.
        *   `None`: If the Gemini API call fails (e.g., network error, invalid API key, or no content returned from the model).

*   ### `generate_image_with_imagen(prompt: str, output_filename: str) -> bool`
    *   **Purpose:** Utilizes the Google Imagen API (`models/imagen-4.0-ultra-generate-preview-06-06` model) to create an image based on the provided descriptive prompt. The generated image is then saved to the specified output file path.
    *   **Arguments:**
        *   `prompt` (`str`): The descriptive prompt string for the image generation.
        *   `output_filename` (`str`): The full path, including the filename and extension (e.g., `.png`), where the generated image will be saved.
    *   **Returns:**
        *   `bool`: `True` if the image was successfully generated and saved; `False` otherwise (e.g., API error, no images generated, or file saving issue).

*   ### `save_prompt_to_file(prompt_content: str, file_path: str)`
    *   **Purpose:** Writes the generated image prompt content to a plain text file. This function is useful for archiving prompts, debugging, or reviewing the prompts independently of the image generation.
    *   **Arguments:**
        *   `prompt_content` (`str`): The string content of the image prompt to be saved.
        *   `file_path` (`str`): The full path, including the filename and extension (e.g., `.txt`), where the prompt will be saved.
    *   **Returns:**
        *   `None`

*   ### `main()`
    *   **Purpose:** The central function that orchestrates the entire poem-to-image generation workflow. It handles directory creation, loading input data, iterating through poems, managing prompt generation/loading, and initiating image generation.
    *   **Arguments:**
        *   None
    *   **Returns:**
        *   `None`

## 4. Workflow

The script's primary workflow, managed by the [`main()`](Utility_Python_Scripts/Poem_to_Image/poem_to_image2.py:136) function, proceeds as follows:

1.  **Output Directory Initialization:** It first checks if the `OUTPUT_DIR` (`poem_images`) exists. If not, it creates the directory to store outputs.
2.  **Poem Data Loading:** It calls [`load_poems_from_json("allpoems.json")`](Utility_Python_Scripts/Poem_to_Image/poem_to_image2.py:145) to load the list of poems from the specified JSON file. If no poems are loaded or an error occurs, the script exits.
3.  **Iterative Poem Processing:** The script then iterates through each poem in the loaded list. For each poem:
    *   **Filename Sanitization:** The poem's title is sanitized to create a clean, file-system-friendly filename for both the prompt and the image.
    *   **Prompt Management:**
        *   It first checks if a prompt file (`[sanitized_title]_prompt.txt`) for the current poem already exists in the `OUTPUT_DIR`.
        *   If the prompt file exists, it reads the prompt content directly from this file, avoiding redundant API calls.
        *   If the prompt file does not exist, it calls [`generate_prompt_from_poem(title, poem)`](Utility_Python_Scripts/Poem_to_Image/poem_to_image2.py:159) to generate a new prompt using the Gemini API.
        *   If a new prompt is successfully generated, it saves this prompt to a new file in the `OUTPUT_DIR` using [`save_prompt_to_file`](Utility_Python_Scripts/Poem_to_Image/poem_to_image2.py:161).
        *   If prompt generation fails, it logs an error and skips to the next poem.
    *   **Image Generation (Currently Commented Out):**
        *   The script then checks if an image file (`[sanitized_title].png`) for the current poem already exists in the `OUTPUT_DIR`.
        *   If the image file exists, it skips image generation to prevent overwriting.
        *   *Important Note:* The line responsible for calling [`generate_image_with_imagen(image_prompt, output_path)`](Utility_Python_Scripts/Poem_to_Image/poem_to_image2.py:171) is currently commented out (`# generate_image_with_imagen(...)`). This means the script will generate and save prompts but will *not* generate actual images unless this line is uncommented in the source code.

## 5. Dependencies

To run this script, you need to install the following Python libraries:

*   [`google-genai`](https://pypi.org/project/google-genai/): The official Google Generative AI Python SDK, which provides access to the Gemini and Imagen APIs.
*   [`Pillow`](https://pypi.org/project/Pillow/): A powerful image processing library, used here to handle image data returned by the Imagen API and save it to files.
*   [`python-dotenv`](https://pypi.org/project/python-dotenv/): A library for loading environment variables from `.env` files, which is used to manage your API key securely.

You can install these dependencies using pip:

```bash
pip install google-genai pillow python-dotenv
```

Additionally, the script relies on the following local files:

*   `allpoems.json`: The input JSON file containing the poems to be processed.
*   [`image_gen_prompt.md`](Utility_Python_Scripts/Poem_to_Image/image_gen_prompt.md): A Markdown file containing the system prompt (or meta-prompt) that guides the Gemini API in generating relevant image prompts from the poem content.

## 6. Usage

Follow these steps to run the `poem_to_image2.py` script:

1.  **Obtain and Set Up API Key:**
    *   Get your `GOOGLE_API_KEY` from the [Google AI Studio](https://aistudio.google.com/) or Google Cloud Console.
    *   Create a file named `.env` in the same directory as `poem_to_image2.py` (or in your project's root directory if you're running it from there).
    *   Add your API key to the `.env` file in the following format:
        ```
        GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
        ```
    *   Ensure the `.env` file is in your `.gitignore` to prevent committing your API key to version control.

2.  **Prepare Input Poems:**
    *   Create a JSON file named `allpoems.json` in the same directory as `poem_to_image2.py`.
    *   This file should be a JSON array of objects, where each object represents a poem and must include `"titlelist"` and `"content"` keys. Example:
        ```json
        [
          {
            "titlelist": "The Silent Forest",
            "content": "Deep in the woods, where shadows creep,\nThe ancient trees their secrets keep.\nA gentle breeze, a whispered sigh,\nAs starlight gleams in nature's eye."
          },
          {
            "titlelist": "Urban Symphony",
            "content": "Concrete canyons, towers tall,\nCity's pulse, a vibrant call.\nHeadlights stream, a hurried pace,\nLife's rhythm in this crowded space."
          }
        ]
        ```

3.  **Run the Script:**
    *   Open your preferred terminal or command prompt.
    *   Navigate to the `Utility_Python_Scripts/Poem_to_Image/` directory:
        ```bash
        cd Utility_Python_Scripts/Poem_to_Image/
        ```
    *   Execute the script using Python:
        ```bash
        python poem_to_image2.py
        ```
    *   The script will begin processing poems. You will see print statements indicating prompt generation status and file saving.
    *   Generated prompt files (`.txt`) will be saved in the `poem_images` directory.
    *   *To enable actual image generation:* You must uncomment the line `generate_image_with_imagen(image_prompt, output_path)` within the `main()` function in `poem_to_image2.py`. After uncommenting, re-run the script. Generated image files (`.png`) will then also be saved in the `poem_images` directory.