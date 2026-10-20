#!/usr/bin/env python3
"""
Simple wrapper script to generate website summary using LLM
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Parse arguments and generate summary"""
    parser = argparse.ArgumentParser(description='Generate website summary')
    parser.add_argument('--specs', type=str, default='output/specs.json', help='Path to specs.json file')
    parser.add_argument('--output', type=str, default='output/website_summary.html', help='Path to output HTML file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.specs):
        logging.error(f"Specs file not found: {args.specs}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Call the LLM-based summary generator
    logging.info("Generating website summary using LLM...")
    
    # Import the LLM-based generator and generate summary
    try:
        from generate_llm_summary import generate_html_from_specs
        if generate_html_from_specs(args.specs, args.output):
            logging.info(f"Successfully generated HTML summary: {args.output}")
            return 0
        else:
            logging.error("Failed to generate HTML summary")
            return 1
    except ImportError:
        logging.error("Failed to import LLM-based summary generator. Using fallback method.")
        # Fallback to the original render_html.py if the LLM-based generator is not available
        try:
            # Try to use render_html.py as a fallback
            import subprocess
            cmd = [sys.executable, "render_html.py", args.specs, args.output]
            subprocess.run(cmd, check=True)
            logging.info(f"Generated HTML summary using fallback method: {args.output}")
            return 0
        except Exception as e:
            logging.error(f"Error using fallback method: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main()) 