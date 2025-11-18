# Pipes

Pipes are powerful components that can intercept and modify messages between the user and the LLM. They can be used for tasks like:
- Adding context to messages
- Modifying model responses
- Implementing custom model routing
- Adding authentication/authorization
- Managing model interactions

## Model Management with Pipes

When developing Pipe functions, it's recommended to use OpenWebUI's built-in model management system instead of making direct API calls. This provides several benefits:

1. **Automatic Authentication**: Uses the user's existing model configurations
2. **Simplified Deployment**: No need to manage API keys or endpoints
3. **Better Integration**: Works seamlessly with OpenWebUI's model selection UI

## Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Must be named `Pipe`
- **Valves Configuration**: User-configurable parameters defined in a nested Pydantic class named `Valves`
- **Initialization**: The `__init__` method must instantiate the `Valves`
- **Pipe Method**: `async def pipe()` - main processing entry point
- **Pipes Method**: `def pipes()` - returns list of available pipes

## Complete Example

```python
"""
title: 'Research Assistant Pipe'
description: 'Enhances messages with research context and handles citations.'
author: 'OpenWebUI Team'
version: '1.0.0'
requirements: ['requests', 'pydantic']
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Callable, Awaitable
from open_webui.main import generate_chat_completions
from open_webui.models.users import User
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Pipe:
    class Valves(BaseModel):
        ENABLED: bool = Field(
            default=True,
            description="Enable or disable this pipe"
        )
        MODEL_NAME: str = Field(
            default="gpt-3.5-turbo",
            description="Default model to use"
        )
        ADD_CITATIONS: bool = Field(
            default=True,
            description="Automatically add citations to responses"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.type = "pipe"
        self.__user__ = None
        self.__request__ = None
        self.__event_emitter__ = None
        
    def pipes(self) -> list[dict]:
        return [{
            "id": "research-assistant-pipe",
            "name": "Research Assistant"
        }]

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]],
        __request__: Any,
        **kwargs
    ) -> Any:
        """
        Process incoming chat requests with research capabilities.
        
        Args:
            body: The request body containing messages and model info
            __user__: User information and permissions
            __event_emitter__: For sending status updates to the UI
            __request__: The original request object
            
        Returns:
            The generated response or a streaming generator
        """
        # Store context for use in other methods
        self.__user__ = User(**__user__) if __user__ else None
        self.__request__ = __request__
        self.__event_emitter__ = __event_emitter__
        
        try:
            # Add research context if needed
            if self._needs_research(body):
                body = await self._add_research_context(body)
                
            # Generate response using OpenWebUI's model management
            response = await self._generate_completion(
                body=body,
                model=body.get("model") or self.valves.MODEL_NAME,
                temperature=0.7
            )
            
            # Add citations if enabled
            if self.valves.ADD_CITATIONS:
                response = await self._add_citations(response)
                
            return response
            
        except Exception as e:
            logger.error(f"Error in research pipe: {str(e)}", exc_info=True)
            if self.__event_emitter__:
                await self.__event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"Error: {str(e)}",
                        "done": True,
                        "is_error": True
                    }
                })
            raise

    async def _generate_completion(self, body: dict, model: str, **kwargs) -> Any:
        """Generate a completion using OpenWebUI's model management."""
        # Forward the request to OpenWebUI's model management
        response = await generate_chat_completion(
            request=self.__request__,
            body=body,
            user=self.__user__,
            **kwargs
        )
        return response
        
    def _needs_research(self, body: dict) -> bool:
        """Determine if the message requires research."""
        messages = body.get("messages", [])
        if not messages:
            return False
        
        # Check if the last message suggests research is needed
        last_message = messages[-1].get("content", "").lower()
        research_keywords = ["research", "find", "latest", "update", "current", "recent", "news"]
        return any(keyword in last_message for keyword in research_keywords)
        
    async def _add_research_context(self, body: dict) -> dict:
        """Add research context to the message."""
        if not self.__event_emitter__:
            return body
            
        await self.__event_emitter__({
            "type": "status",
            "data": {
                "description": "🔍 Researching...",
                "done": False
            }
        })
        
        # Simulate research - in a real implementation, this would call external APIs
        research_results = [
            {
                "title": "Latest Research on Topic",
                "url": "https://example.com/research-paper",
                "summary": "Recent studies show significant advancements in this field..."
            }
        ]
        
        # Add research context to the message
        research_context = "\n\nResearch Context:\n"
        research_context += "\n".join(f"- {r['title']}: {r['summary']}" for r in research_results)
        
        if "messages" in body and body["messages"]:
            body["messages"][-1]["content"] += research_context
            
        return body
        
    async def _add_citations(self, response: Any) -> Any:
        """Add citations to the response."""
        if isinstance(response, dict):
            # Handle non-streaming response
            if "content" in response:
                response["content"] += "\n\n[1] Example Research Paper (2023)"
        elif hasattr(response, "__aiter__"):
            # Handle streaming response
            async for chunk in response:
                yield chunk
            # Add citation after streaming complete
            if self.__event_emitter__:
                await self.__event_emitter__({
                    "type": "citation",
                    "data": {
                        "content": "Example Research Paper (2023)",
                        "source_url": "https://example.com/research-paper",
                        "source_name": "Example Research Paper",
                        "metadata": {
                            "author": "Jane Doe",
                            "publication_date": "2023-01-15",
                            "license": "CC BY 4.0"
                        }
                    }
                })
        return response
```

## Key Concepts

1. **Model Integration**: Use `generate_chat_completion` for seamless model management
2. **Context Preservation**: Store `__user__`, `__request__`, and `__event_emitter__` for later use
3. **Streaming Support**: Handle both streaming and non-streaming responses appropriately
4. **Error Handling**: Implement comprehensive error handling with user feedback
5. **Event Emitters**: Use `__event_emitter__` for status updates and notifications

## Related Documentation
- [Pipe Functions](https://docs.openwebui.com/features/plugin/functions/pipe/)
- [Model Management](https://docs.openwebui.com/features/open_webui/pipelines/)
- [Authentication Middleware](https://docs.openwebui.com/features/plugin/functions/)
- [OpenAI API Integration](https://docs.openwebui.com/features/plugin/functions/pipe/)