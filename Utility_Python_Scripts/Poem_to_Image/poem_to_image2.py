# To run this code you need to install the following dependencies:
# pip install google-genai pillow
# To run this code you need to install the following dependencies:
# pip install google-genai pillow

from google.genai import types
from google import genai
import os
from PIL import Image
from io import BytesIO
import re
import json # Import the json library
import dotenv

dotenv.load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Create the client
client = genai.Client(api_key=GEMINI_API_KEY)


OUTPUT_DIR = "poem_images"

# --- Input Data ---
def load_poems_from_json(file_path: str) -> list:
    """
    Reads and parses a JSON file containing a list of poems.

    Args:
        file_path: The path to the JSON file.

    Returns:
        A list of dictionaries, where each dictionary represents a poem.
        Returns an empty list if the file is not found or is invalid JSON.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            poems = json.load(f)
            return poems
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Please make sure the file exists.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}. Please check the file format.")
        return []

# Load meta prompt from gen_prompt.md

with open("image_gen_prompt.md", "r") as f:
    SYSTEM_PROMPT = f.read()

    USER_PROMPT = ( # Use a default meta-prompt if the file is not found
        "--- POEM ---\nTitle: {title}\n\n{poem}\n\n--- PROMPT ---"
    )

def generate_prompt_from_poem(title: str, poem: str) -> str | None:

    print(f"Generating prompt for '{title}'...")

    template_prompt = USER_PROMPT.format(title=title, poem=poem)


    try:
        # Use the new API to generate text
        # print(f"template_prompt: {template_prompt}")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=template_prompt),
                    ],
                ),
            ],
            config=types.GenerateContentConfig(
                system_instruction=[
                    types.Part.from_text(text=SYSTEM_PROMPT),
                ],
            )
        )

        # Navigate the Gemini API response structure and extract only the prompt part
        if response and response.text:
            response_text = response.text
            prompt_marker = "--- IMAGE PROMPT ---" # Updated marker based on meta-prompt structure
            if prompt_marker in response_text:
                # Split by the marker and take the part after it
                prompt_text = response_text.split(prompt_marker, 1)[1].strip()
            else:
                # If the marker is not found, use the whole response text as the prompt
                # You might want to adjust the meta-prompt to ensure the marker is always present
                print(f"  > Warning: Prompt marker '{prompt_marker}' not found in response. Using full response as prompt.")
                prompt_text = response_text.strip()

            print(f"  > Generated Prompt: {prompt_text}")
            return prompt_text if prompt_text else None # Return None if the extracted prompt is empty
        else:
            print(f"  > Error: No content returned from Gemini API. Response: {response}")
            return None

    except Exception as e:
        print(f"  > Error calling Gemini API: {e}")
        return None

def generate_image_with_imagen(prompt: str, output_filename: str) -> bool:
    """
    Uses Imagen to generate an image from a prompt and saves it.

    Args:
        prompt: The descriptive prompt for the image.
        output_filename: The path where the generated image will be saved.

    Returns:
        True if the image was generated and saved successfully, False otherwise.

    """
    print(f"Generating image for file '{output_filename}'...")


    try:
        # Use the new API to generate images
        # The Imagen part of the API might also need adjustment based on the correct import and client initialization
        # Assuming the client is initialized correctly with the new import

        result = client.models.generate_images(
            model="models/imagen-4.0-ultra-generate-preview-06-06",
            prompt=prompt,
            config=dict(
                number_of_images=1,
                output_mime_type="image/jpeg",
                person_generation="ALLOW_ADULT",
                aspect_ratio="16:9",
            ),
        )

        if not result.generated_images:
            print("No images generated.")
            return False

        if len(result.generated_images) != 1:
            print("Number of images generated does not match the requested number.")
            return False

        for generated_image in result.generated_images:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            image.save(output_filename) # Save the image instead of showing it
            print(f"  > Successfully saved image to {output_filename}")
            return True

    except Exception as e:
        print(f"  > Error calling Imagen API: {e}")
        return False


def save_prompt_to_file(prompt_content: str, file_path: str):
    """
    Saves the generated prompt content to a text file.

    Args:
        prompt_content: The string content of the prompt.
        file_path: The full path to the file where the prompt will be saved.
    """
    try:
        with open(file_path, "w") as f:
            f.write(prompt_content)
        print(f"  > Successfully saved prompt to {file_path}")
    except IOError as e:
        print(f"  > Error saving prompt to file: {e}")


def main():
    """
    Main function to orchestrate the poem-to-image generation process.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    # Load poems from the JSON file
    poems = load_poems_from_json("allpoems.json")
    if not poems:
        print("No poems to process. Exiting.")
        return

    # TEMPORARY: Process only the first 2 poems for testing
    poems = poems[:100]

    # Process each poem in the input data
    for item in poems:
        title = item["titlelist"]
        poem = item["content"]

        # Sanitize the title to create a valid filename
        sanitized_title = re.sub(r'[^\w\-_\. ]', '_', title).replace(' ', '_').lower()
        prompt_filename = f"{sanitized_title}_prompt.txt"
        prompt_filepath = os.path.join(OUTPUT_DIR, prompt_filename)
        output_path = os.path.join(OUTPUT_DIR, f"{sanitized_title}.png")

        # 1. Generate a prompt from the poem
        if os.path.exists(prompt_filepath):
            print(f"Prompt file already exists for '{title}'. Loading from file.")
            with open(prompt_filepath, "r") as f:
                image_prompt = f.read()
        else:
            image_prompt = generate_prompt_from_poem(title, poem)
            if image_prompt:
                save_prompt_to_file(image_prompt, prompt_filepath)

        if not image_prompt:
            print(f"Skipping image generation for '{title}' due to prompt generation failure.\n")
            continue

        # 2. Generate an image from the prompt
        if os.path.exists(output_path):
            print(f"Image file already exists for '{title}'. Skipping image generation.")
        else:
            # generate_image_with_imagen(image_prompt, output_path)
            pass
        
        print("-" * 20) # Separator for clarity

    print("Script finished.")


if __name__ == "__main__":
    main()