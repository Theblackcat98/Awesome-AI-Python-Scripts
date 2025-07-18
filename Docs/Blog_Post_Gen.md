# Tech Blog Post Generator

This Python script automates the generation of technical blog posts by leveraging the GitHub API to find repository information and an Ollama-compatible Large Language Model (LLM) to write the content. It can operate in two modes: discovering a random trending repository based on a defined tech niche, or focusing on a specific, pre-defined repository.

## 1. Purpose

The `tech_blog.py` script is designed to streamline the process of creating technical blog posts. It achieves this by:
-   **Fetching Repository Data:** Interacting with the GitHub API to retrieve details, README files, and documentation from open-source repositories.
-   **AI-Powered Content Generation:** Using an LLM (via Ollama) to generate a blog post outline and a full draft based on the fetched repository data.
-   **Grammar Correction:** Utilizing `language_tool_python` for basic proofreading and grammar correction.
-   **Markdown Output:** Saving the final blog post in Markdown format with YAML front matter.

This script is ideal for technical writers, developers, or content creators who want to quickly generate drafts for blog posts about trending or specific open-source projects.

## 2. Configuration

The script's behavior is controlled by several variables at the top of the `tech_blog.py` file.

-   **`TECH_SUB_NICHE`**: A string variable used for **Discovery Mode**.
    -   **Purpose:** When `SPECIFIC_REPO` is left blank, the script will use this variable to select a pre-defined tech sub-niche from the `SUB_NICHES` dictionary. It then searches GitHub for a random trending repository within that sub-niche.
    -   **How to Use (Discovery Mode):** Set this to one of the keys defined in the `SUB_NICHES` dictionary (e.g., `"AI/LLM from Big Tech"`, `"Top Python Projects"`). Ensure `SPECIFIC_REPO` is an empty string (`""`).
    -   **Example:** `TECH_SUB_NICHE = "Top Python Projects"`

-   **`SPECIFIC_REPO`**: A string variable used for **Specific Repo Mode**.
    -   **Purpose:** Allows you to specify a particular GitHub repository (e.g., `"owner/repo_name"`) that the script should write about directly. This mode overrides `TECH_SUB_NICHE`.
    -   **How to Use (Specific Repo Mode):** Fill this with the full name of the repository (e.g., `"facebook/react"`).
    -   **Example:** `SPECIFIC_REPO = "Doriandarko/make-it-heavy"`
    -   **To switch back to Discovery Mode:** Set `SPECIFIC_REPO = ""`

