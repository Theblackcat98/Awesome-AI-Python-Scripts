#!/usr/bin/env python3
import logging
import argparse
import os
from dotenv import load_dotenv
from flow import create_website_cloner_flow

# Load environment variables
load_dotenv()

def main():
    """Run the Website Cloner."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Website Cloner - Analyze websites and generate specifications")
    parser.add_argument("--url", required=True, help="URL of the website to analyze")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to crawl (default: 10)")
    parser.add_argument("--output-dir", default="output", help="Directory to save output files (default: output)")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel processing of design and content")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--skip-design", action="store_true", help="Skip design element extraction")
    parser.add_argument("--skip-content", action="store_true", help="Skip content extraction")
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("website_cloner")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Prepare shared data
    shared = {
        "url": args.url,
        "max_pages": args.max_pages,
        "output_dir": args.output_dir,
        "skip_design": args.skip_design,
        "skip_content": args.skip_content,
        "succeeded": True  # Will be set to False if errors occur
    }
    
    # Create and run the flow
    logger.info(f"Starting Website Cloner for {args.url}")
    
    try:
        flow = create_website_cloner_flow(not args.no_parallel)
        flow.run(shared, "initial_fetch")
        
        # Check if there was an error
        if shared.get("succeeded", True) == False:
            error_message = shared.get("error_message", "Unknown error occurred")
            logger.error(f"Website cloning failed: {error_message}")
            logger.info(f"Try using a different URL or check website access permissions.")
            return 1
            
        specs_file = os.path.join(args.output_dir, "specs.json")
        html_file = os.path.join(args.output_dir, "summary.html")
        
        logger.info(f"Website cloning completed successfully!")
        logger.info(f"Specifications saved to: {specs_file}")
        logger.info(f"HTML summary saved to: {html_file}")
        
        return 0
    except Exception as e:
        logger.error(f"Error during website cloning: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info(f"Try using a different URL or check website access permissions.")
        return 1

if __name__ == "__main__":
    exit(main())
