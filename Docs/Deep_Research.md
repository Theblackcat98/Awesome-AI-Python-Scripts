### High-Level Overview

This Python script, `func.py`, defines a "pipe" for Open WebUI named **"Deep Research at Home"**. Its purpose is to act as a sophisticated, multi-step research agent that takes a user's query and performs the following actions:

1.  **Initial Research:** Conducts preliminary web searches to understand the topic landscape.
2.  **Outline Generation:** Creates a structured research outline based on the initial findings.
3.  **Interactive Feedback (Optional):** Asks the user for feedback on the outline, allowing them to guide the research by keeping or removing topics.
4.  **Cyclical Research:** Enters a loop of generating targeted queries, fetching web content, processing it, and analyzing the results to systematically cover all topics in the outline.
5.  **Semantic Analysis:** Uses embedding models to understand the meaning of text, guide the research direction, compress information, and identify knowledge gaps.
6.  **Content Synthesis:** Once research is complete, it writes a comprehensive, structured report section by section, complete with in-text citations.
7.  **Citation Verification:** Fact-checks its own generated content against the source material, striking through any claims it cannot verify.
8.  **Final Report Generation:** Assembles the sections, adds a title, abstract, introduction, conclusion, and a formatted bibliography.

---

### Core Architectural Components

The code is built around a main `Pipe` class and several helper classes that manage state and perform specific tasks.

*   **`Pipe` Class:** The central orchestrator that contains the main logic for the entire research process.
*   **`Valves` (Inside `Pipe`):** A Pydantic model that defines all user-configurable settings, such as which AI models to use, the number of research cycles, and various thresholds. This makes the tool highly customizable.
*   **`ResearchStateManager`:** A crucial class for a multi-user environment. It ensures that the state of each research session (e.g., completed topics, search history, user preferences) is isolated per conversation, preventing data from one user's research from leaking into another's.
*   **`EmbeddingCache` & `TransformationCache`:** These are simple in-memory caches. Since getting embeddings (numerical representations of text) from an AI model can be slow and costly, these caches store the results. If the same piece of text needs an embedding again, it's retrieved instantly from the cache.
*   **`TrajectoryAccumulator`:** A helper class to calculate the "direction" of the research. It averages the embeddings of queries and successful results over time to understand where the research is heading, helping to maintain momentum.

---

### The Flow of Execution: Step-by-Step

The entire process is kicked off by the `pipe()` method at the end of the file. Here is the logical flow from start to finish.

#### Step 1: Initialization and State Handling

1.  **Entry Point:** The `pipe()` method is called with the user's message.
2.  **Conversation ID:** It creates a unique ID for the current conversation to keep its state separate using `ResearchStateManager`.
3.  **State Check:** It checks the state for this conversation. This is a critical branching point:
    *   **Is it a new conversation?** It calls `reset_state()` to start fresh.
    *   **Is it waiting for outline feedback?** If so, it processes the user's new message as feedback.
    *   **Is it a follow-up to a completed report?** It recognizes this and prepares to build upon the previous research.

#### Step 2: Outline Generation & User Feedback

*(This step occurs for new research queries.)*

1.  **Initial Queries:** The LLM generates a set of broad search queries based on the user's initial prompt to get a lay of the land.
2.  **Initial Search:** It executes these queries using `search_web()` and processes the top results.
3.  **Generate Outline:** The LLM analyzes the content from the initial search results and generates a structured research outline (e.g., "History of Topic X," "Applications of Topic X").
4.  **Interactive Feedback (if enabled):**
    *   The pipe displays the outline to the user.
    *   It asks for feedback using commands like `/keep 1,3` or `/remove 2,4`, or natural language.
    *   It then **pauses execution**. The next time the user sends a message, the pipe will start from the "State Check" (Step 1) and process it as feedback.
    *   When feedback is received, it calculates a **Preference Direction Vector (PDV)**—a mathematical representation of the user's interests. This vector will be used to steer all future research. The outline is then updated.

#### Step 3: The Main Research Cycles

This is the core engine of the research process. It's a `while` loop that continues until a set number of cycles is complete or all topics are covered.