-   **`GITHUB_TOKEN`**: An optional string variable for GitHub API authentication.
    -   **Purpose:** GitHub API has rate limits for unauthenticated requests. Providing a Personal Access Token significantly increases these limits, preventing errors during frequent use.
    -   **How to Use:** Generate a token from [https://github.com/settings/tokens](https://github.com/settings/tokens) (classic tokens are sufficient, with `public_repo` scope if needed, though usually not required for public repo access). Paste the token into this variable.
    -   **Example:** `GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"`

-   **`SUB_NICHES`**: A dictionary containing predefined GitHub search queries for various tech sub-niches.
    -   **Purpose:** This dictionary maps human-readable sub-niche names (keys) to their corresponding GitHub API search queries (values). These queries are used in **Discovery Mode** to find relevant repositories.
    -   **How to Use:** You can add, modify, or remove entries in this dictionary to customize the tech areas the script can discover. The queries are standard GitHub search syntax.
    -   **Example of an entry:** `"AI/LLM from Big Tech": "q=(AI+OR+LLM+OR+transformer)+in:name,description,topics+org:google+org:meta+org:openai+org:microsoft+org:apple+sort:stars-desc+created:>=2023-01-01"`

## 3. Functions

The script is structured with several functions, each responsible for a specific part of the blog post generation process.

### `sanitize_filename(title)`
-   **Purpose:** Cleans a given string to make it suitable for use as a filename by removing invalid characters and formatting it for readability.
-   **Arguments:**
    -   `title` (str): The input string, typically a repository name or blog post title.
-   **Return Value:**
    -   (str): A sanitized version of the input string, suitable for a filename (e.g., `"Doriandarko/make-it-heavy"` becomes `"doriandarko_make-it-heavy"`).

### `get_tech_topic_and_data()`
-   **Purpose:** Fetches relevant repository data from GitHub based on the configured mode (`SPECIFIC_REPO` or `TECH_SUB_NICHE`). It also attempts to fetch the repository's README and content from a `/docs` directory if available.
-   **Arguments:** None. It uses the global configuration variables (`SPECIFIC_REPO`, `TECH_SUB_NICHE`, `SUB_NICHES`, `GITHUB_TOKEN`).
-   **Return Value:**
    -   (dict or None): A dictionary containing comprehensive repository data (e.g., `full_name`, `description`, `language`, `stargazers_count`, `topics`, `html_url`, `readme`, `docs`). Returns `None` if data fetching fails or no repository is found.

### `generate_blog_post()`
-   **Purpose:** Orchestrates the entire blog post generation process, from fetching data to saving the final Markdown file. This is the main function that drives the script.
-   **Arguments:** None.
-   **Return Value:** None. It prints progress to the console and saves the generated blog post to a file.

## 4. Workflow

The `generate_blog_post()` function outlines the high-level steps for creating a blog post:

1.  **Get Repository Data:** Calls [`get_tech_topic_and_data()`](#get_tech_topic_and_data) to retrieve information about a chosen or discovered GitHub repository, including its README and documentation.
2.  **Generate Title and Keywords:** Creates an initial blog post title and a list of keywords based on the repository's details.
3.  **Connect to Ollama:** Initializes a connection to the Ollama server to interact with the specified LLM.
4.  **Generate Outline:** Sends a detailed prompt to the LLM (via Ollama) to generate a structured outline for the blog post, leveraging the fetched repository data for context.
5.  **Generate Full Draft:** Sends another comprehensive prompt to the LLM, instructing it to write the full blog post based on the generated outline and all available repository content.
6.  **Editing and Proofreading:** Uses the `language_tool_python` library to perform grammar and style corrections on the LLM-generated draft.
7.  **Create and Save Markdown File:** Constructs the final Markdown file with YAML front matter (including title, date, description, keywords, and repository URL) and saves it to a `posts` directory within the script's location. The filename is sanitized using [`sanitize_filename()`](#sanitize_filename) and includes the current date.

## 5. Dependencies

This script requires the following external Python libraries:

-   [`requests`](https://pypi.org/project/requests/): Used for making HTTP requests to the GitHub API to fetch repository data.
-   [`language_tool_python`](https://pypi.org/project/language-tool-python/): Used for grammar and style checking of the generated blog post.
-   [`ollama`](https://pypi.org/project/ollama/): The Python client for interacting with the Ollama local LLM server.

You can install these dependencies using pip:

```bash
pip install requests language-tool-python ollama
```

Additionally, you need to have **Ollama** installed and running on your system, with the specified LLM model (`jan-nano:latest` by default) downloaded.

-   **Ollama Installation:** Follow instructions on the [Ollama website](https://ollama.com/download).
-   **Model Download:** Once Ollama is running, download the model used in the script (e.g., `jan-nano:latest`) via your terminal:
    ```bash
    ollama pull jan-nano:latest
    ```
    *(Note: The model name is configurable within the `generate_blog_post` function.)*

## 6. Usage

To run the `tech_blog.py` script:

1.  **Configure:** Open `Utility_Python_Scripts/Blog_Post_Generator/tech_blog.py` and set the `TECH_SUB_NICHE`, `SPECIFIC_REPO`, and `GITHUB_TOKEN` variables according to your desired mode and authentication needs.
2.  **Install Dependencies:** Ensure all required Python libraries are installed (`pip install requests language-tool-python ollama`).
3.  **Run Ollama:** Make sure your Ollama server is running and the necessary LLM model (`jan-nano:latest` or your chosen model) is downloaded and available.
4.  **Execute:** Navigate to the directory containing `tech_blog.py` in your terminal and run the script:

    ```bash
    python tech_blog.py
    ```

The script will print its progress to the console. Once completed, the generated Markdown blog post will be saved in the `Utility_Python_Scripts/Blog_Post_Generator/posts/` directory.