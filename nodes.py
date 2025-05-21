"""
Website Cloner - Node-based implementation of Map-Reduce pattern for website analysis.

This module defines the core node classes for processing websites in a structured manner:

1. Base Classes:
   - Node: Base class for all processing nodes
   - BatchNode: Specialized node for batch processing
   - Flow: Manages the flow of data between nodes

2. Map Phase Nodes:
   - InitialFetchNode: Fetches the initial page content
   - SitemapBatchNode: Builds a sitemap by crawling website
   - DesignElementsBatchNode: Extracts design elements from pages
   - ContentBatchNode: Extracts content and business info from pages

3. Reduce Phase Nodes:
   - CombineResultsNode: Combines results from the map phase
   - GenerateSpecsNode: Generates business and brand specifications
   - CreateHtmlSummaryNode: Creates a visual HTML summary

The Map-Reduce pattern is implemented with:
- Map: Processing each page independently and in batches
- Reduce: Combining results and generating specifications
"""

import logging
from urllib.parse import urlparse, urljoin
from utils.get_website_content import get_website_content
from utils.build_sitemap import is_valid_url
from utils.extract_design_elements import extract_design_elements
from utils.extract_content import extract_content
from utils.generate_specs import generate_specs, save_specs
from utils.generate_html_summary import generate_html_summary, save_html_summary

# Base Node class for all nodes
class Node:
    def __init__(self, max_retries=1, wait=0):
        self.max_retries = max_retries
        self.wait = wait
        self.cur_retry = 0
        
    def prep(self, shared):
        """Prepare data for execution."""
        return shared
        
    def exec(self, prep_res):
        """Execute main logic."""
        return prep_res
        
    def exec_fallback(self, prep_res, exc):
        """Handle exceptions after retries are exhausted."""
        logging.error(f"Error in node execution: {str(exc)}")
        raise exc
        
    def post(self, shared, prep_res, exec_res):
        """Post-process and update shared store."""
        return "default"
        
    def run(self, shared):
        """Run the node with the shared store."""
        try:
            prep_res = self.prep(shared)
            
            self.cur_retry = 0
            while True:
                try:
                    exec_res = self.exec(prep_res)
                    break
                except Exception as e:
                    self.cur_retry += 1
                    if self.cur_retry >= self.max_retries:
                        exec_res = self.exec_fallback(prep_res, e)
                        break
                    import time
                    time.sleep(self.wait)
            
            action = self.post(shared, prep_res, exec_res)
            return action or "default"
        except Exception as e:
            logging.error(f"Error running node: {str(e)}")
            raise e

# Batch Node for processing items in batches
class BatchNode(Node):
    def __init__(self, max_retries=1, wait=0):
        super().__init__(max_retries, wait)
        
    def prep(self, shared):
        """Return an iterable to process in batch."""
        return []
        
    def exec(self, item):
        """Process a single item in the batch."""
        return item
        
    def post(self, shared, prep_res, exec_res_list):
        """Process the list of results from batch execution."""
        return "default"
        
    def run(self, shared):
        """Run the batch node with the shared store."""
        try:
            # Get list of items to process
            items = self.prep(shared)
            
            # Process each item
            results = []
            for item in items:
                self.cur_retry = 0
                while True:
                    try:
                        result = self.exec(item)
                        results.append(result)
                        break
                    except Exception as e:
                        self.cur_retry += 1
                        if self.cur_retry >= self.max_retries:
                            try:
                                result = self.exec_fallback(item, e)
                                results.append(result)
                            except:
                                # If fallback also fails, continue with next item
                                logging.error(f"Failed to process item {item}: {str(e)}")
                            break
                        import time
                        time.sleep(self.wait)
            
            # Post-process batch results
            action = self.post(shared, items, results)
            return action or "default"
        except Exception as e:
            logging.error(f"Error running batch node: {str(e)}")
            raise e