1.  **Prioritize Topics (`rank_topics_by_research_priority`):** In each cycle, it doesn't just pick topics randomly. It ranks the remaining topics based on:
    *   **Research Trajectory:** What direction has been successful so far?
    *   **Knowledge Gaps:** Which semantic dimensions are least covered?
    *   **User Preferences (PDV):** What did the user say they were interested in?
    *   **Topic Dampening:** Topics that have been queried recently are given a lower priority to encourage exploration.
2.  **Generate New Queries (`improved_query_generation`):** Based on the prioritized topics and a rich context (previous queries, results, and cycle summaries), the LLM generates a new, highly specific set of search queries for the current cycle.
3.  **Search and Process (`process_query`):**
    *   It runs each query through the `search_web` function.
    *   It uses `fetch_content` to download the full text from URLs, employing anti-blocking techniques like rotating user agents.
    *   It uses `extract_text_from_html` or `extract_text_from_pdf` to clean the raw content.
    *   It uses `compress_content...` functions to semantically shrink large documents down to their most relevant parts, guided by the query's embedding.
4.  **Analyze and Update (`check_result_relevance` and LLM analysis):**
    *   The results are filtered for relevance. A lightweight "quality filter" model can be used to discard low-quality or irrelevant content.
    *   The LLM analyzes the cycle's findings and updates the status of the research outline, marking topics as "completed," "irrelevant," or discovering "new" topics to add to the list.
    *   This analysis is shown to the user, providing a progress update.

#### Step 4: Synthesis and Report Writing

Once the research cycles are complete, the pipe switches from gathering information to writing the report.

1.  **Final Outline:** A final, refined outline for the report is generated by the LLM, organizing all the discovered information logically.
2.  **Section-by-Section Writing (`generate_section_content_with_citations`):**
    *   The pipe iterates through the final outline, one section at a time.
    *   For each section, it gathers all the relevant research results.
    *   It instructs the LLM to write the content for that section **and to include numerical in-text citations** (e.g., `[1]`, `[2]`) based on the provided sources.
3.  **Smoothing and Review (`smooth_section_transitions`, `review_synthesis`):** The LLM reviews the combined text of each section to improve transitions and ensure a consistent tone, making it read like a single, cohesive document.
4.  **Citation Verification (`verify_citations`):**
    *   This is a critical fact-checking step. For each citation, the pipe fetches the original source content again.
    *   It then asks the LLM: "Does this source document actually support this sentence: '...'?".
    *   If the LLM says no, the sentence in the final report is automatically wrapped in `~~strikethrough~~` tags, indicating it could not be verified.

#### Step 5: Final Assembly and Output

1.  **Generate Front Matter:** The LLM generates a main title, subtitle, and a 150-250 word abstract for the report.
2.  **Generate Bibliography (`generate_bibliography`):** It compiles a list of all unique sources that were actually cited in the text and formats them into a numbered bibliography.
3.  **Assemble Final Document:** It combines all the pieces: Title, Subtitle, Abstract, Introduction, the edited and verified sections, Conclusion, and the Bibliography.
4.  **Export (Optional):** If enabled, it saves all the raw research data (every query, result, and its content) to a text file for the user's records.
5.  **Emit Final Message:** The complete, formatted report is sent to the user in the chat.

---
### Key Sub-Functions Explained

*   **`get_embedding`:** The foundation of all semantic operations. It takes text and returns a vector of numbers representing its meaning.
*   **`compress_content_with_eigendecomposition`:** A sophisticated compression method. It analyzes the "semantic structure" of a document to find its most important themes (eigenvectors) and keeps the text chunks that best represent them, effectively summarizing without losing the core concepts.
*   **`calculate_preference_direction_vector`:** Calculates the user's interest vector by subtracting the average meaning of "removed" topics from the average meaning of "kept" topics. This vector is then used to score all future content and topics.
*   **`fetch_content` & `extract_text_from...`:** These functions make the pipe a robust web scraper, capable of handling HTML, PDFs, and common blocking techniques.
*   **`process_user_outline_feedback`:** Manages the interactive part of the research, parsing user commands and updating the research plan accordingly.
*   **`verify_citation_batch`:** The core of the self-correction mechanism, where the LLM is used to fact-check its own work against primary sources.

In summary, this code defines a powerful and methodical research assistant that automates the entire process from initial brainstorming to a final, verified report, with opportunities for human guidance along the way.
