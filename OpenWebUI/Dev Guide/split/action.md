# Actions

Action Functions add custom buttons to the message toolbar, enabling interactive functionality like "Summarize" or "Translate" buttons.

## Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Must be named `Action`
- **Method**: `async def action()` - main entry point
- **Docstring Frontmatter**: Required metadata defining button behavior

## Action Method Parameters
- `body: dict`: Message data and context
- `__user__`: User object with permissions and settings
- `__event_emitter__`: Function for real-time UI updates
- `__event_call__`: Function for bidirectional communication
- `__model__`: Model information that triggered the action
- `__request__`: FastAPI request object
- `__id__`: Action ID for multi-action functions

## Frontmatter Fields
- `title`: Display name of the Action
- `author`: Creator name
- `version`: Version number
- `required_open_webui_version`: Minimum compatible version
- `icon_url`: Custom icon (data:image/svg+xml;base64,...)
- `requirements`: Python package dependencies

## Complete Example

```python
"""
title: 'Summarize Message'
description: 'Adds a button to summarize the selected message.'
author: 'Your Name'
version: '0.1.0'
required_open_webui_version: '0.3.9'
icon_url: 'data:image/svg+xml;base64,(...)
requirements: ['asyncio']
"""

import asyncio
from pydantic import BaseModel, Field
from typing import Dict, Any

class Action:
    def __init__(self):
        pass
    
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
        """
        Main action entry point.
        """
        message_content = body.get("content", "")
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "Summarizing content...", "done": False}
            })
        
        # Simulate processing
        await asyncio.sleep(1)
        
        # Generate summary
        summary = f"Summary of: {message_content[:50]}..."
        word_count = len(message_content.split())
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "Summary complete!", "done": True}
            })
        
        return {
            "summary": summary,
            "word_count": word_count,
            "reading_time": f"{word_count // 200} minutes"
        }
```

## Multi-Action Example

```python
"""
title: 'Content Processor'
description: 'Process content with multiple operation options.'
author: 'OpenWebUI Team'
version: '1.0.0'
required_open_webui_version: '0.3.9'
requirements: ['asyncio', 'requests']
"""

import asyncio
from pydantic import BaseModel, Field
from typing import Optional, Dict

class Valves(BaseModel):
    api_endpoint: str = Field(
        default="https://api.example.com",
        description="API endpoint for processing"
    )

class Action:
    def __init__(self):
        self.valves = Valves()
        self.actions = {
            "summarize": {"title": "Summarize Content", "icon": "📝"},
            "translate": {"title": "Translate Content", "icon": "🌐"},
        }

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
        
        action_type = __id__ or "summarize"
        message_content = body.get("content", "")
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"Starting {self.actions[action_type]['title']}...",
                    "done": False
                }
            })

        try:
            if action_type == "summarize":
                result = {"summary": f"Summary: {message_content[:50]}..."}
            elif action_type == "translate":
                result = {"translated": f"Translated: {message_content}"}
            else:
                result = {"error": f"Unknown action: {action_type}"}
            
            return {
                "message": message_content,
                "action": action_type,
                "result": result
            }
            
        except Exception as e:
            error_msg = f"Error during {action_type}: {str(e)}"
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": error_msg, "done": True, "is_error": True}
                })
            raise
```

## Key Concepts

1. **Event Emitters**: Use `__event_emitter__` for progress updates and status notifications
2. **User Interaction**: Leverage `__event_call__` for confirmations and input collection  
3. **Multi-Action Support**: Use `__id__` parameter for multiple sub-actions
4. **Error Handling**: Always wrap operations in try-catch blocks with user feedback
5. **Background Tasks**: For long operations, consider using background task patterns

## Related Documentation
- [Action Functions](https://docs.openwebui.com/features/plugin/functions/action/)
- [Event Emitters](https://docs.openwebui.com/features/plugin/functions/)
- [Background Tasks](https://docs.openwebui.com/features/plugin/functions/action/)