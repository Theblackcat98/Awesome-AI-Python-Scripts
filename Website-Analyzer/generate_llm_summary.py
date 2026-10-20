#!/usr/bin/env python3
"""
Script to generate HTML summary from specs.json using LLM (Ollama)
"""

import json
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
import requests
import sys
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Get Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi4:latest")

def call_llm(prompt):
    """
    Call Ollama API to generate text based on prompt
    
    Args:
        prompt: Text prompt
        
    Returns:
        Generated text
    """
    try:
        api_url = f"{OLLAMA_BASE_URL}/api/generate"
        
        # Prepare the request with advanced parameters
        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "context_length": 25000,  # Extended context window
            "num_batch": 2048,        # Increased batch size
            "num_gpu": 140,           # Dedicated GPU resources
            "temperature": 0.4,       # Lower temperature for more focused outputs
            "top_k": 30,              # More selective token filtering
            "num_predict": 8192       # Generate more tokens per request
        }
        
        logging.info(f"Calling Ollama with model: {OLLAMA_MODEL} and advanced parameters")
        logging.info(f"Context length: 25000, Batch size: 2048, GPU allocation: 140")
        
        response = requests.post(api_url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            logging.error(f"Error calling Ollama API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"Error calling Ollama API: {str(e)}")
        return None

def get_template():
    """Get the HTML template from the template file"""
    try:
        from utils.templates.template_generator import get_template
        return get_template()
    except ImportError:
        logging.warning("Could not import template_generator, using default template")
        return None

def generate_html_from_specs(specs_file, output_file):
    """
    Generate HTML summary from specs.json using LLM
    
    Args:
        specs_file: Path to specs.json
        output_file: Path to output HTML file
    """
    try:
        # Read specs.json
        with open(specs_file, 'r') as f:
            specs_data = json.load(f)
        
        logging.info(f"Loaded specs data from {specs_file}")
        
        # Get the template
        template = get_template()
        
        # Create prompt for LLM
        prompt = """
You are an expert HTML developer. Your task is to generate a complete, styled HTML page that summarizes the website specification data provided below. 

The output must be ONLY valid HTML, with no markdown formatting or other text.

"""
        
        # If we have a template, include it
        if template:
            prompt += """
Here's a template to follow. You should maintain the overall structure but fill in all the appropriate 
sections with the data from the specs. You can modify the CSS as needed to improve the design:

"""
            prompt += template
            prompt += "\n\n"
        
        prompt += """
The HTML should include:
1. A header with the business name and source URL
2. Business information section with name, type, industry, target audience, and products/services
3. Brand section with identity, colors, typography, and other brand elements
4. Use a clean, modern design with appropriate CSS
5. Format all data in a user-friendly way

Only include information that is found in the specification data. Do not make up or hallucinate any additional content.
Do not include any GitHub repository content, file paths, or code snippets unless they are actually in the specs data.

Here's the specification data (in JSON format):
"""
        prompt += json.dumps(specs_data, indent=2)
        
        # Call LLM
        logging.info("Calling Ollama to generate HTML with enhanced processing power...")
        html_content = call_llm(prompt)
        
        if not html_content:
            logging.error("Failed to generate HTML content")
            return False
        
        # Write HTML to file
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logging.info(f"HTML summary saved to {output_file}")
        return True
        
    except Exception as e:
        logging.error(f"Error generating HTML from specs: {str(e)}")
        return False

def main():
    """Main function to parse arguments and generate HTML"""
    parser = argparse.ArgumentParser(description='Generate HTML summary from specs.json using LLM')
    parser.add_argument('--specs', type=str, default='output/specs.json', help='Path to specs.json file')
    parser.add_argument('--output', type=str, default='output/llm_summary.html', help='Path to output HTML file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.specs):
        logging.error(f"Specs file not found: {args.specs}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    if generate_html_from_specs(args.specs, args.output):
        logging.info(f"Successfully generated HTML summary: {args.output}")
    else:
        logging.error("Failed to generate HTML summary")
        sys.exit(1)

if __name__ == "__main__":
    main() 