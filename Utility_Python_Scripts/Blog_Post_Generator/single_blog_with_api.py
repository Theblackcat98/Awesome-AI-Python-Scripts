import requests
import language_tool_python
import os
import random
import re
from datetime import datetime
from ollama import Client

# --- Configuration: Set your niche ---
# Options: travel, tech, gaming, food, history, nature, art, music, sports, health, science, literature, space
NICHE = "tech" 

# --- Helper Functions for Topic Generation (Fixes the core logical error) ---
# By selecting the random item ONCE, we ensure consistency.

def _generate_travel_topic(data):
    country = random.choice(data)
    name = country.get('name', {}).get('common', 'an amazing destination')
    return (
        f"Top Cultural Highlights of {name}",
        [f"cultural highlights {name}", f"{name} travel tips", f"{name} culture guide"],
        country
    )

def _generate_tech_topic(data):
    # Note: GitHub's /trending endpoint was deprecated. Using a different one.
    # This now gets a list of public repositories.
    repo = random.choice(data)
    name = repo.get('name', 'a cool project')
    return (
        f"Top Features of the {name.capitalize()} Repository in 2025",
        [f"{name} features", "tech trends 2025", "open source tools"],
        repo
    )

def _generate_gaming_topic(data):
    pokemon_info = random.choice(data.get('results', []))
    name = pokemon_info.get('name', 'a pokemon').capitalize()
    # Fetch detailed data for the chosen pokemon
    try:
        detailed_data = requests.get(pokemon_info['url']).json()
    except Exception:
        detailed_data = {"name": name, "info": "Could not fetch details."}
    return (
        f"Why {name} Will Dominate the Competitive Scene in 2025",
        [f"{name} competitive guide", "Pokémon trends 2025", "gaming tips"],
        detailed_data
    )

def _generate_food_topic(data):
    meal = random.choice(data.get('meals', []))
    name = meal.get('strMeal', 'a delicious dish')
    return (
        f"Delicious {name} Recipes for Any Occasion",
        [f"{name} recipe", "cooking tips 2025", "food trends"],
        meal
    )
    
def _generate_art_topic(data):
    artwork = random.choice(data.get('data', []))
    title = artwork.get('title', 'a masterpiece')
    return (
        f"Exploring the Symbolism in '{title}'",
        [f"{title} analysis", "art interpretation", "art history"],
        artwork
    )

def _generate_space_topic(data):
    body = random.choice(data.get('bodies', []))
    name = body.get('englishName', 'a celestial body')
    if not name: name = body.get('name', 'a celestial body') # Fallback for moons etc.
    return (
        f"Fascinating Facts About {name}",
        [f"{name} facts", "space exploration 2025", "astronomy"],
        body
    )

# --- API Sources Dictionary ---
# Using the helper functions makes this section much cleaner and corrects the logic.
API_SOURCES = {
    "travel": {"url": "https://restcountries.com/v3.1/all", "generator": _generate_travel_topic},
    "tech": {"url": "https://api.github.com/repositories", "generator": _generate_tech_topic},
    "gaming": {"url": "https://pokeapi.co/api/v2/pokemon?limit=151", "generator": _generate_gaming_topic},
    "food": {"url": "https://www.themealdb.com/api/json/v1/1/search.php?s=", "generator": _generate_food_topic},
    "art": {"url": "https://api.artic.edu/api/v1/artworks?limit=50", "generator": _generate_art_topic},
    "space": {"url": "https://api.le-systeme-solaire.net/rest/bodies/", "generator": _generate_space_topic},
    # Note: Some of the original APIs were unreliable or required more complex parsing.
    # The list below uses simpler, more direct data structures.
    "history": {"url": "http://history.muffinlabs.com/date", "generator": lambda data: (f"On This Day: Fascinating Events from {data.get('date', '')}", ["historical events", "history facts", "on this day"], data.get('data', {}).get('Events', []))},
    "science": {"url": "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", "generator": lambda data: (f"Exploring {data.get('title', 'a Cosmic Wonder')}", [data.get('title', '').lower(), "science discoveries", "NASA"], data)},
}

def sanitize_filename(title):
    """Removes invalid characters from a string to make it a valid filename."""
    # Remove invalid characters
    sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
    # Replace spaces with hyphens
    sanitized = sanitized.replace(' ', '-').lower()
    # Truncate to a reasonable length
    return sanitized[:100]

