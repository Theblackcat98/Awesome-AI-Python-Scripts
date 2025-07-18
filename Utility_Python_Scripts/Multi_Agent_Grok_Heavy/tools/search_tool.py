from typing import Any, Dict, List, Optional
import requests
from requests.exceptions import RequestException, Timeout
from bs4 import BeautifulSoup
from ddgs import DDGS # Assuming 'ddgs' library is installed (pip install duckduckgo_search)

from .base_tool import BaseTool # Relative import

# --- Default Configuration Constants ---
# These can be overridden via the 'config' dictionary when initializing the tool
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
DEFAULT_REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_CONTENT_SNIPPET_LENGTH = 1500 # Number of characters for the extracted page content

class SearchTool(BaseTool):
    """
    A tool for performing web searches using DuckDuckGo and extracting content
    from search results.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config) # Call the base class constructor

        # Initialize DuckDuckGo Search client
        # DDGS can take proxies, headers, etc., which could also be passed via config
        self.ddgs = DDGS()

        # Configure request parameters from the tool's config or use defaults
        self.user_agent = self.config.get('user_agent', DEFAULT_USER_AGENT)
        self.request_timeout = self.config.get('request_timeout', DEFAULT_REQUEST_TIMEOUT_SECONDS)
        self.content_snippet_length = self.config.get('content_snippet_length', DEFAULT_CONTENT_SNIPPET_LENGTH)

    @property
    def name(self) -> str:
        return "search_web"

    @property
    def description(self) -> str:
        return (
            "Search the web using DuckDuckGo for current information. "
            "Provides a list of relevant results, each including the title, URL, a brief snippet from the search engine, "
            "and an extracted content snippet from the linked page if successfully fetched. "
            "Use this tool when you need up-to-date information that is not available in the model's training data, "
            "or when a more detailed context from the actual webpage is required."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The concise and specific search query to find information on the web. Avoid conversational language.",
                    "examples": ["latest news on AI breakthroughs", "weather in London tomorrow", "history of quantum mechanics"]
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of top search results to return. A smaller number (e.g., 3-5) is usually sufficient. Do not set too high to avoid excessive processing and API calls.",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10 # Set a sensible upper limit for performance and cost
                }
            },
            "required": ["query"]
        }

    def _fetch_and_parse_url(self, url: str) -> str:
        """
        Helper method to fetch content from a URL and extract clean text.
        Raises requests.RequestException or other exceptions on failure.
        """
        headers = {'User-Agent': self.user_agent}
        response = requests.get(url, headers=headers, timeout=self.request_timeout)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script, style, and potentially other irrelevant elements
        for unwanted_tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
            unwanted_tag.decompose()

        # Get text content
        text = soup.get_text()
        # Clean up excessive whitespace (multiple newlines, tabs, spaces)
        text = ' '.join(text.split()).strip()

        # Limit content length
        if len(text) > self.content_snippet_length:
            text = text[:self.content_snippet_length] + "..."
        return text

    def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Searches the web using DuckDuckGo and attempts to fetch and parse
        the content of the top results.

        Args:
            query: The search query string.
            max_results: The maximum number of search results to retrieve and process.

        Returns:
            A dictionary containing a 'success' status, and either 'results' (list of dicts)
            or an 'error' message. Each result dict includes 'title', 'url', 'snippet',
            and 'full_content' (which may indicate failure to fetch).
        """
        if not query:
            return {"success": False, "error": "Search query cannot be empty."}
        if not isinstance(max_results, int) or max_results <= 0:
            return {"success": False, "error": "max_results must be a positive integer."}
        # Enforce the maximum specified in parameters to prevent abuse
        if max_results > self.parameters['properties']['max_results']['maximum']:
            return {"success": False, "error": f"max_results cannot exceed {self.parameters['properties']['max_results']['maximum']}."}

        try:
            # Perform the DuckDuckGo search
            # ddgs.text returns a generator, convert to list to iterate multiple times if needed
            # or just iterate directly. For simplicity, we convert to list here.
            search_results = list(self.ddgs.text(keywords=query, max_results=max_results))

            if not search_results:
                return {"success": True, "results": [], "message": "No search results found for the query."}

            processed_results: List[Dict[str, Any]] = []

            for result in search_results:
                item = {
                    "title": result.get('title', 'No Title'),
                    "url": result.get('href', ''),
                    "snippet": result.get('body', 'No snippet available.'), # DuckDuckGo's own snippet
                    "full_content": "Could not fetch content." # Default placeholder
                }

                # Only attempt to fetch if URL is present and looks valid
                if item["url"] and item["url"].startswith("http"):
                    try:
                        item["full_content"] = self._fetch_and_parse_url(item["url"])
                    except Timeout:
                        item["full_content"] = "Could not fetch content: Request timed out."
                    except RequestException as req_e:
                        # Catch broader requests errors (connection, HTTP errors etc.)
                        item["full_content"] = f"Could not fetch content: Network or HTTP error ({type(req_e).__name__}: {req_e})."
                    except Exception as e:
                        # Catch any other parsing errors (e.g., BeautifulSoup issues)
                        item["full_content"] = f"Could not parse content: An unexpected error occurred ({type(e).__name__}: {str(e)})."
                else:
                    item["full_content"] = "Invalid or missing URL for content fetch."

                processed_results.append(item)

            return {
                "success": True,
                "results": processed_results
            }

        except Exception as e:
            # Catch any errors during the initial DDGS search itself
            return {
                "success": False,
                "error": f"An error occurred during the web search initiation: {type(e).__name__}: {str(e)}"
            }