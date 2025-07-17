# Google Gemini Pipeline

The `Google Gemini Pipeline` is a manifold pipe for OpenWebUI that facilitates interaction with Google's Gemini family of models. It is designed for flexibility and robustness, supporting dynamic model selection, streaming responses, multimodal inputs (text and images), and comprehensive error handling.

## Features

*   **Asynchronous API Calls**: Utilizes asynchronous operations for improved performance and responsiveness.
*   **Model Caching**: Caches the list of available Google models to reduce redundant API calls and speed up model selection.
*   **Dynamic Model Specification**: Automatically strips prefixes from model IDs and handles various naming conventions (e.g., `google_gemini_pipeline.gemini-1.5-pro` maps to `gemini-1.5-pro`).
*   **Streaming Response Handling**: Efficiently processes and streams responses from the Gemini API, providing real-time output.
*   **Multimodal Input Support**: Seamlessly handles conversations that include both text and base64-encoded image data.
*   **Flexible Error Handling**: Implements retry mechanisms with exponential backoff for transient API errors and provides clear error messages for other issues.
*   **Google Generative AI & Vertex AI Integration**: Can be configured to use either the standard Google Generative AI API or Google Cloud's Vertex AI for content generation.
*   **Customizable Generation Parameters**: Supports various parameters like `temperature`, `top_p`, `top_k`, and `max_output_tokens` for fine-tuning model behavior.
*   **Configurable Safety Settings**: Allows users to enable more permissive safety settings via environment variables.
*   **Encrypted API Key Storage**: Uses a custom `EncryptedStr` type to automatically encrypt and decrypt sensitive API keys, enhancing security.
*   **Grounding with Google Search**: Supports integrating with Google Search to "ground" responses, providing relevant web search results and citations.
*   **Native Tool Calling**: Integrates with OpenWebUI's tool system, allowing `Gemini` models to utilize external functions for enhanced capabilities.

## Key Components

*   [`Pipe`](OpenWebUI/Gemini_Pipe.py:126) Class: The main class that orchestrates the entire pipeline, handling API interactions, content preparation, and response processing.
*   [`Valves`](OpenWebUI/Gemini_Pipe.py:131) Class: A `Pydantic` model that defines all user-configurable settings for the pipe, such as API keys, project IDs, and various operational flags.
*   [`EncryptedStr`](OpenWebUI/Gemini_Pipe.py:44) Class: A custom string type that automatically encrypts and decrypts values when a `WEBUI_SECRET_KEY` is set in the environment, ensuring sensitive information like API keys are protected.
*   [`_get_client()`](OpenWebUI/Gemini_Pipe.py:175) Method: Initializes and returns a `genai.Client` instance, configured for either Google Generative AI or Vertex AI based on the `Valves` settings.
*   [`_validate_api_key()`](OpenWebUI/Gemini_Pipe.py:195) Method: Ensures that the necessary API credentials (API key or Vertex AI project ID) are properly configured before making API calls.
*   [`strip_prefix()`](OpenWebUI/Gemini_Pipe.py:220) Method: A helper function that cleans up model IDs, removing unnecessary prefixes to get the pure model name.
*   [`get_google_models()`](OpenWebUI/Gemini_Pipe.py:241) Method: Fetches and caches a list of available `Gemini` models from the Google API, filtering for content generation capabilities.
*   [`_prepare_content()`](OpenWebUI/Gemini_Pipe.py:347) Method: Prepares the incoming messages (including multimodal content like images) into a format suitable for the `Gemini` API. It also extracts system instructions.
*   [`_process_multimodal_content()`](OpenWebUI/Gemini_Pipe.py:388) Method: Specifically handles the conversion of multimodal content (text and base64-encoded images) into `Gemini` API compatible parts.
*   [`_create_tool()`](OpenWebUI/Gemini_Pipe.py:495) Method: A static method that wraps OpenWebUI tools into a callable format compatible with `genai`'s tool-calling mechanism, adjusting signatures as needed.
*   [`_configure_generation()`](OpenWebUI/Gemini_Pipe.py:501) Method: Sets up generation parameters (e.g., `temperature`, `max_output_tokens`) and applies safety settings, including enabling `Google Search` grounding and native tool calling if configured.
*   [`_process_grounding_metadata()`](OpenWebUI/Gemini_Pipe.py:585) Method: Processes `Gemini`'s grounding metadata, extracting information about web search queries and generating citations within the text.
*   [`_handle_streaming_response()`](OpenWebUI/Gemini_Pipe.py:663) Method: Manages the asynchronous streaming of responses from `Gemini`, emitting message deltas and handling grounding metadata.
*   [`_handle_standard_response()`](OpenWebUI/Gemini_Pipe.py:718) Method: Processes non-streaming responses, checking for safety blocks and extracting the generated content.
*   [`_retry_with_backoff()`](OpenWebUI/Gemini_Pipe.py:755) Method: An internal helper for retrying API calls with exponential backoff on temporary server errors.
*   [`pipe()`](OpenWebUI/Gemini_Pipe.py:798) Method: The main execution method, which orchestrates the entire process: validates the model, prepares content, configures generation, makes the API call, and handles the response (streaming or non-streaming).

## Configuration (`Valves`)

The following settings can be configured to control the behavior of the Google Gemini Pipeline:

*   [`GOOGLE_API_KEY`](OpenWebUI/Gemini_Pipe.py:133):
    *   **Description**: Your API key for the Google Generative AI service.
    *   **Default**: Fetched from `os.getenv("GOOGLE_API_KEY")`.
*   [`USE_VERTEX_AI`](OpenWebUI/Gemini_Pipe.py:138):
    *   **Description**: A boolean flag indicating whether to use Google Cloud Vertex AI instead of the standard Google Generative AI API.
    *   **Default**: `false` (determined by `os.getenv("GOOGLE_GENAI_USE_VERTEXAI")`).
*   [`VERTEX_PROJECT`](OpenWebUI/Gemini_Pipe.py:143):
    *   **Description**: The Google Cloud project ID to use with Vertex AI.
    *   **Default**: Fetched from `os.getenv("GOOGLE_CLOUD_PROJECT")`.
*   [`VERTEX_LOCATION`](OpenWebUI/Gemini_Pipe.py:148):
    *   **Description**: The Google Cloud region to use with Vertex AI (e.g., `us-central1`).
    *   **Default**: `global` (fetched from `os.getenv("GOOGLE_CLOUD_LOCATION")`).
*   [`USE_PERMISSIVE_SAFETY`](OpenWebUI/Gemini_Pipe.py:152):
    *   **Description**: A boolean flag to use more permissive safety settings for content generation.
    *   **Default**: `false` (determined by `os.getenv("USE_PERMISSIVE_SAFETY")`).
*   [`MODEL_CACHE_TTL`](OpenWebUI/Gemini_Pipe.py:157):
    *   **Description**: Time in seconds to cache the list of available models before refreshing.
    *   **Default**: `600` seconds (10 minutes).
*   [`RETRY_COUNT`](OpenWebUI/Gemini_Pipe.py:161):
    *   **Description**: The number of times to retry API calls on temporary failures (e.g., server errors).
    *   **Default**: `2`.