def generate_topic(niche):
    """Generate a topic based on the selected niche and API."""
    print(f"Generating topic for niche: {niche}...")
    try:
        if niche in API_SOURCES:
            source = API_SOURCES[niche]
            response = requests.get(source["url"], timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            topic, keywords, api_data = source["generator"](data)
            return topic, keywords, api_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {niche}: {e}")
    except Exception as e:
        print(f"Error generating topic for {niche}: {e}")
    
    # Fallback if API fails or niche is not in the list
    print("Using fallback topic generator.")
    topic = f"Top Trends in {niche.capitalize()} for 2025"
    keywords = [f"{niche} trends 2025", f"best {niche} tips", f"{niche} guide"]
    api_data = {}
    return topic, keywords, api_data

def generate_blog_post():
    # Step 1: Topic Ideation
    topic, keywords, api_data = generate_topic(NICHE)
    title = topic
    print(f"Generated Title: {title}")
    print(f"Keywords: {', '.join(keywords)}")

    # Step 2: Connect to Ollama
    try:
        ollama = Client(host='http://localhost:11434')
        models = ollama.list()['models']
        # More robust check for the model
        if not any('llama3.1' in model['name'] for model in models):
            print("Error: A 'llama3.1' model was not found.")
            print("Available models:", [model['name'] for model in models])
            print("Please run: ollama pull llama3.1")
            return
        MODEL_NAME = 'llama3.1' # Or whichever version you have
        print(f"Successfully connected to Ollama and found model: {MODEL_NAME}")
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print("Please ensure Ollama is running on http://localhost:11434.")
        return

    # Step 3: Generate Outline
    print("Generating outline...")
    prompt = f"Create a detailed blog post outline for the title: '{title}'. The outline should include a compelling introduction, 3 to 4 main body sections with bullet points for each, and a concluding paragraph. Use the following keywords naturally in the outline: {', '.join(keywords)}."
    try:
        outline_response_iter = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        outline_response = list(outline_response_iter)[0]
        outline = outline_response
        print("--- Outline ---\n", outline, "\n---------------")
    except Exception as e:
        print(f"Error generating outline: {e}")
        outline = "Introduction\nSection 1: Overview\nSection 2: Key Details\nSection 3: Future Implications\nConclusion" # Fallback outline

    # Step 4: Generate Content from Outline
    print("Generating full draft from outline...")
    # Truncate API data to avoid exceeding context window. Convert to string.
    api_data_str = str(api_data)[:1500] 
    
    prompt = f"""
    You are a helpful blog post writer. Write a complete, 1000-word blog post based on the following outline and information.
    
    Title: {title}
    
    Keywords to include: {', '.join(keywords)}
    
    Factual data to reference (optional): {api_data_str}
    
    Outline to follow:
    ---
    {outline}
    ---
    
    Write the full blog post now in a conversational and engaging tone. Use Markdown for formatting (e.g., ## for headings).
    """
    try:
        draft_response_iter = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        draft_response = list(draft_response_iter)[0]  # Convert iterator to list and get first item
        draft = draft_response
    except Exception as e:
        print(f"Error generating full draft: {e}")
        draft = f"## {title}\n\nAn error occurred while generating the content."

    # Step 5: Editing and Proofreading
    print("Proofreading and correcting grammar...")
    try:
        tool = language_tool_python.LanguageTool("en-US")
        # Ensure draft is a string (some API responses may be dicts)
        if isinstance(draft, dict) and 'message' in draft:
            draft_text = draft['message']
        elif isinstance(draft, dict) and 'content' in draft:
            draft_text = draft['content']
        else:
            draft_text = str(draft)
        corrected_draft = tool.correct(draft_text)
    except Exception as e:
        print(f"Warning: Could not perform grammar check: {e}")
        print("This might be because Java is not installed or language tool failed to download.")
        corrected_draft = str(draft)  # Fallback to unedited draft

    # Step 6: Create Final Markdown File
    front_matter = f"""---
title: "{title.replace('"', "'")}"
date: {datetime.now().strftime("%Y-%m-%d")}
description: "An in-depth look at {title.lower()}, exploring trends and insights for the {NICHE} niche."
keywords: "{', '.join(keywords)}"
---
"""
    final_draft = f"{front_matter}\n{corrected_draft}"

    # Step 7: Save Markdown
    filename = sanitize_filename(title)
    filepath = os.path.join("posts", f"{datetime.now().strftime('%Y-%m-%d')}-{filename}.md")
    os.makedirs("posts", exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_draft)
    print(f"\n✅ Blog post successfully saved to: {filepath}")

if __name__ == "__main__":
    generate_blog_post()