# Flow class to connect nodes
class Flow(Node):
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.transitions = {}
        
    def add_node(self, node_name, node):
        """Add a node to the flow with a name."""
        self.nodes[node_name] = node
        
    def add_transition(self, from_node, action, to_node):
        """Add a transition from one node to another based on action."""
        if from_node not in self.transitions:
            self.transitions[from_node] = {}
        self.transitions[from_node][action] = to_node
        
    def run(self, shared, start_node):
        """Run the flow starting from the specified node name."""
        if start_node not in self.nodes:
            raise ValueError(f"Node '{start_node}' not found in flow")
            
        current_node_name = start_node
        
        while current_node_name:
            current_node = self.nodes[current_node_name]
            
            # Run the current node
            try:
                logging.info(f"Running node: {current_node_name}")
                action = current_node.run(shared)
                logging.info(f"Node {current_node_name} completed with action: {action}")
                
                # Handle transitions based on action
                if current_node_name in self.transitions and action in self.transitions[current_node_name]:
                    current_node_name = self.transitions[current_node_name][action]
                    
                    # Check for parallel actions
                    if action == "parallel":
                        # Save the next node to return to after parallel execution
                        next_after_parallel = current_node_name
                        
                        # Find all parallel transitions from the originating node
                        parallel_nodes = []
                        orig_node = list(self.transitions.keys())[list(self.transitions.values()).index({action: current_node_name})]
                        
                        for act, node in self.transitions[orig_node].items():
                            if act != "next" and act != "default" and node != next_after_parallel:
                                parallel_nodes.append(node)
                        
                        # Execute parallel nodes
                        for node_name in parallel_nodes:
                            logging.info(f"Executing parallel node: {node_name}")
                            self.nodes[node_name].run(shared)
                            
                        # Continue with the main flow
                        current_node_name = next_after_parallel
                    
                elif action == "next" and current_node_name in self.transitions:
                    # Default to "next" if available
                    for next_action, next_node in self.transitions[current_node_name].items():
                        if next_action == "next":
                            current_node_name = next_node
                            break
                    else:
                        # No "next" transition found
                        break
                else:
                    # No matching transition
                    break
            except Exception as e:
                logging.error(f"Error in node {current_node_name}: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
                raise
                
        return "complete"

# Map phase nodes
class InitialFetchNode(Node):
    def exec(self, prep_res):
        """Fetch the initial page content."""
        url = prep_res.get("url")
        if not url:
            raise ValueError("No URL provided")
            
        soup, status, error = get_website_content(url)
        if error:
            logging.error(f"Error fetching {url}: {error}")
            return {"error": error, "status": 0}
            
        return {"soup": soup, "status": status}
        
    def post(self, shared, prep_res, exec_res):
        """Store the initial soup object."""
        if "error" in exec_res:
            shared["error_message"] = f"Error fetching URL: {exec_res['error']}"
            shared["error_source"] = "initial_fetch"
            shared["succeeded"] = False
            return "error"
            
        shared["soup"] = exec_res["soup"]
        shared["initial_status"] = exec_res["status"]
        return "next"

class SitemapBatchNode(BatchNode):
    def __init__(self, max_retries=1, wait=0, max_iterations=30):
        super().__init__(max_retries, wait)
        self.max_iterations = max_iterations
        self.iteration = 0
        
    def prep(self, shared):
        """Prepare URLs to crawl."""
        if "url" not in shared:
            raise ValueError("No base URL provided")
            
        # On first run, initialize sitemap data
        if "sitemap" not in shared:
            base_url = shared["url"]
            shared["pages_to_process"] = [base_url]
            shared["pages_visited"] = set()
            shared["sitemap"] = {
                "base_url": base_url,
                "pages": {}
            }
            
            # Parse base URL
            parsed_base = urlparse(base_url)
            shared["base_domain"] = parsed_base.netloc
        
        # Filter out URLs that have already been visited
        to_process = []
        max_pages = shared.get("max_pages", 20)
        
        # Only process up to max_pages - already visited
        pages_remaining = max_pages - len(shared.get("pages_visited", set()))
        
        for url in shared["pages_to_process"]:
            if url not in shared.get("pages_visited", set()) and len(to_process) < pages_remaining:
                to_process.append(url)
        
        # Clear pages_to_process and rebuild with remaining pages
        remaining = [url for url in shared["pages_to_process"] if url not in to_process and url not in shared.get("pages_visited", set())]
        shared["pages_to_process"] = remaining
        
        # Increment iteration counter
        self.iteration += 1
        if self.iteration > 1:
            logging.info(f"Sitemap iteration {self.iteration}: Processing {len(to_process)} pages, {len(remaining)} remaining, {len(shared.get('pages_visited', set()))} visited")
                
        return to_process
        
    def exec(self, url):
        """Process a single URL to build sitemap."""
        soup, status, error = get_website_content(url)
        if error or not soup:
            return {"url": url, "error": error or "Failed to fetch content", "links": []}
            
        # Extract page structure
        page_structure = {
            "title": soup.title.string if soup.title else "No title",
            "headers": {
                "h1": [h.text.strip() for h in soup.find_all('h1')],
                "h2": [h.text.strip() for h in soup.find_all('h2')],
                "h3": [h.text.strip() for h in soup.find_all('h3')],
            },
            "paragraphs_count": len(soup.find_all('p')),
            "links": [],
            "soup": soup  # Store soup for later use
        }
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            
            # Only add internal links
            if is_valid_url(absolute_url, urlparse(url).netloc):
                links.append(absolute_url)
                page_structure["links"].append(absolute_url)
                
        return {"url": url, "structure": page_structure, "links": links}
        
    def post(self, shared, prep_res, exec_res_list):
        """Update sitemap with processed URLs and discover new ones."""
        # Handle case where we received no valid results
        if not exec_res_list or all("error" in result for result in exec_res_list):
            shared["error_message"] = "Failed to build sitemap - all requests failed"
            shared["error_source"] = "sitemap_batch"
            shared["succeeded"] = False
            return "error"
            
        sitemap = shared["sitemap"]
        max_pages = shared.get("max_pages", 20)
        
        # Initialize if not already
        if "pages_visited" not in shared:
            shared["pages_visited"] = set()
            
        # Add processed URLs to sitemap
        for result in exec_res_list:
            url = result["url"]
            shared["pages_visited"].add(url)
            
            if "error" not in result:
                # Add to sitemap
                page_key = url.replace(sitemap["base_url"], "") or "/"
                sitemap["pages"][page_key] = result["structure"]
                
                # Add soup to shared store for later use
                if "soups" not in shared:
                    shared["soups"] = {}
                shared["soups"][url] = result["structure"].pop("soup", None)
                
                # Discover new URLs to process
                for link in result["links"]:
                    if (link not in shared["pages_visited"] and 
                        link not in shared["pages_to_process"]):
                        shared["pages_to_process"].append(link)
        
        # Update shared store
        shared["sitemap"] = sitemap
        shared["visited_urls"] = list(shared["pages_visited"])  # For backward compatibility
        
        # Determine next action
        visited_count = len(shared["pages_visited"])
        to_process_count = len(shared["pages_to_process"])
        
        logging.info(f"Sitemap status: {visited_count} pages visited, {to_process_count} pages to process")
        
        # Check if we've hit our iteration limit
        if self.iteration >= self.max_iterations:
            logging.warning(f"Reached maximum iteration limit ({self.max_iterations})")
            return "next"
        
        # Check if we have more pages to process and haven't reached max pages yet
        if to_process_count > 0 and visited_count < max_pages:
            return "continue"
        else:
            # Finished sitemap construction
            logging.info(f"Sitemap construction complete with {len(sitemap['pages'])} pages")
            return "next"

class DesignElementsBatchNode(BatchNode):
    def prep(self, shared):
        """Prepare pages for design elements extraction."""
        sitemap = shared.get("sitemap", {})
        pages = []
        
        for page_key, page_info in sitemap.get("pages", {}).items():
            url = shared["sitemap"]["base_url"]
            if page_key != "/":
                url = urljoin(url, page_key)
                
            # Check if we have the soup already
            if "soups" in shared and url in shared["soups"]:
                pages.append((url, page_key, shared["soups"][url]))
            else:
                pages.append((url, page_key, None))
                
        return pages
        
    def exec(self, page_data):
        """Extract design elements from a page."""
        url, page_key, soup = page_data
        
        # If soup wasn't provided, fetch it
        if not soup:
            soup, status, error = get_website_content(url)
            if error or not soup:
                return {"page_key": page_key, "error": error or "Failed to fetch content"}
                
        # Extract design elements
        design_data = extract_design_elements(soup, url)
        return {"page_key": page_key, "design": design_data}
        
    def post(self, shared, prep_res, exec_res_list):
        """Combine design elements from all pages."""
        if "design" not in shared:
            shared["design"] = {
                "colors": {},
                "fonts": [],
                "layout": {
                    "sections": 0,
                    "columns": False,
                    "responsive": False
                },
                "images": {
                    "count": 0,
                    "types": {}
                },
                "pages_data": {}
            }
            
        # Aggregate data across pages
        for result in exec_res_list:
            if "error" not in result:
                page_key = result["page_key"]
                design = result["design"]
                
                # Store per-page data
                shared["design"]["pages_data"][page_key] = design
                
                # Aggregate colors
                for color, count in design.get("colors", {}).items():
                    if color in shared["design"]["colors"]:
                        shared["design"]["colors"][color] += count
                    else:
                        shared["design"]["colors"][color] = count
                
                # Aggregate fonts
                for font in design.get("fonts", []):
                    if font not in shared["design"]["fonts"]:
                        shared["design"]["fonts"].append(font)
                
                # Aggregate layout info
                if design.get("layout", {}).get("responsive", False):
                    shared["design"]["layout"]["responsive"] = True
                if design.get("layout", {}).get("columns", False):
                    shared["design"]["layout"]["columns"] = True
                shared["design"]["layout"]["sections"] += design.get("layout", {}).get("sections", 0)
                
                # Aggregate image info
                shared["design"]["images"]["count"] += design.get("images", {}).get("count", 0)
                for img_type, count in design.get("images", {}).get("types", {}).items():
                    if img_type in shared["design"]["images"]["types"]:
                        shared["design"]["images"]["types"][img_type] += count
                    else:
                        shared["design"]["images"]["types"][img_type] = count
        
        # Sort colors by frequency
        shared["design"]["colors"] = dict(
            sorted(shared["design"]["colors"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return "next"

class ContentBatchNode(BatchNode):
    def prep(self, shared):
        """Prepare pages for content extraction."""
        sitemap = shared.get("sitemap", {})
        pages = []
        
        for page_key, page_info in sitemap.get("pages", {}).items():
            url = shared["sitemap"]["base_url"]
            if page_key != "/":
                url = urljoin(url, page_key)
                
            # Check if we have the soup already
            if "soups" in shared and url in shared["soups"]:
                pages.append((url, page_key, shared["soups"][url]))
            else:
                pages.append((url, page_key, None))
                
        return pages
        
    def exec(self, page_data):
        """Extract content from a page."""
        url, page_key, soup = page_data
        
        # If soup wasn't provided, fetch it
        if not soup:
            soup, status, error = get_website_content(url)
            if error or not soup:
                return {"page_key": page_key, "error": error or "Failed to fetch content"}
                
        # Extract content
        content_data = extract_content(soup, url)
        return {"page_key": page_key, "content": content_data}
        
    def post(self, shared, prep_res, exec_res_list):
        """Combine content from all pages."""
        if "content" not in shared:
            shared["content"] = {
                "page_title": "",
                "main_content": {
                    "header": [],
                    "main": [],
                    "footer": []
                },
                "business_info": {},
                "business_type": {
                    "type": None,
                    "confidence": 0
                },
                "word_count": 0,
                "pages_data": {}
            }
            
        # Prioritize home page for main content
        home_page_content = None
        for result in exec_res_list:
            if "error" not in result:
                page_key = result["page_key"]
                if page_key == "/" or page_key == "":
                    home_page_content = result["content"]
                    break
        
        # If home page was found, use it for main business info
        if home_page_content:
            shared["content"]["page_title"] = home_page_content.get("page_title", "")
            shared["content"]["main_content"] = home_page_content.get("main_content", {})
            shared["content"]["business_info"] = home_page_content.get("business_info", {})
            shared["content"]["business_type"] = home_page_content.get("business_type", {})
        
        # Aggregate data across pages
        total_word_count = 0
        business_types = {}
        
        for result in exec_res_list:
            if "error" not in result:
                page_key = result["page_key"]
                content = result["content"]
                
                # Store per-page data
                shared["content"]["pages_data"][page_key] = content
                
                # Aggregate word count
                total_word_count += content.get("word_count", 0)
                
                # Track business types
                business_type = content.get("business_type", {}).get("type")
                confidence = content.get("business_type", {}).get("confidence", 0)
                if business_type:
                    if business_type in business_types:
                        business_types[business_type]["count"] += 1
                        business_types[business_type]["confidence"] += confidence
                    else:
                        business_types[business_type] = {"count": 1, "confidence": confidence}
        
        # Add total word count
        shared["content"]["word_count"] = total_word_count
        
        # Find best business type
        if business_types:
            best_type = max(business_types.items(), key=lambda x: (x[1]["count"], x[1]["confidence"]))
            shared["content"]["business_type"] = {
                "type": best_type[0],
                "confidence": round(best_type[1]["confidence"] / best_type[1]["count"])
            }
        
        logging.info(f"Total word count: {shared['content']['word_count']}")
        
        return "next"

# Reduce phase nodes
class CombineResultsNode(Node):
    def exec(self, prep_res):
        """Combine results from all nodes."""
        return True
        
    def post(self, shared, prep_res, exec_res):
        """Store combined results."""
        return "next"

class GenerateSpecsNode(Node):
    def prep(self, shared):
        """
        Prepare data for specification generation.
        
        Returns:
            dict: Data needed for spec generation
        """
        return {
            "url": shared.get("url", ""),
            "content_data": shared.get("content_data", {}),
            "design_data": shared.get("design", {}),
            "sitemap_data": shared.get("sitemap", {}),
            "output_dir": shared.get("output_dir", "output")
        }
    
    def exec(self, prep_data):
        """
        Generate business and brand specifications.
        
        Args:
            prep_data (dict): Prepared data
            
        Returns:
            dict: Specification results
        """
        try:
            # Generate specifications
            business_spec, brand_spec = generate_specs(
                prep_data["content_data"],
                prep_data["design_data"],
                prep_data["sitemap_data"]
            )
            
            # Save specifications to file
            specs_file = save_specs(
                business_spec,
                brand_spec,
                prep_data["url"],
                prep_data["output_dir"]
            )
            
            return {
                "success": True,
                "business_spec": business_spec,
                "brand_spec": brand_spec,
                "specs_file": specs_file,
                "content_data": prep_data["content_data"]  # Include content_data in the response
            }
        except Exception as e:
            logging.error(f"Error generating specifications: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def post(self, shared, prep_res, exec_res):
        """
        Store specifications in shared context.
        
        Returns:
            str: Action to take
        """
        if exec_res.get("success", False):
            shared["business_spec"] = exec_res["business_spec"]
            shared["brand_spec"] = exec_res["brand_spec"]
            shared["specs_file"] = exec_res["specs_file"]
            shared["content_data"] = exec_res["content_data"]  # Ensure content_data is stored in shared
            logging.info(f"Specifications saved to {exec_res['specs_file']}")
            return "next"
        else:
            logging.error(f"Failed to generate specifications: {exec_res.get('error', 'Unknown error')}")
            return "error"

class CreateHtmlSummaryNode(Node):
    def prep(self, shared):
        """
        Prepare data for HTML summary generation.
        
        Returns:
            dict: Data needed for HTML generation
        """
        return {
            "url": shared.get("url", "Unknown URL"),
            "business_spec": shared.get("business_spec", {}),
            "brand_spec": shared.get("brand_spec", {}),
            "sitemap_data": shared.get("sitemap_data", shared.get("sitemap", {})),
            "design_data": shared.get("design_data", shared.get("design", {})),
            "output_dir": shared.get("output_dir", "output"),
            "content_data": shared.get("content_data", {})
        }
    
    def exec(self, prep_data):
        """
        Generate HTML summary.
        
        Args:
            prep_data (dict): Prepared data
        
        Returns:
            dict: Summary and file path
        """
        try:
            html = generate_html_summary(
                prep_data["url"],
                prep_data["business_spec"],
                prep_data["brand_spec"],
                prep_data["sitemap_data"],
                prep_data["design_data"],
                prep_data["content_data"]
            )
            
            output_path = save_html_summary(html, prep_data["url"], prep_data["output_dir"])
            
            return {
                "success": True,
                "html_summary": html,
                "output_path": output_path
            }
        except Exception as e:
            logging.error(f"Error generating HTML summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def post(self, shared, prep_res, exec_res):
        """
        Store summary results in shared context.
        
        Returns:
            str: Action to take
        """
        if exec_res.get("success", False):
            shared["html_summary"] = exec_res.get("html_summary", "")
            shared["html_output_path"] = exec_res.get("output_path", "")
            logging.info(f"HTML summary saved to {exec_res.get('output_path')}")
            return "next"
        else:
            logging.error(f"Failed to generate HTML summary: {exec_res.get('error', 'Unknown error')}")
            return "error"

class ExtractContentNode(Node):
    def prep(self, shared):
        """
        Prepare data for content extraction.
        
        Returns:
            dict: Data needed for extraction
        """
        return {
            "url": shared.get("url", ""),
            "soup": shared.get("soup", None),
            "status": shared.get("status", None)
        }
    
    def exec(self, prep_data):
        """
        Extract content from the webpage.
        
        Args:
            prep_data (dict): Prepared data
            
        Returns:
            dict: Extraction results
        """
        if not prep_data["soup"]:
            logging.error("No soup object provided to extract content")
            return {
                "success": False,
                "error": "No soup object provided",
                "content_data": {}
            }
        
        try:
            content_data = extract_content(prep_data["soup"], prep_data["url"])
            
            return {
                "success": True,
                "content_data": content_data
            }
        except Exception as e:
            logging.error(f"Error extracting content: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content_data": {}
            }
    
    def post(self, shared, prep_res, exec_res):
        """
        Store extracted content in shared context.
        
        Returns:
            str: Action to take
        """
        if exec_res.get("success", False):
            shared["content_data"] = exec_res["content_data"]  # Use content_data key consistently
            logging.info("Content extraction completed successfully")
            return "next"
        else:
            logging.error(f"Content extraction failed: {exec_res.get('error', 'Unknown error')}")
            return "error"