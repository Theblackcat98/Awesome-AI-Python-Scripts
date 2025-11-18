# Tools

Tools are Python functions that the LLM can call to access external data or execute specific actions. They serve as "superpowers" for LLMs, enabling capabilities like web search, image generation, and API integrations.

## Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Must be named `Tools`
- **Valves Configuration**: User-configurable parameters defined in a nested Pydantic class named `Valves`
- **Initialization**: The `__init__` method must instantiate the `Valves`
- **Tool Methods**: Any public method in the `Tools` class is exposed as a callable tool

## Context Arguments
Tools can access special optional parameters:
- `__user__`: Dict containing user information and valve settings (`__user__["valves"]`)
- `__event_emitter__`: Function for status updates and progress tracking
- `__event_call__`: Function for user interaction (confirmations, input collection)

## Function Calling Modes

### Default Mode
In default mode, tools are called with structured data and return results directly to the LLM.

### Native Mode  
In native mode, tools are called with additional context and can provide richer interactions through event emitters and user communication.

## Complete Example

```python
"""
title: 'Web Search Tool'
description: 'Search the web for information and return structured results.'
author: 'OpenWebUI Team'
version: '1.0.0'
requirements: ['requests', 'beautifulsoup4']
"""

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class Tools:
    class Valves(BaseModel):
        search_engine: str = Field(
            default="duckduckgo",
            description="Search engine to use",
            json_schema_extra={
                "ui": {
                    "component": "select",
                    "options": [
                        {"value": "duckduckgo", "label": "DuckDuckGo"},
                        {"value": "bing", "label": "Bing"}
                    ]
                }
            }
        )
        max_results: int = Field(default=5, description="Maximum results to return")
        timeout_seconds: int = Field(default=10, description="Request timeout")

    def __init__(self):
        self.valves = self.Valves()

    async def web_search(
        self, 
        query: str, 
        __event_emitter__=None,
        __event_call__=None,
        __user__=None
    ) -> Dict[str, Any]:
        """
        Search the web for the given query.
        :param query: The search query
        :param __event_emitter__: Event emitter for status updates
        :param __event_call__: Event call for user interactions
        :param __user__: User context and valve settings
        :return: Search results with titles, URLs, and snippets
        """
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"Searching for '{query}'...", "done": False}
            })

        # Check if user wants to proceed (native mode interaction)
        if __event_call__ and query.lower().contains("sensitive"):
            await __event_call__(
                type="ask_confirm",
                message="Search sensitive content?",
                detail="This search may return sensitive information. Continue?"
            )

        try:
            # Simulate search API call
            results = [
                {
                    "title": f"Result for '{query}' - Page 1",
                    "url": "https://example.com/page1",
                    "snippet": f"Information about {query} from page 1..."
                },
                {
                    "title": f"Result for '{query}' - Page 2", 
                    "url": "https://example.com/page2",
                    "snippet": f"More information about {query} from page 2..."
                }
            ]
            
            # Limit results based on valve setting
            results = results[:self.valves.max_results]
            
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": f"Found {len(results)} results", "done": True}
                })
                
                # Send citations for research tools
                await __event_emitter__({
                    "type": "citation",
                    "data": {
                        "content": f"Search results for '{query}'",
                        "source_url": "https://example.com",
                        "source_name": "Web Search Tool",
                        "metadata": {"query": query, "results_count": len(results)}
                    }
                })
            
            return {
                "results": results, 
                "query": query,
                "total_results": len(results)
            }

        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": error_msg, "done": True, "is_error": True}
                })
            return {"error": error_msg}

    async def get_weather(
        self,
        location: str,
        __event_emitter__=None,
        __user__=None
    ) -> Dict[str, Any]:
        """
        Get current weather for a location.
        """
        if not location:
            return {"error": "Location is required"}
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"Fetching weather for {location}...", "done": False}
            })

        # Simulate weather API call
        weather_data = {
            "location": location,
            "temperature": 22,
            "unit": "celsius",
            "condition": "Sunny",
            "humidity": 65
        }
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "Weather data retrieved!", "done": True}
            })
        
        return weather_data

    def reverse_string(self, text: str) -> str:
        """
        Simple tool that reverses input strings.
        :param text: The string to reverse
        :return: The reversed string
        """
        return text[::-1]
```

## Advanced Example

```python
async def process_document(
    self, 
    document_url: str,
    __event_emitter__=None,
    __event_call__=None,
    __user__=None,
    __messages__=None
) -> Dict[str, Any]:
    """
    Process a document with native mode capabilities.
    """
    # Get user confirmation before processing
    if __event_call__:
        await __event_call__(
            type="ask_confirm",
            message=f"Process document: {document_url}?",
            detail="This will download and analyze the document"
        )
    
    # Send progress updates
    if __event_emitter__:
        await __event_emitter__({
            "type": "status", 
            "data": {"description": "Downloading document...", "progress": 20}
        })
    
    # Process document...
    
    return {"status": "processed", "summary": "Document analysis complete"}
```

## Key Concepts

1. **Function Compatibility**: Design tools to work in both default and native modes
2. **Event Emitters**: Use `__event_emitter__` for progress updates and user notifications
3. **User Interaction**: Leverage `__event_call__` for confirmations and input collection
4. **Error Handling**: Implement comprehensive error handling with user-friendly messages
5. **Context Awareness**: Access `__user__` and `__messages__` when needed for context-aware operations

## Best Practices

1. **Error Handling**: Implement comprehensive error handling with user-friendly messages
2. **Progress Feedback**: Use `__event_emitter__` for long-running operations
3. **User Interaction**: Leverage `__event_call__` for confirmation dialogs and user input
4. **Context Awareness**: Access `__user__` and `__messages__` when needed for context-aware operations
5. **Thread Safety**: Consider thread safety for concurrent operations

## Related Documentation
- [Tools Development](https://docs.openwebui.com/features/plugin/tools/development/)
- [Function Calling Documentation](https://docs.openwebui.com/features/plugin/functions/)
- [Event Emitters Guide](https://docs.openwebui.com/features/plugin/functions/)