import requests
import language_tool_python
import os
import random
import re
from datetime import datetime
from ollama import Client
from typing import cast, Mapping, Any

# --- Configuration: Tech Niche Settings ---

# MODE 1: DISCOVERY - Choose a sub-niche to search for a random repo.
# To use this mode, leave SPECIFIC_REPO blank.
TECH_SUB_NICHE = "AI/LLM from Big Tech"  # Options are keys in SUB_NICHES dictionary below

# MODE 2: SPECIFIC REPO - Provide a repo name to write about it directly.
# To use this mode, fill in the repo name (e.g., "facebook/react"). This will override the sub-niche search.
SPECIFIC_REPO = "" # Example: "google/gemma.cpp" or "vercel/next.js"

# Optional: Add your GitHub Personal Access Token to increase API rate limits
# Create one here: https://github.com/settings/tokens
GITHUB_TOKEN = "" # e.g., "ghp_xxxxxxxxxxxxxxxxxxxx"

# --- Sub-Niche Definitions (GitHub Search Queries) ---
# Feel free to add your own!
SUB_NICHES = {
    "AI/LLM from Big Tech": "q=(AI+OR+LLM+OR+transformer)+in:name,description,topics+org:google+org:meta+org:openai+org:microsoft+org:apple+sort:stars-desc+created:>=2023-01-01",
    "Top Python Projects": "q=language:python+sort:stars-desc+created:>=2023-01-01",
    "Trending JavaScript Frameworks": "q=javascript+framework+in:name,description,topics&sort=stars&order=desc",
    "Data Science & Analytics": "q=data+science+OR+pandas+OR+numpy+OR+scikitlearn+in:topics&sort=stars&order=desc",
    "WebAssembly (WASM) Tools": "q=webassembly+OR+wasm+in:name,description,topics&sort=stars&order=desc",
    "Rust Language Projects": "q=language:rust&sort=stars&order=desc",
    "Cloud Native & DevOps Tools": "q=cloud-native+OR+kubernetes+OR+docker+OR+terraform+OR+ansible+in:name,description,topics+sort:stars-desc",
    "Cybersecurity & Hacking Tools": "q=security+OR+hacking+OR+pentesting+OR+vulnerability+in:name,description,topics+sort:stars-desc",
    "Mobile Development (Flutter/React Native)": "q=(flutter+OR+\"react native\")+in:name,description,topics+sort:stars-desc",
    "Blockchain & Web3": "q=blockchain+OR+web3+OR+ethereum+OR+solana+in:name,description,topics+sort:stars-desc",
    "Edge Computing & IoT": "q=(edge+OR+iot+OR+embedded)+in:name,description,topics+sort:stars-desc",
}

def sanitize_filename(title):
    """Removes invalid characters from a string to make it a valid filename."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
    sanitized = sanitized.replace('/', '_') # Replace slash from repo name
    sanitized = sanitized.replace(' ', '-').lower()
    return sanitized[:100]

def get_tech_topic_and_data():
    """Fetches repository data based on the chosen mode (specific or discovery)."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    repo_data = None
    
    # MODE 2: Specific repo is prioritized
    if SPECIFIC_REPO:
        print(f"Fetching data for specific repository: {SPECIFIC_REPO}...")
        try:
            url = f"https://api.github.com/repos/{SPECIFIC_REPO}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            repo_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: Could not fetch data for repository '{SPECIFIC_REPO}'. Please check the name. Details: {e}")
            return None

    # MODE 1: Discover from a sub-niche
    else:
        print(f"Discovering a repository from sub-niche: {TECH_SUB_NICHE}...")
        if TECH_SUB_NICHE not in SUB_NICHES:
            print(f"Error: Sub-niche '{TECH_SUB_NICHE}' not found in SUB_NICHES dictionary.")
            return None
            
        try:
            query = SUB_NICHES[TECH_SUB_NICHE]
            url = f"https://api.github.com/search/repositories?{query}&per_page=20"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            search_results = response.json().get('items', [])
            
            if not search_results:
                print(f"Warning: No repositories found for the sub-niche '{TECH_SUB_NICHE}'.")
                return None
            
            repo_data = random.choice(search_results)
            print(f"Randomly selected repository: {repo_data.get('full_name')}")

        except requests.exceptions.RequestException as e:
            print(f"Error: Could not search GitHub for sub-niche '{TECH_SUB_NICHE}'. Details: {e}")
            return None

    return repo_data

