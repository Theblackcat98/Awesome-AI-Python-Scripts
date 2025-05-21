"""
Website Cloner Flow - This module defines the flow for the Website Cloner application.

The flow connects nodes in a structured manner to implement the Map-Reduce pattern.
It handles transitions between nodes and ensures proper execution order.
"""

from nodes import (
    Flow, InitialFetchNode, SitemapBatchNode, DesignElementsBatchNode, 
    ContentBatchNode, CombineResultsNode, GenerateSpecsNode, CreateHtmlSummaryNode,
    Node, ExtractContentNode
)
import logging

# Add a simple error handling node
class ErrorHandlingNode(Node):
    def exec(self, prep_res):
        """Handle errors gracefully."""
        error_message = prep_res.get("error_message", "Unknown error occurred")
        error_source = prep_res.get("error_source", "unknown")
        
        logging.error(f"Error in {error_source}: {error_message}")
        
        # Here you could add more advanced error handling:
        # - Retry with different parameters
        # - Fall back to cached data
        # - Attempt alternative scraping methods
        
        return {"handled": True, "message": f"Error handled: {error_message}"}
    
    def post(self, shared, prep_res, exec_res):
        """Store error info and continue."""
        shared["error_handled"] = exec_res["handled"]
        shared["error_message"] = exec_res["message"]
        shared["succeeded"] = False
        return "complete"

def create_website_cloner_flow(parallel_processing=True):
    """Create the Website Cloner flow.
    
    Args:
        parallel_processing (bool): Whether to execute design and content extraction in parallel
        
    Returns:
        Flow: The configured flow
    """
    flow = Flow()
    
    # Create nodes
    initial_fetch = InitialFetchNode()
    sitemap_batch = SitemapBatchNode()
    design_batch = DesignElementsBatchNode()
    content_batch = ContentBatchNode()
    extract_content = ExtractContentNode()
    combine_results = CombineResultsNode()
    generate_specs = GenerateSpecsNode()
    create_html = CreateHtmlSummaryNode()
    error_handler = ErrorHandlingNode()
    
    # Add nodes to flow
    flow.add_node("initial_fetch", initial_fetch)
    flow.add_node("sitemap_batch", sitemap_batch)
    flow.add_node("design_batch", design_batch)
    flow.add_node("content_batch", content_batch)
    flow.add_node("extract_content", extract_content)
    flow.add_node("combine_results", combine_results)
    flow.add_node("generate_specs", generate_specs)
    flow.add_node("create_html", create_html)
    flow.add_node("error_handler", error_handler)
    
    # Define transitions
    # Initial fetch to Sitemap
    flow.add_transition("initial_fetch", "next", "sitemap_batch")
    flow.add_transition("initial_fetch", "error", "error_handler")
    
    # Sitemap node can loop back to itself with "continue"
    flow.add_transition("sitemap_batch", "continue", "sitemap_batch")
    flow.add_transition("sitemap_batch", "next", "design_batch")
    flow.add_transition("sitemap_batch", "error", "error_handler")
    
    # Design and content nodes
    flow.add_transition("design_batch", "next", "extract_content")
    flow.add_transition("design_batch", "error", "error_handler")
    flow.add_transition("extract_content", "next", "combine_results")
    flow.add_transition("extract_content", "error", "error_handler")
    
    # Keep the old content_batch for backward compatibility
    flow.add_transition("content_batch", "next", "combine_results")
    flow.add_transition("content_batch", "error", "error_handler")
    
    # Add parallel path if enabled
    if parallel_processing:
        flow.add_transition("sitemap_batch", "parallel", "content_batch")
    
    # Final flow steps
    flow.add_transition("combine_results", "next", "generate_specs")
    flow.add_transition("combine_results", "error", "error_handler")
    flow.add_transition("generate_specs", "next", "create_html")
    flow.add_transition("generate_specs", "error", "error_handler")
    flow.add_transition("create_html", "error", "error_handler")
    
    return flow
