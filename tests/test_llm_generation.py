#!/usr/bin/env python3
"""
Test script for LLM-based HTML generation
"""

import json
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def create_sample_specs():
    """Create sample specs.json for testing"""
    sample_specs = {
        "url": "https://example.com",
        "business_spec": {
            "business_overview": {
                "name": "Example Coffee Co.",
                "type": "Coffee Shop",
                "industry": "Food & Beverage",
                "size_estimate": "Small (10-50 employees)"
            },
            "target_audience": {
                "demographics": ["Coffee enthusiasts", "Young professionals", "Students"],
                "needs": ["High-quality coffee", "Comfortable work space", "Fast service"],
                "pain_points": ["Low-quality coffee elsewhere", "Noisy environments", "Slow service"]
            },
            "value_proposition": {
                "problem_solution": "Providing premium coffee in a comfortable, quiet atmosphere ideal for working and socializing"
            },
            "products_services_offered": {
                "specific_coffees": [
                    {"name": "Signature Dark Roast", "price": "$4.50", "origin": "Ethiopian"},
                    {"name": "Morning Blend", "price": "$3.75", "origin": "Colombian"}
                ],
                "coffee_subscriptions": [
                    {"name": "Monthly Bean Box", "price": "$35/month", "description": "Selection of beans delivered monthly"}
                ]
            }
        },
        "brand_spec": {
            "brand_identity": {
                "personality_traits": ["Sophisticated", "Welcoming", "Authentic"],
                "character": "Knowledgeable coffee expert who is approachable and never pretentious"
            },
            "color_palette": {
                "primary_colors": [
                    {"color": "#4A3520", "meaning": "Rich, earthy coffee tones representing quality and authenticity"},
                    {"color": "#D4C3A5", "meaning": "Warm, inviting cream color representing comfort"}
                ],
                "secondary_colors": [
                    {"color": "#7D6552", "meaning": "Complementary coffee tone for depth"},
                    {"color": "#F3ECD7", "meaning": "Light cream accent for contrast"}
                ]
            },
            "typography": {
                "fonts": {
                    "Montserrat": "Used for headings to convey modern sophistication",
                    "Open Sans": "Used for body text for optimal readability"
                }
            },
            "visual_elements": {
                "layout_style": "Clean and uncluttered with generous whitespace",
                "imagery_approach": "Authentic photography of coffee, beans, and brewing process"
            },
            "voice_and_tone": {
                "communication_style": "Knowledgeable yet accessible, avoiding industry jargon",
                "language": ["Warm", "Informative", "Passionate"]
            }
        },
        "sitemap_data": {
            "pages": {
                "/": {"title": "Home"},
                "/menu": {"title": "Our Coffee Menu"},
                "/about": {"title": "About Us"},
                "/subscribe": {"title": "Coffee Subscriptions"},
                "/contact": {"title": "Contact Us"}
            }
        },
        "design_data": {
            "colors": {
                "#4A3520": 10,
                "#D4C3A5": 8,
                "#7D6552": 5,
                "#F3ECD7": 3
            },
            "fonts": ["Montserrat", "Open Sans"],
            "spacing": "generous",
            "layout": {"responsive": True}
        }
    }
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Write sample specs to file
    sample_specs_path = "output/sample_specs.json"
    with open(sample_specs_path, 'w') as f:
        json.dump(sample_specs, f, indent=2)
    
    logging.info(f"Sample specs saved to {sample_specs_path}")
    return sample_specs_path

def test_llm_generation():
    """Test LLM-based HTML generation with sample data"""
    # Create sample specs.json
    sample_specs_path = create_sample_specs()
    
    # Generate HTML using LLM
    output_path = "output/sample_llm_summary.html"
    
    # Check for Ollama configuration
    ollama_url = os.environ.get("OLLAMA_BASE_URL")
    ollama_model = os.environ.get("OLLAMA_MODEL")
    
    if not (ollama_url and ollama_model):
        logging.warning("Ollama configuration not found in environment variables.")
        logging.info("Using default Ollama configuration: http://localhost:11434 and phi4:latest")
    
    try:
        from generate_llm_summary import generate_html_from_specs
        
        logging.info("Generating HTML using Ollama LLM...")
        success = generate_html_from_specs(sample_specs_path, output_path)
        
        if success:
            logging.info(f"HTML generated successfully: {output_path}")
            return True
        else:
            logging.error("Failed to generate HTML")
            return False
    except ImportError:
        logging.error("Could not import generate_llm_summary. Make sure it's in the current directory.")
        return False

if __name__ == "__main__":
    test_llm_generation() 