def generate_blog_post():
    # Step 1: Get Repository Data
    repo_data = get_tech_topic_and_data()
    if not repo_data:
        print("Could not retrieve repository data. Exiting.")
        return

    repo_name = repo_data.get('full_name', 'a cool tech project')
    description = repo_data.get('description', 'No description available.')
    language = repo_data.get('language', 'N/A')
    stars = repo_data.get('stargazers_count', 0)
    topics = ", ".join(repo_data.get('topics', []))

    # Step 2: Generate Title and Keywords
    title = f"A Deep Dive into {repo_name}: Features, Use Cases, and Getting Started"
    keywords = [repo_name, repo_name.split('/')[-1], language, "tech tutorial", "open source"] + repo_data.get('topics', [])
    keywords = list(dict.fromkeys(keywords)) # Remove duplicates

    print(f"\n--- Preparing Blog Post ---")
    print(f"Title: {title}")
    print(f"Keywords: {', '.join(keywords)}")
    print("---------------------------\n")

    # Step 3: Connect to Ollama
    try:
        ollama = Client(host='http://localhost:11434')
        MODEL_NAME = 'llama3.1'
        print(f"Successfully connected to Ollama.")
    except Exception as e:
        print(f"Error connecting to Ollama: {e}\nPlease ensure Ollama is running and '{MODEL_NAME}' is installed.")
        return

    # Step 4: Generate Outline
    print("Generating outline...")
    prompt = f"""
    You are a senior software engineer and technical writer tasked with creating a blog post outline.

    **Objective:** Create a detailed, well-structured blog post outline for the title: '{title}'.

    **Repository Details:**
    - **Name:** {repo_name}
    - **Description:** "{description}"
    - **Primary Language:** {language}
    - **Stars:** {stars}
    - **Topics/Keywords:** {topics}

    **Instructions:**
    Generate a comprehensive outline that covers the following sections. Ensure the content is targeted at developers and avoids generic marketing language.

    1.  **Introduction:**
        -   Hook: Start with a compelling question or statement about the problem the repository solves.
        -   Briefly introduce '{repo_name}' and its core purpose based on its description.
        -   Mention its popularity (stars) and the primary language.

    2.  **Why It Matters: Key Features & Uniqueness:**
        -   Identify 2-3 standout features based on the description and topics.
        -   Explain what makes this project unique compared to alternatives (if applicable).

    3.  **Core Use Cases & Target Audience:**
        -   Describe the primary scenarios where this repository is most useful.
        -   Define the ideal user for this project (e.g., frontend developers, data scientists).

    4.  **Getting Started: A Quick Practical Guide:**
        -   Outline the basic steps for installation and a simple "hello world" example.
        -   Mention key dependencies or prerequisites.

    5.  **Conclusion & Future Outlook:**
        -   Summarize the key takeaways and the repository's importance.
        -   Include a call to action (e.g., "Try it out," "Contribute to the project").
        -   Briefly touch on its potential future development or impact.
    """
    try:
        outline_response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        outline = cast(Mapping[str, Any], outline_response)['message']['content']
        print("--- Outline Generated ---")
    except Exception as e:
        print(f"Error generating outline: {e}")
        return

    # Step 5: Generate Full Draft
    print("Generating full draft from outline...")
    
    prompt = f"""
    You are a technical blog writer with expertise in '{language}'. Your task is to write a complete, in-depth blog post.

    **Target Audience:** Developers with intermediate experience in this field. The tone should be informative, engaging, and technically precise.

    **Instructions:**
    -   Write a ~1000-word blog post based on the provided title, context, and outline.
    -   Strictly adhere to the outline, using the points as a guide for section headers (use Markdown `##` and `###`).
    -   Naturally weave the following keywords into the text: {', '.join(keywords)}.
    -   Where appropriate, especially in the "Getting Started" section, provide clear and concise code snippets using Markdown code blocks.
    -   End with a strong conclusion and a clear call to action.

    ---
    **Title:** {title}

    **Technical Context:**
    -   **Repository:** {repo_name}
    -   **Description:** {description}
    -   **Language:** {language}
    -   **Stars:** {stars}
    -   **Topics:** {topics}

    ---
    **Outline to Follow:**
    {outline}
    ---

    Write the full blog post now.
    """
    try:
        draft_response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        draft = cast(Mapping[str, Any], draft_response)['message']['content']
    except Exception as e:
        print(f"Error generating full draft: {e}")
        return

    # Step 6: Editing and Proofreading
    print("Proofreading and correcting grammar...")
    try:
        tool = language_tool_python.LanguageTool("en-US")
        corrected_draft = tool.correct(draft)
    except Exception as e:
        print(f"Warning: Could not perform grammar check: {e}")
        corrected_draft = draft

    # Step 7: Create and Save Markdown File
    front_matter = f"""---
title: "{title.replace('"', "'")}"
date: {datetime.now().strftime("%Y-%m-%d")}
description: "An in-depth look at the {repo_name} repository, covering its features, use cases, and how to get started."
keywords: "{', '.join(keywords)}"
repository_url: "{repo_data.get('html_url', '')}"
---
"""
    final_draft = f"{front_matter}\n{corrected_draft}"
    
    filename = sanitize_filename(repo_name)
    filepath = os.path.join("posts", f"{datetime.now().strftime('%Y-%m-%d')}-{filename}.md")
    os.makedirs("posts", exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_draft)
    print(f"\n✅ Blog post successfully saved to: {filepath}")

if __name__ == "__main__":
    generate_blog_post()
