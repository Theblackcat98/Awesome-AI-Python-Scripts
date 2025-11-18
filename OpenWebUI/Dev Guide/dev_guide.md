
# OpenWebUI Functions Development Guide

This comprehensive guide provides the necessary context for developing OpenWebUI Functions, including Tools, Pipes, Filters, and Buttons. These components allow you to extend and customize OpenWebUI's functionality.

## Overview

OpenWebUI Functions are modular Python components that extend the platform's capabilities. They are built-in, fast, and highly customizable plugins written in pure Python that operate directly within the OpenWebUI environment.

### Key Citations
- [Functions Overview](https://docs.openwebui.com/features/plugin/functions/)  
- [Tools Development](https://docs.openwebui.com/features/plugin/tools/development/)  
- [Pipe Functions](https://docs.openwebui.com/features/plugin/functions/pipe/)  
- [Filter Functions](https://docs.openwebui.com/features/plugin/functions/filter/)  
- [Action Functions](https://docs.openwebui.com/features/plugin/functions/action/)  
- [Releases](https://github.com/open-webui/open-webui/releases)

## Table of Contents

1. [Tools](#1-tools)
2. [Pipes](#2-pipes)
3. [Filters](#3-filters)
4. [Buttons](#4-actions)
5. [Common Patterns](#5-common-patterns)
6. [Version Compatibility](#6-version-compatibility)

## 1. Tools

Tools are Python functions that the LLM can call to access external data or execute specific actions. They serve as "superpowers" for LLMs, enabling capabilities like web search, image generation, and API integrations.

### Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Must be named `Tools`
- **Valves Configuration**: User-configurable parameters defined in a nested Pydantic class named `Valves`
- **Initialization**: The `__init__` method must instantiate the `Valves`
- **Tool Methods**: Any public method in the `Tools` class is exposed as a callable tool

### Context Arguments
Tools can access special optional parameters:
- `__user__`: Dict containing user information and valve settings (`__user__["valves"]`)
- `__event_emitter__`: Async function for sending status updates to chat UI
- `__event_call__`: Async function for requesting user interaction (confirmation modals)
- `__messages__`: List of previous chat messages

### Example: Basic Tool Structure

```python
"""
title: 'String Reverser'
description: 'A simple tool that reverses input strings.'
author: 'OpenWebUI Team'
version: '1.0.0'
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class Tools:
    def __init__(self):
        self.valves = self.Valves()

    class Valves(BaseModel):
        enable_uppercase: bool = Field(
            default=False,
            description="Convert output to uppercase"
        )

    def reverse_string(self, text: str) -> str:
        """
        Reverses the input string.
        :param text: The string to reverse
        :return: The reversed string
        """
        result = text[::-1]
        if self.valves.enable_uppercase:
            result = result.upper()
        return result
```

## 2. Pipes

Pipes are powerful components that can intercept and modify messages between the user and the LLM. They can be used for tasks like:
- Adding context to messages
- Modifying model responses
- Implementing custom model routing
- Adding authentication/authorization
- Managing model interactions
- Processing citations and references

### Model Management with Pipes

When developing Pipe functions, it's recommended to use OpenWebUI's built-in model management system instead of making direct API calls. This provides several benefits:

1. **Automatic Authentication**: Uses the user's existing model configurations
2. **Simplified Deployment**: No need to manage API keys or endpoints
3. **Better Integration**: Works seamlessly with OpenWebUI's model selection UI

### Basic Pipe Structure with Model Management

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

## 3. Filters

Filters allow you to modify messages at different stages of processing:
- `inlet`: Before the message is sent to the LLM
- `stream`: As the LLM generates a response (for streaming)
- `outlet`: After the LLM has generated a response

### Filter Example

```python
"""
title: 'Message Logger'
description: 'Logs all incoming and outgoing messages.'
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional

class Filter:
    class Valves(BaseModel):
        log_level: str = "INFO"
        
    def __init__(self):
        self.valves = self.Valves()
        
    def inlet(self, body: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[INLET] {body}")
        return body
        
    def stream(self, event: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[STREAM] {event}")
        return event
        
    def outlet(self, body: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[OUTLET] {body}")
        return body
```

## 4. Actions


Action Functions add custom buttons to the message toolbar, enabling interactive functionality like "Summarize" or "Translate" buttons.

### Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Must be named `Action`
- **Method**: `async def action()` - main entry point
- **Docstring Frontmatter**: Required metadata defining button behavior

### Action Method Parameters
- `body: dict`: Message data and context
- `__user__`: User object with permissions and settings
- `__event_emitter__`: Function for real-time UI updates
- `__event_call__`: Function for bidirectional communication
- `__model__`: Model information that triggered the action
- `__request__`: FastAPI request object
- `__id__`: Action ID for multi-action functions

### Frontmatter Fields
- `title`: Display name of the Action
- `author`: Creator name
- `version`: Version number
- `required_open_webui_version`: Minimum compatible version
- `icon_url`: Custom icon (data:image/svg+xml;base64,...)
- `requirements`: Python package dependencies

### Template Structure

```python
"""
title: 'Summarize Message'
description: 'Adds a button to summarize the selected message.'
author: 'Your Name'
version: '0.1.0'
required_open_webui_version: '0.3.9'
icon_url: 'data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIHdpZHRoPSIyNHB4IiBoZWlnaHQ9IjI0cHgiIHZpZXdCb3g9IjAgMCAyNCAyNCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIj48dGl0bGU+U3VtbWFyaXplPC90aXRsZT48ZGVzYz5DcmVhdGVkIHdpdGggU2tldGNoLjwvZGVzYz48ZyBpZD0iUGFnZS0xIiBzdHJva2U9Im5vbmUiIHN0cm9rZS1pZHRwPSIxIiBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGlkPSJTdW1tYXJpemUiIGZpbGw9IiNmZmZmZmYiIGZpbGwtcnVsZT0ibm9uemVybyI+PHBhdGggZD0iTTQsNCBMMjAsNCBMMjAsNiBMNCw2IEw0LDQgWiBNNCw4IEwyMCw4IEwyMCwxMCBMNCwxMCBMNCw4IFogTTQsMTIgTDIwLDEyIEwyMCwxNCBMNCwxNCBMNCwxMiBaIE00LDE2IEwxNCwxNiBMMTQsMTggTDQsMTggTDQsMTYgWiIgaWQ9IkxpbmVzIj48L3BhdGg+PC9nPjwvZz48L3N2Zz4='
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
import asyncio

class Valves(BaseModel):
    summary_prefix: str = Field(
        default="Summary:",
        description="Text to add before the summary."
    )

# Main class must be named 'Action'
class Action:
    def __init__(self):
        self.valves = self.Valves()

    # Main entry point when button is clicked
    async def action(
        self,
        body: dict,
        __user__ = None,
        __event_emitter__ = None,
        __event_call__ = None,
        __model__ = None,
        __request__ = None,
        __id__ = None,
    ) -> dict:
        
        # Get message content that triggered this action
        message_content = body.get("content", "")
        
        # Send status update to UI
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Summarizing message...", "done": False}
        })

        # Perform the action (example: call an LLM to summarize)
        await asyncio.sleep(1)  # Simulate processing
        summary = f"This is a summary of: '{message_content[:20]}...'"
        
        # Get prefix from valves
        valves = __user__["valves"] if __user__ else self.valves
        prefix = valves.summary_prefix

        # Send final status update
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Summary complete!", "done": True}
        })

        # Return new body to update message content
        return {
            "content": f"**{prefix}**\n\n{summary}"
        }
```


## 5. Common Patterns

### Accessing User Information

```python
# In any component
async def my_method(self, __user__: Dict, **kwargs):
    user_id = __user__.get("id")
    user_email = __user__.get("email")
    # Access valve settings
    my_setting = __user__.get("valves", {}).get("my_component", {}).get("my_setting")
```

### Sending UI Updates

```python
# In any component with __event_emitter__
async def my_method(self, __event_emitter__, **kwargs):
    await __event_emitter__({
        "type": "status",
        "data": {
            "description": "Processing...",
            "done": False
        }
    })
    # Do work...
    await __event_emitter__({
        "type": "status",
        "data": {
            "description": "Done!",
            "done": True
        }
    })
```

## 6. Version Compatibility

### Component Versions

| Component           | Introduced | Key Features                                                                 |
|---------------------|------------|------------------------------------------------------------------------------|
| **Core Tools**      | v0.1.0     | Basic tool functionality with Valves configuration                           |
| **Pipes**           | v0.2.0     | Message interception and modification                                        |
| **Filters**         | v0.3.0     | Inlet/stream/outlet processing pipeline                                      |
| **Action**          | v0.4.0     | Interactive UI elements with custom actions                                  |
| **Event System**    | v0.5.0     | Real-time updates, user interactions, and status notifications               |
| **Model Management**| v0.6.0     | Built-in model handling, automatic authentication, and simplified deployment |
| **Citations**       | v0.6.5     | Structured citation handling and source attribution                          |
| **Streaming**       | v0.7.0     | Improved streaming support with chunk processing                             |

### Breaking Changes

#### v0.7.0 (Current)
- Updated streaming interface for better performance
- Added support for chunked responses in Pipes
- Improved error handling and status reporting

#### v0.6.0
- Introduced built-in model management system
- Added support for automatic API key handling
- Deprecated direct API calls in favor of `generate_chat_completion`

#### v0.5.0
- Updated function signatures to include `__user__` and `__event_emitter__`
- Added support for real-time UI updates
- Improved error handling with event system

#### v0.4.0
- Introduced new button system
- Deprecated old action system
- Added support for custom UI elements

#### v0.3.0
- Reworked filter system with separate inlet/stream/outlet methods
- Improved message processing pipeline
- Added support for streaming modifications




---

## 2. Pipe Functions (Custom Models)

Pipe Functions act as custom "models" in the OpenWebUI interface, appearing in the model selector. They can create pipelines of models or call external services, enabling integration with non-OpenAI-compatible APIs.

### Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Can be any name (e.g., `MyPipe`)
- **Required Methods**:
  - `pipes()`: Returns list of available models
  - `pipe()`: Main logic for processing chat requests

### Key Methods

#### pipes() Method
- **Purpose**: Returns available models as a list
- **Return Type**: `list[dict]`
- **Format**: `[{"id": "model_id", "name": "Model Name"}]`
- **Usage**: Creates "manifold" - single pipe representing multiple models

#### pipe() Method
- **Purpose**: Main entry point for processing chat requests
- **Parameters**:
  - `body: dict`: Request data containing `body["model"]` and `body["messages"]`
  - `__user__: dict = None`: User information for authentication
  - `__request__: Request = None`: FastAPI request object
- **Return Types**:
  - Non-streaming: `str` or `dict` (e.g., `{"content": "response"}`)
  - Streaming: `Iterable` (yields response chunks when `body.get("stream", False)` is True)

### Template Structure

```python
"""
title: 'My Custom Pipe'
description: 'A pipe function that acts as a custom model.'
author: 'Your Name'
version: '0.1.0'
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union, Generator, Any
from fastapi import Request
import json

class Valves(BaseModel):
    api_url: str = Field(default="https://api.example.com", description="Endpoint for the custom service.")

# Class name can be custom
class MyPipe:
    def __init__(self):
        self.valves = self.Valves()

    # Returns list of models this pipe provides
    def pipes(self) -> list:
        # These appear in OpenWebUI model selector
        return [
            {"id": "my-pipe-model-1", "name": "My Custom Model 1"},
            {"id": "my-pipe-model-2", "name": "My Custom Model 2"},
        ]

    # Main entry point for processing chat requests
    def pipe(self, body: dict, __user__: dict = None, __request__: Request = None) -> Any:
        model_id = body.get("model", "")
        messages = body.get("messages", [])
        last_message = messages[-1].get("content", "") if messages else ""
        is_streaming = body.get("stream", False)

        # Routing logic based on selected model
        if model_id == "my-pipe-model-1":
            response_content = f"Response from Model 1 for: {last_message}"
        else:
            response_content = f"Response from Model 2 for: {last_message}"

        if not is_streaming:
            # Return single dictionary for non-streaming
            return {"content": response_content}
        
        # For streaming, yield OpenAI-compatible chunks
        def stream_generator():
            chunk = {
                "id": "chatcmpl-...",
                "object": "chat.completion.chunk",
                "created": 12345,
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": response_content},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            
            # Final chunk
            final_chunk = {
                "id": "chatcmpl-...",
                "object": "chat.completion.chunk",
                "created": 12345,
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return stream_generator()
```

## 3. Filter Functions (Modify I/O)

Filter Functions "hook" into the chat request/response process to modify data in transit. They act as "water treatment stages" for data flowing to and from models.

### Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Can be any name (e.g., `Filter`)
- **UI Controls**: 
  - Set `self.toggle = True` in `__init__` to create on/off switch (OpenWebUI 0.6.10+)
  - Set `self.icon` to SVG data URI for custom icon

### Core Methods

#### inlet() Method
- **Purpose**: Modifies request before sending to LLM (pre-processing)
- **Parameters**: `body: dict`, `__user__: Optional[dict] = None`
- **Use Cases**: Add context, format data, sanitize input, streamline user input

#### stream() Method (OpenWebUI 0.5.17+)
- **Purpose**: Modifies streaming response chunks in real-time
- **Parameters**: `event: dict`
- **Use Cases**: Real-time censorship, modify streaming responses, logging

#### outlet() Method
- **Purpose**: Modifies completed response after LLM processing (post-processing)
- **Parameters**: `body: dict`, `__user__: Optional[dict] = None`
- **Use Cases**: Clean up response, adjust tone, format data

### Template Structure

```python
"""
title: 'My Chat Filter'
description: 'A filter that modifies chat inputs and outputs.'
author: 'Your Name'
version: '0.1.0'
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict

class Valves(BaseModel):
    replacement_text: str = Field(
        default="***REDACTED***",
        description="Text to use for redaction."
    )
    words_to_redact_csv: str = Field(
        default="secret,private",
        description="A comma-separated list of words to redact from input."
    )

class Filter:
    def __init__(self):
        self.valves = self.Valves()
        # Create toggle switch in UI (OpenWebUI 0.6.10+)
        self.toggle = True
        # Custom icon for the toggle
        self.icon = "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIHdpZHRoPSIyNHB4IiBoZWlnaHQ9IjI0cHgiIHZpZXdCb3g9IjAgMCAyNCAyNCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIj48dGl0bGU+RmlsdGVyPC90aXRsZT48ZGVzYz5DcmVhdGVkIHdpdGggU2tldGNoLjwvZGVzYz48ZyBpZD0iUGFnZS0xIiBzdHJva2U9Im5vbmUiIHN0cm9rZS1pZHRwPSIxIiBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGlkPSJGaWx0ZXIiIGZpbGw9IiNmZmZmZmYiIGZpbGwtcnVsZT0ibm9uemVybyI+PHBhdGggZD0iTTEyLDIgQzYuNDc3MTUyNTUsMiAyLDYuNDc3MTUyNTUgMiwxMiBDMiwxNy41MjI4NDc1IDYuNDc3MTUyNTUsMjIgMTIsMjIgQzE3LjUyMjg0NzUsMjIgMjIsMTcuNTIyODQ3NSAyMiwxMiBDMjIsNi40NzcxNTI1NSAxNy41MjI4NDc1LDIgMTIsMiBaIE0xMiwyMCBDNy41ODM3NDA2OCwyMCA0LDE2LjQxNjI1OTMgNCwxMiBDNCw3LjU4Mzc0MDY4IDcuNTgzNzQwNjgsNCAxMiw0IEMxNi40MTYyNTkzLDQgMjAsNy41ODM3NDA2OCAyMCwxMiBDMjAsMTYuNDE2MjU5MyAxNi40MTYyNTkzLDIwIDEyLDIwIFogTTEzLjUsOC4yNSBMMy43NSwxMiBMOSwxMiBMOSwxMy41IEwxNSwxMy41IEwxNSwxMiBMMjAuMjUsMTIgTDEwLjUsOC4yNSBaIE05LDE1IEwyMC4yNSwxNSBMOSwxOC43NSBMOSwxNSBaIiBpZD0iT3ZhbCI+PC9wYXRoPjwvZz48L2c+PC9zdmc+"

    # Modifies request before sending to LLM
    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        try:
            # Get valve settings
            valves = __user__["valves"] if __user__ else self.valves
            replacement = valves.replacement_text
            words_to_redact = valves.words_to_redact_csv.split(',')
            
            # Modify the last user message
            if body.get("messages"):
                last_message = body["messages"][-1]
                if last_message.get("role") == "user":
                    content = last_message.get("content", "")
                    for word in words_to_redact:
                        if word:
                            content = content.replace(word, replacement)
                    body["messages"][-1]["content"] = content
        except Exception as e:
            print(f"Filter inlet error: {e}")
            
        return body

    # Modifies streaming response chunks (OpenWebUI 0.5.17+)
    def stream(self, event: dict) -> dict:
        try:
            if event["choices"][0]["delta"].get("content"):
                text = event["choices"][0]["delta"]["content"]
                # Example: Convert to uppercase
                event["choices"][0]["delta"]["content"] = text.upper()
        except Exception as e:
            print(f"Filter stream error: {e}")
            
        return event

    # Modifies completed response after LLM processing
    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        try:
            # Example: Add formatting to assistant responses
            if body.get("messages"):
                for message in body["messages"]:
                    if message.get("role") == "assistant":
                        content = message.get("content", "")
                        if content and not content.startswith("**Formatted:**"):
                            message["content"] = f"**Formatted:**\n{content}"
        except Exception as e:
            print(f"Filter outlet error: {e}")
            
        return body
```


## Best Practices and Security Considerations

### Security
- Be cautious with API keys and sensitive data in valve configurations
- Implement proper error handling and user feedback

### Performance
- Use async/await for I/O operations
- Implement timeouts for external API calls
- Consider background tasks for long-running operations
- Provide progress updates for heavy processing

### User Experience
- Clear error messages and feedback
- Status updates for long operations
- Confirmation dialogs for destructive actions
- Intuitive button labels and descriptions

### Development
- Follow Pydantic best practices for valve definitions
- Use proper type hints and documentation
- Test with various input scenarios
- Consider both streaming and non-streaming modes

## Version Compatibility

- **Filter stream() method**: OpenWebUI 0.5.17+
- **Filter toggle functionality**: OpenWebUI 0.6.10+
- **Action functions**: OpenWebUI 0.3.9+
- Always specify `required_open_webui_version` in frontmatter

## Installation and Usage

Functions are installed through the OpenWebUI community library or by importing directly. They can be:
- Enabled globally for all models
- Configured per-model in model settings
- Toggled on/off during chat sessions

Refer to the OpenWebUI documentation for detailed installation and configuration instructions.