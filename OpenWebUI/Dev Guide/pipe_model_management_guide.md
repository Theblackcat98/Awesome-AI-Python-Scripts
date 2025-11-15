# Using OpenWebUI's Built-in Model Management in Pipe Functions

When developing Pipe functions, it's recommended to use OpenWebUI's built-in model management system instead of making direct API calls. This provides several benefits:

1. **Automatic Authentication**: Uses the user's existing model configurations
2. **Simplified Deployment**: No need to manage API keys or endpoints
3. **Better Integration**: Works seamlessly with OpenWebUI's model selection UI

## Implementation Guide

### 1. Required Imports

```python
from open_webui.main import generate_chat_completions
from open_webui.models.users import User
from typing import Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, Field
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### 2. Basic Pipe Structure

```python
class MyPipe:
    class Valves(BaseModel):
        ENABLED: bool = Field(
            default=True,
            description="Enable or disable this pipe"
        )
        MODEL_NAME: str = Field(
            default="gpt-3.5-turbo",
            description="Default model to use"
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()
        self.__user__ = None
        self.__request__ = None
        self.__event_emitter__ = None

    def pipes(self) -> list[dict]:
        return [{
            "id": "my-custom-pipe",
            "name": "My Custom Pipe"
        }]
```

### 3. Handling the Pipe Method

```python
async def pipe(
    self,
    body: dict,
    __user__: dict,
    __event_emitter__: Optional[Callable[[dict], Awaitable[None]]],
    __request__: Any,
    **kwargs
) -> Any:
    """
    Process incoming chat requests using OpenWebUI's model management.
    
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
    
    # Get model from request or use default
    model = body.get("model") or self.valves.MODEL_NAME
    messages = body.get("messages", [])
    
    try:
        # Generate response using OpenWebUI's model management
        response = await self._generate_completion(
            model=model,
            messages=messages,
            temperature=0.7
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in pipe: {str(e)}", exc_info=True)
        return f"An error occurred: {str(e)}"
```

### 4. Generating Completions

```python
async def _generate_completion(
    self, 
    model: str, 
    messages: list[dict], 
    temperature: float = 0.7,
    stream: bool = False
) -> Any:
    """
    Generate a completion using OpenWebUI's model management.
    
    Args:
        model: The model to use for generation
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Sampling temperature (0.0 to 2.0)
        stream: Whether to stream the response
        
    Returns:
        The generated text or a streaming generator
    """
    if not self.__request__:
        raise ValueError("Request context not initialized")
    
    form_data = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "temperature": min(max(0.0, temperature), 2.0),
    }
    
    try:
        # For non-streaming responses
        if not stream:
            response_data = await generate_chat_completions(
                self.__request__,
                form_data,
                user=self.__user__,
            )
            return response_data["choices"][0]["message"]["content"]
            
        # For streaming responses
        else:
            async def generate():
                async for chunk in generate_chat_completions(
                    self.__request__,
                    form_data,
                    user=self.__user__,
                ):
                    yield chunk
            return generate()
            
    except Exception as e:
        logger.error(f"Error in _generate_completion: {str(e)}", exc_info=True)
        raise
```

## Best Practices

1. **Error Handling**
   - Always wrap API calls in try/except blocks
   - Provide meaningful error messages
   - Log detailed error information for debugging

2. **Resource Management**
   - Close any resources in a `finally` block
   - Use context managers when possible
   - Handle timeouts appropriately

3. **Performance**
   - Cache frequently used resources
   - Use streaming for long responses
   - Implement rate limiting if needed

4. **Security**
   - Never hardcode API keys
   - Validate all inputs
   - Sanitize outputs to prevent XSS attacks

## Example: Complete Pipe Implementation

```python
"""
title: Smart Response Generator
description: Generates responses using OpenWebUI's model management
author: Your Name
version: 1.0.0
"""

from typing import Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, Field
from open_webui.main import generate_chat_completions
from open_webui.models.users import User
import logging

logger = logging.getLogger(__name__)

class SmartResponsePipe:
    class Valves(BaseModel):
        ENABLED: bool = Field(
            default=True,
            description="Enable or disable this pipe"
        )
        DEFAULT_MODEL: str = Field(
            default="gpt-3.5-turbo",
            description="Default model to use for generation"
        )
        MAX_TOKENS: int = Field(
            default=2000,
            description="Maximum number of tokens to generate"
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()
        self.__user__ = None
        self.__request__ = None
        self.__event_emitter__ = None

    def pipes(self) -> list[dict]:
        return [{
            "id": "smart-response-pipe",
            "name": "Smart Response Generator"
        }]

    async def _generate_completion(
        self, 
        model: str, 
        messages: list[dict], 
        temperature: float = 0.7
    ) -> str:
        """Generate a completion using OpenWebUI's model management."""
        try:
            form_data = {
                "model": model,
                "messages": messages,
                "stream": False,
                "temperature": min(max(0.0, temperature), 2.0),
                "max_tokens": self.valves.MAX_TOKENS
            }

            response_data = await generate_chat_completions(
                self.__request__,
                form_data,
                user=self.__user__,
            )
            return response_data["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}", exc_info=True)
            raise

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]],
        __request__: Any,
        **kwargs
    ) -> str:
        try:
            # Store context
            self.__user__ = User(**__user__) if __user__ else None
            self.__request__ = __request__
            self.__event_emitter__ = __event_emitter__
            
            # Get model and messages
            model = body.get("model") or self.valves.DEFAULT_MODEL
            messages = body.get("messages", [])
            
            if not messages:
                return "No messages provided"
                
            # Generate response
            response = await self._generate_completion(
                model=model,
                messages=messages,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Error in SmartResponsePipe: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"An error occurred: {error_msg}"
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify the model service is running
   - Check network connectivity
   - Ensure the model name is correct

2. **Authentication Failures**
   - Verify API keys are properly configured
   - Check user permissions
   - Ensure the model is accessible to the user

3. **Performance Issues**
   - Reduce max tokens for faster responses
   - Enable streaming for long responses
   - Check for rate limiting

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Inspect Request/Response**
   ```python
   logger.debug(f"Request: {form_data}")
   logger.debug(f"Response: {response_data}")
   ```

3. **Check Model Availability**
   ```python
   from open_webui.models import get_model_list
   available_models = await get_model_list()
   logger.debug(f"Available models: {available_models}")
   ```

## Best Practices Summary

1. Always use `generate_chat_completions` for model interactions
2. Store request context in instance variables
3. Implement comprehensive error handling
4. Use proper logging for debugging
5. Follow security best practices
6. Document your code thoroughly
7. Test with different model configurations
8. Handle streaming responses efficiently
9. Implement proper cleanup in error cases
## 7. Citation Handling in Pipes

Proper citation handling is crucial for maintaining transparency and giving credit to sources. Here's how to implement citations in your Pipe functions:

### Basic Citation Structure

```python
# In your pipe method
async def pipe(self, body: dict, __user__, __event_emitter__, __request__, **kwargs):
    # ... your code ...
    
    # When you have content to cite
    citation_data = {
        "type": "citation",
        "data": {
            "document": ["Content to be cited"],
            "metadata": [{"source": "https://example.com/source"}],
            "source": {"name": "Source Name"}
        }
    }
    
    await __event_emitter__(citation_data)
```

### Complete Example with Error Handling

```python
async def emit_citation(
    event_emitter: Callable[[dict], Awaitable[None]],
    content: str,
    source_url: str,
    source_name: str,
    metadata: Optional[dict] = None
) -> None:
    """Helper function to emit citation events with proper formatting.
    
    Args:
        event_emitter: The event emitter function
        content: The content being cited
        source_url: URL of the source
        source_name: Name of the source
        metadata: Additional metadata (optional)
    """
    if not event_emitter:
        return
        
    try:
        citation = {
            "type": "citation",
            "data": {
                "document": [content],
                "metadata": [{"source": source_url, **(metadata or {})}],
                "source": {"name": source_name}
            }
        }
        await event_emitter(citation)
    except Exception as e:
        logger.error(f"Failed to emit citation: {str(e)}")
```

### Best Practices for Citations

1. **Source Attribution**
   - Always include the original source URL
   - Provide a clear, human-readable source name
   - Include publication date if available

2. **Content Formatting**
   - Keep citations concise but meaningful
   - Preserve original context and meaning
   - Use markdown for formatting when appropriate

3. **Metadata**
   - Include relevant metadata like author, publication date, and license
   - Add timestamps for time-sensitive information
   - Include content type (article, video, research paper, etc.)

4. **Error Handling**
   - Always wrap citation emission in try/except blocks
   - Log errors but don't fail the entire operation if citation fails
   - Provide fallback behavior when citation data is incomplete

5. **Performance**
   - Batch multiple citations when possible
   - Avoid including large content directly in citations
   - Consider using content hashes for deduplication

### Example Usage in a Pipe

```python
class ResearchPipe:
    # ... other pipe code ...
    
    async def pipe(self, body: dict, __user__, __event_emitter__, __request__, **kwargs):
        # ... your research logic ...
        
        # When you find content to cite
        await emit_citation(
            event_emitter=__event_emitter__,
            content=research_summary,
            source_url="https://example.com/research-paper",
            source_name="Example Research Paper",
            metadata={
                "author": "Jane Doe",
                "publication_date": "2023-01-15",
                "license": "CC BY 4.0"
            }
        )
        
        return research_summary
```

10. Keep your code modular and maintainable
