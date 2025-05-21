#!/usr/bin/env python3
import logging
import sys
import os
from nodes import (
    InitialFetchNode, SitemapBatchNode, DesignElementsBatchNode, 
    ContentBatchNode, CombineResultsNode, GenerateSpecsNode, 
    CreateHtmlSummaryNode, Flow
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_initial_fetch(url):
    """Test the initial fetch node."""
    print(f"\n=== Testing InitialFetchNode with {url} ===")
    node = InitialFetchNode()
    shared = {"url": url}
    
    try:
        action = node.run(shared)
        print(f"- Action: {action}")
        print(f"- Soup object created: {'soup' in shared}")
        print(f"- Status code: {shared.get('initial_status')}")
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_sitemap_batch(url, max_pages=3):
    """Test the sitemap batch node."""
    print(f"\n=== Testing SitemapBatchNode with {url} (max_pages={max_pages}) ===")
    node = SitemapBatchNode()
    shared = {"url": url, "max_pages": max_pages}
    
    try:
        action = node.run(shared)
        print(f"- Action: {action}")
        print(f"- Sitemap pages found: {len(shared.get('sitemap', {}).get('pages', {}))}")
        print(f"- Pages discovered: {len(shared.get('pages_to_process', []))}")
        print(f"- Pages visited: {len(shared.get('visited_urls', []))}")
        
        # Print first few pages in sitemap
        sitemap_pages = list(shared.get('sitemap', {}).get('pages', {}).keys())
        if sitemap_pages:
            print("- First few pages:")
            for key in sitemap_pages[:3]:
                print(f"  - {key}")
        
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_design_elements_batch(url, max_pages=3):
    """Test the design elements batch node after running sitemap."""
    print(f"\n=== Testing DesignElementsBatchNode with {url} ===")
    
    # First, build sitemap
    sitemap_node = SitemapBatchNode()
    shared = {"url": url, "max_pages": max_pages}
    sitemap_node.run(shared)
    
    # Then extract design elements
    design_node = DesignElementsBatchNode()
    
    try:
        action = design_node.run(shared)
        print(f"- Action: {action}")
        
        design = shared.get('design', {})
        print(f"- Colors found: {len(design.get('colors', {}))}")
        print(f"- Fonts found: {len(design.get('fonts', []))}")
        print(f"- Layout info:")
        print(f"  - Sections: {design.get('layout', {}).get('sections', 0)}")
        print(f"  - Columns: {design.get('layout', {}).get('columns', False)}")
        print(f"  - Responsive: {design.get('layout', {}).get('responsive', False)}")
        print(f"- Images found: {design.get('images', {}).get('count', 0)}")
        
        # Print some colors if available
        colors = list(design.get('colors', {}).items())
        if colors:
            print("- Top colors:")
            for color, count in colors[:3]:
                print(f"  - {color}: {count}")
        
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_content_batch(url, max_pages=3):
    """Test the content batch node after running sitemap."""
    print(f"\n=== Testing ContentBatchNode with {url} ===")
    
    # First, build sitemap
    sitemap_node = SitemapBatchNode()
    shared = {"url": url, "max_pages": max_pages}
    sitemap_node.run(shared)
    
    # Then extract content
    content_node = ContentBatchNode()
    
    try:
        action = content_node.run(shared)
        print(f"- Action: {action}")
        
        content = shared.get('content', {})
        print(f"- Page title: {content.get('page_title', 'N/A')}")
        print(f"- Business name: {content.get('business_info', {}).get('name', 'N/A')}")
        print(f"- Business type: {content.get('business_type', {}).get('type', 'N/A')} (confidence: {content.get('business_type', {}).get('confidence', 0)}%)")
        print(f"- Word count: {content.get('word_count', 0)}")
        print(f"- Main sections: {len(content.get('main_content', {}).get('main', []))}")
        
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_complete_flow(url, max_pages=3, output_dir="output"):
    """Test the complete Website Cloner flow."""
    print(f"\n=== Testing complete flow with {url} (max_pages={max_pages}) ===")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create flow
    flow = Flow()
    
    # Add nodes to flow
    initial_fetch = InitialFetchNode()
    sitemap_batch = SitemapBatchNode()
    design_batch = DesignElementsBatchNode()
    content_batch = ContentBatchNode()
    combine_results = CombineResultsNode()
    generate_specs = GenerateSpecsNode()
    create_html = CreateHtmlSummaryNode()
    
    # Connect nodes
    flow.add_node("initial_fetch", initial_fetch)
    flow.add_node("sitemap_batch", sitemap_batch)
    flow.add_node("design_batch", design_batch)
    flow.add_node("content_batch", content_batch)
    flow.add_node("combine_results", combine_results)
    flow.add_node("generate_specs", generate_specs)
    flow.add_node("create_html", create_html)
    
    # Define transitions
    flow.add_transition("initial_fetch", "next", "sitemap_batch")
    flow.add_transition("sitemap_batch", "next", "design_batch")
    flow.add_transition("design_batch", "next", "content_batch")
    flow.add_transition("content_batch", "next", "combine_results")
    flow.add_transition("combine_results", "next", "generate_specs")
    flow.add_transition("generate_specs", "next", "create_html")
    
    # Prepare shared data
    shared = {
        "url": url, 
        "max_pages": max_pages,
        "output_dir": output_dir
    }
    
    try:
        # Run the flow
        flow.run(shared, "initial_fetch")
        
        # Check results
        print("\nFlow execution completed. Results:")
        print(f"- Sitemap pages: {len(shared.get('sitemap', {}).get('pages', {}))}")
        print(f"- Colors identified: {len(shared.get('design', {}).get('colors', {}))}")
        print(f"- Business name: {shared.get('content', {}).get('business_info', {}).get('name', 'N/A')}")
        
        # Check output files
        specs_file = os.path.join(output_dir, "specs.json")
        html_file = os.path.join(output_dir, "summary.html")
        
        print(f"- Specs file created: {os.path.exists(specs_file)}")
        print(f"- HTML summary created: {os.path.exists(html_file)}")
        
        return True
    except Exception as e:
        print(f"ERROR in flow execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests for Website Cloner components."""
    if len(sys.argv) < 2:
        print("Usage: python test_flow.py URL [max_pages] [output_dir] [--full]")
        return 1
    
    url = sys.argv[1]
    full_test = "--full" in sys.argv
    
    # Remove --full from sys.argv if present to avoid interfering with other argument parsing
    args = [arg for arg in sys.argv if arg != "--full"]
    
    # Parse max_pages and output_dir
    max_pages = 3  # Default value
    output_dir = "output"  # Default value
    
    if len(args) > 2:
        try:
            max_pages = int(args[2])
        except ValueError:
            # If the second argument isn't an integer, assume it's the output_dir
            output_dir = args[2]
    
    if len(args) > 3:
        output_dir = args[3]
    
    print(f"Testing Website Cloner components with URL: {url}, max_pages: {max_pages}")
    
    if full_test:
        # Run complete flow test
        if not test_complete_flow(url, max_pages, output_dir):
            print("Complete flow test failed.")
            return 1
        print("\nComplete flow test passed successfully!")
        return 0
    
    # Run tests for each component
    if not test_initial_fetch(url):
        print("Initial fetch test failed. Stopping tests.")
        return 1
    
    if not test_sitemap_batch(url, max_pages):
        print("Sitemap batch test failed. Stopping tests.")
        return 1
    
    if not test_design_elements_batch(url, max_pages):
        print("Design elements batch test failed. Stopping tests.")
        return 1
    
    if not test_content_batch(url, max_pages):
        print("Content batch test failed. Stopping tests.")
        return 1
    
    print("\nAll component tests completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main()) 