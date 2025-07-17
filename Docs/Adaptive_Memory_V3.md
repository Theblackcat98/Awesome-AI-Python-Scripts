# Adaptive Memory v3.0 - Advanced Memory System for OpenWebUI

Adaptive Memory is a sophisticated OpenWebUI pipe designed to provide **persistent, personalized memory capabilities** for Large Language Models (LLMs). This system allows LLMs to "remember" key information about users across various conversations, fostering a more natural and personalized interaction experience. It intelligently extracts, filters, stores, and retrieves user-specific details, dynamically injecting relevant memories into future LLM prompts.

## Key Features

1.  **Intelligent Memory Extraction**:
    *   Automatically identifies facts, preferences, relationships, and goals from user messages.
    *   Categorizes memories with appropriate tags (e.g., `identity`, `preference`, `behavior`, `relationship`, `goal`, `possession`).
    *   Filters out general knowledge or trivia, focusing on user-specific information.
2.  **Multi-layered Filtering Pipeline**:
    *   Robust JSON parsing with fallback mechanisms ensures reliable memory extraction.
    *   Includes preference statement shortcuts for common user likes/dislikes.
    *   A blacklist/whitelist system provides control over topic filtering.
    *   Smart deduplication uses both semantic (embedding-based) and text-based similarity to prevent redundant storage.
3.  **Optimized Memory Retrieval**:
    *   Leverages vector-based similarity for efficient retrieval of relevant memories.
    *   Offers an optional LLM-based relevance scoring for enhanced accuracy when needed.
    *   Performance optimizations reduce unnecessary LLM calls.
4.  **Adaptive Memory Management**:
    *   Intelligently clusters and summarizes related older memories to prevent memory clutter.
    *   Employs intelligent pruning strategies (e.g., FIFO, least relevant) when memory limits are reached.
    *   Supports configurable background tasks for continuous maintenance operations.
5.  **Memory Injection & Output Filtering**:
    *   Contextually injects relevant memories into LLM prompts.
    *   Offers customizable memory display formats (`bullet`, `numbered`, `paragraph`).
    *   Filters meta-explanations from LLM responses for cleaner output.
6.  **Broad LLM Support**:
    *   Features generalized LLM provider configuration, supporting both Ollama and OpenAI-compatible APIs.
    *   Allows configurable model selection and API endpoint URLs.
    *   Utilizes optimized prompts for reliable JSON response parsing.
7.  **Comprehensive Configuration System**:
    *   Provides fine-grained control through extensive "valve" settings.
    *   Includes input validation to prevent misconfiguration.
    *   Supports per-user configuration options.
8.  **Memory Banks**:
    *   Categorizes memories into distinct banks (e.g., `Personal`, `Work`, `General`) to enable focused retrieval and injection based on context.

## Recent Improvements (v3.0)

*   **Optimized Relevance Calculation**: Reduced latency and cost by adding a vector-only option and smart LLM call skipping for high-confidence scenarios.
*   **Enhanced Memory Deduplication**: Introduced embedding-based similarity for more accurate semantic duplicate detection.
*   **Intelligent Memory Pruning**: Implemented support for both FIFO (First-In, First-Out) and relevance-based pruning strategies when memory limits are reached.
*   **Cluster-Based Summarization**: New system to group and summarize related memories by semantic similarity or shared tags.
*   **LLM Call Optimization**: Minimized LLM usage through high-confidence vector similarity thresholds.
*   **Resilient JSON Parsing**: Strengthened JSON extraction with robust fallbacks and smart parsing.
*   **Background Task Management**: Provided configurable control over summarization, logging, and date update tasks.
*   **Enhanced Input Validation**: Added comprehensive validation to prevent valve misconfiguration.
*   **Refined Filtering Logic**: Fine-tuned filters and thresholds for better accuracy.
*   **Generalized LLM Provider Support**: Unified configuration for Ollama and OpenAI-compatible APIs.
*   **Memory Banks**: Introduced "Personal," "Work," and "General" memory banks for better organization.
*   **Fixed Configuration Persistence**: Resolved issues where user-configured LLM provider settings were not applied correctly.

## Key Architectural Components

*   [`Filter`](OpenWebUI/Adaptive_Memory_V3.py:209) Class: The main class encapsulating all the logic for memory operations.
*   [`Filter.Valves`](OpenWebUI/Adaptive_Memory_V3.py:238) Class: A `Pydantic` model defining all global configuration options for the memory system.
*   [`Filter.UserValves`](OpenWebUI/Adaptive_Memory_V3.py:780) Class: A `Pydantic` model for user-specific memory settings, allowing individual users to enable/disable the pipe or set their timezone.
*   [`MemoryOperation`](OpenWebUI/Adaptive_Memory_V3.py:199) Class: A `Pydantic` model representing an operation to be performed on a memory (e.g., `NEW`, `UPDATE`, `DELETE`).
*   [`_get_aiohttp_session()`](OpenWebUI/Adaptive_Memory_V3.py:1516) Method: Manages the asynchronous HTTP client session for making API calls.
*   [`inlet()`](OpenWebUI/Adaptive_Memory_V3.py:1524) Method: The entry point for incoming messages. It intercepts messages, extracts memories, and injects relevant ones into the conversation context. It also handles chat commands like `/memory list_banks` and `/memory assign_bank`.
*   [`outlet()`](OpenWebUI/Adaptive_Memory_V3.py:1837) Method: Processes the LLM's response, extracts new memories from the user's last message, and updates the response with memory-related information or status messages.
*   [`_process_user_memories()`](OpenWebUI/Adaptive_Memory_V3.py:2136) Method: Orchestrates the entire memory processing pipeline, from identification and filtering to deduplication and storage.
*   [`identify_memories()`](OpenWebUI/Adaptive_Memory_V3.py:2781) Method: Uses an LLM to identify potential memories from the input text, guided by a strict JSON output format.
*   [`_extract_and_parse_json()`](OpenWebUI/Adaptive_Memory_V3.py:3061) Method: A robust utility for extracting and parsing JSON content from LLM responses, handling common formatting issues.
*   [`_calculate_memory_similarity()`](OpenWebUI/Adaptive_Memory_V3.py:3245) & [`_calculate_embedding_similarity()`](OpenWebUI/Adaptive_Memory_V3.py:3281) Methods: Functions for determining the similarity between memories, using either text-based or embedding-based (semantic) comparisons.
*   [`get_relevant_memories()`](OpenWebUI/Adaptive_Memory_V3.py:3330) Method: Retrieves memories relevant to the current conversation context, applying vector similarity filtering and optional LLM-based scoring.
*   [`_inject_memories_into_context()`](OpenWebUI/Adaptive_Memory_V3.py:2038) Method: Modifies the system message in the LLM's prompt to include relevant memories, ensuring the LLM is aware of past interactions without explicitly mentioning memory operations.
*   [`process_memories()`](OpenWebUI/Adaptive_Memory_V3.py:3747) Method: Executes the identified memory operations (NEW, UPDATE, DELETE) and handles deduplication and pruning.
*   Background Tasks (e.g., [`_summarize_old_memories_loop()`](OpenWebUI/Adaptive_Memory_V3.py:1116), [`_log_error_counters_loop()`](OpenWebUI/Adaptive_Memory_V3.py:1308), [`_schedule_date_update()`](OpenWebUI/Adaptive_Memory_V3.py:1390)): Asynchronous functions that run periodically to maintain the memory system, summarize old data, and log errors.
*   `_convert_dict_to_memory_operations()`: Handles cases where the LLM returns JSON in an unexpected dictionary format and converts it into the expected list of operations.