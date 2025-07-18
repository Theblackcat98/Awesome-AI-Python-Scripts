# Python Scripts

This repository primarily hosts a collection of OpenWebUI Functions and Plugins, designed to extend the capabilities of Large Language Models (LLMs) and enhance user interaction within the OpenWebUI environment. In the future, this repository will be expanded to include a variety of utility Python scripts that leverage AI and LLMs for various tasks.

---

## OpenWebUI Functions and Plugins

Below is an overview of the OpenWebUI functions and plugins currently available in this repository:

### Actor-Critic Loop

The `Actor-Critic Loop` pipe implements a self-correction mechanism within OpenWebUI, leveraging two distinct Large Language Models (LLMs) to iteratively refine an answer to a user's query, aiming for higher accuracy and quality.

**Purpose**: Implements a self-correction mechanism within OpenWebUI, using two LLMs (Worker/Actor and Evaluator/Critic) to iteratively refine answers.
**How it Works**: The Worker LLM generates an initial answer. The Evaluator LLM reviews it. If the answer is "NOT SATISFACTORY", the Evaluator provides feedback to the Worker for revision. This loop continues until a "SATISFACTORY" rating is achieved or a `MAX_REVISIONS` limit is reached.
**Key Components**: `Pipe` class (central orchestrator), `Valves` class (defines configurable settings), `setup()` method (initializes LLM clients), `pipe()` method (contains the core iterative refinement logic).
**Configuration (`Valves`)**: Configurable settings include `AGENT_NAME`, `AGENT_ID`, `OLLAMA_API_BASE_URL`, `WORKER_MODEL_ID`, `EVALUATOR_MODEL_ID`, and `MAX_REVISIONS`.

### Adaptive Memory v3.0 - Advanced Memory System for OpenWebUI

Adaptive Memory is a sophisticated OpenWebUI pipe designed to provide persistent, personalized memory capabilities for Large Language Models (LLMs). This system allows LLMs to "remember" key information about users across various conversations, fostering a more natural and personalized interaction experience.

**Purpose**: Provides persistent, personalized memory capabilities for LLMs in OpenWebUI, allowing them to "remember" user information across conversations.
**Key Features**: Intelligent Memory Extraction, Multi-layered Filtering Pipeline, Optimized Memory Retrieval, Adaptive Memory Management, Memory Injection & Output Filtering, Broad LLM Support, Comprehensive Configuration System, Memory Banks.
**Recent Improvements (v3.0)**: Includes Optimized Relevance Calculation, Enhanced Memory Deduplication (embedding-based), Intelligent Memory Pruning (FIFO, relevance-based), Cluster-Based Summarization, LLM Call Optimization, Resilient JSON Parsing, Background Task Management, Enhanced Input Validation, Refined Filtering Logic, Generalized LLM Provider Support, and the introduction of Memory Banks. Fixed configuration persistence issues.
**Key Architectural Components**: `Filter` class (main logic), `Filter.Valves` (global configuration), `Filter.UserValves` (user-specific settings), `MemoryOperation` (memory operation representation), `inlet()` (entry point for messages), `outlet()` (processes LLM responses), `_process_user_memories()` (orchestrates memory pipeline), `identify_memories()` (LLM-based memory identification), `get_relevant_memories()` (retrieves relevant memories), `_inject_memories_into_context()` (modifies prompt with memories), `process_memories()` (executes memory operations), and various Background Tasks for maintenance.

### Deep Research at Home

The `Deep Research at Home` pipe defines a sophisticated, multi-step research agent for OpenWebUI, designed to take a user's query and perform comprehensive web research, culminating in a structured, verified report.

**Purpose**: A sophisticated, multi-step research agent that takes a user's query and performs comprehensive web research.
**How it Works**: The process involves Initial Research, Outline Generation, optional Interactive Feedback from the user, Cyclical Research (generating queries, fetching web content, processing, and analyzing results), Semantic Analysis for understanding and guiding research, Content Synthesis (writing sections with in-text citations), Citation Verification (fact-checking generated content), and Final Report Generation (assembling all parts with bibliography).
**Core Architectural Components**: `Pipe` class (central orchestrator), `Valves` (user-configurable settings), `ResearchStateManager` (manages isolated session states), `EmbeddingCache` & `TransformationCache` (in-memory caching for embeddings), and `TrajectoryAccumulator` (calculates research direction).
**Flow of Execution**: Begins with Initialization and State Handling. For new queries, it moves to Outline Generation & User Feedback, where execution can pause for user input. The core is the Main Research Cycles, which prioritize topics, generate new queries, search/process content, and analyze/update research status. Finally, it transitions to Synthesis & Report Writing, followed by Final Assembly & Output.
**Key Sub-Functions**: Important helper functions include `get_embedding` (semantic operations), `compress_content_with_eigendecomposition` (advanced content compression), `calculate_preference_direction_vector` (user interest vector), `fetch_content` & `extract_text_from...` (robust web scraping), `process_user_outline_feedback` (manages interactive feedback), and `verify_citation_batch` (core fact-checking).

### Google Gemini Pipeline

The `Google Gemini Pipeline` is a manifold pipe for OpenWebUI that facilitates robust and flexible interaction with Google's Gemini family of models.

**Purpose**: A manifold pipe for OpenWebUI that facilitates interaction with Google's Gemini family of models, designed for flexibility and robustness.
**Features**: Supports Asynchronous API Calls, Model Caching, Dynamic Model Specification, Streaming Response Handling, Multimodal Input Support (text and images), Flexible Error Handling with retries, Integration with Google Generative AI & Vertex AI, Customizable Generation Parameters (`temperature`, `top_p`, etc.), Configurable Safety Settings, Encrypted API Key Storage using `EncryptedStr`, Grounding with Google Search for citations, and Native Tool Calling.
**Key Components**: `Pipe` class (orchestrates the pipeline), `Valves` (user-configurable settings), `EncryptedStr` (for secure API key storage), `_get_client()` (initializes Google client), `get_google_models()` (fetches and caches available models), `_prepare_content()` (prepares messages for API), `_process_multimodal_content()` (handles images), `_create_tool()` (wraps OpenWebUI tools), `_configure_generation()` (sets generation and safety parameters), `_process_grounding_metadata()` (processes search grounding), `_handle_streaming_response()` (manages streaming output), and `pipe()` (the main execution method).
**Configuration (`Valves`)**: Key settings include `GOOGLE_API_KEY`, `USE_VERTEX_AI`, `VERTEX_PROJECT`, `VERTEX_LOCATION`, `USE_PERMISSIVE_SAFETY`, `MODEL_CACHE_TTL` (model cache time-to-live), and `RETRY_COUNT` for API calls.

### SMART - Sequential Multi-Agent Reasoning Technique

SMART (Sequential Multi-Agent Reasoning Technique) is a sophisticated pipeline for OpenWebUI that enhances LLM capabilities by employing a multi-agent reasoning process, dynamic model selection, and optional dedicated reasoning steps.

**Purpose**: Enhances LLM capabilities by employing a multi-agent reasoning process, dynamically selecting models, performing planning, and optionally using a dedicated reasoning step.
**Features**: Features a Multi-Agent Architecture (Planning Agent, optional Reasoning Agent, optional Tool-Use Agent, and User Interaction Agent), Dynamic Model Selection based on task complexity and user overrides (via hashtags), Flexible Model Providers (Local Models via Ollama/LM Studio or Google Gemini), Efficient Processing with input truncation and asynchronous streaming, and Event Emission for transparency.
**Requirements**: Requires OpenWebUI version 0.5.0 or higher and specific Python packages: `langchain-openai`, `langgraph`, `langchain-google-genai`, `fastapi`.
**Configuration**: Configured via environment variables that map to the `Pipe.Valves` class, including general settings (`MODEL_PREFIX`, `AGENT_NAME`, `AGENT_ID`), Local Model Configuration (`USE_LOCAL_MODELS`, `LOCAL_API_BASE_URL`, `LOCAL_API_KEY`, `LOCAL_SMALL_MODEL`, `LOCAL_LARGE_MODEL`, `LOCAL_HUGE_MODEL`), and Gemini Configuration (`USE_GEMINI`, `GEMINI_API_KEY`, `GEMINI_SMALL_MODEL`, `GEMINI_LARGE_MODEL`, `GEMINI_HUGE_MODEL`).
**How it Works**: The `planning_model` first determines the optimal model and whether reasoning is needed. User Overrides via hashtags can alter these decisions. If `#reasoning` is indicated, the `reasoning_model` processes context and can request tool usage, which is handled by the `tool_agent_model`. Finally, the `model_to_use` generates and streams the final response.
**Prompts**: Utilizes internal system prompts such as `PLANNING_PROMPT`, `REASONING_PROMPT`, `TOOL_PROMPT`, and `USER_INTERACTION_PROMPT` to guide agent behavior.

### Socratic Thinking Pipe

The `Socratic Thinking` pipe for OpenWebUI implements a self-correction and refinement mechanism that mimics the Socratic method of questioning and improving, utilizing two distinct Large Language Models (LLMs) for generation and critical evaluation.

**Purpose**: Implements a self-correction and refinement mechanism mimicking the Socratic method, using two LLMs (Generator and Evaluator) to question and improve answers.
**How it Works**: The `GENERATOR_MODEL` produces an initial answer. The `EVALUATOR_MODEL` critiques it. If `PASS`, the process concludes. If `FAIL`, the Evaluator provides concise feedback to the Generator for revision. This cycle repeats up to `MAX_LOOPS`.
**Key Components**: `Pipe` class (orchestrates the process), `Valves` class (defines configurable settings), `_generate_completion()` (LLM call helper), `_generate_answer()` (Generator model logic), `_evaluate_answer()` (Evaluator model logic), `emit_status()` & `emit_message()` (for real-time feedback), and `pipe()` (the main entry point).
**Configuration (`Valves`)**: Settings include `ENABLED` (to enable/disable the pipe), `GENERATOR_MODEL` (for answer generation), `EVALUATOR_MODEL` (for critique), `MAX_LOOPS` (maximum refinement iterations), and `TEMPERATURE` (for the Generator model's creativity).

---

## Future Enhancements

This section will be updated to include a list of utility Python Scripts that use AI/LLMs.