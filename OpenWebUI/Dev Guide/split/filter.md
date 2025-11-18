# Filters

Filters allow you to modify messages at different stages of processing:
- `inlet`: Before the message is sent to the LLM
- `stream`: As the LLM generates a response (for streaming)
- `outlet`: After the LLM has generated a response

## Structure Requirements
- **File Structure**: Single Python file
- **Core Class**: Must be named `Filter`
- **Valves Configuration**: User-configurable parameters defined in a nested Pydantic class named `Valves`
- **Initialization**: The `__init__` method must instantiate the `Valves`
- **Processing Methods**: `inlet()`, `stream()`, and `outlet()` methods for different processing stages

## Key Concepts

### Processing Stages
- **Inlet Filter**: Process messages before sending to LLM for validation, context addition, and content filtering
- **Stream Filter**: Modify streaming response chunks in real-time for content moderation and progress tracking
- **Outlet Filter**: Post-process final responses for formatting, citations, and analytics

### UI Components
Filters support UI components through `json_schema_extra`:
- **Toggle**: `{"ui": {"component": "toggle"}}`
- **Select/Dropdown**: `{"ui": {"component": "select", "options": [...]}}`
- **Input**: `{"ui": {"component": "input", "placeholder": "..."}}`

## Complete Example

```python
"""
title: 'Content Filter'
description: 'Filter and process messages at different stages.'
author: 'OpenWebUI Team'
version: '1.0.0'
"""

import re
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class Filter:
    class Valves(BaseModel):
        # Toggle switch for enabling/disabling features
        enable_filtering: bool = Field(
            default=True,
            description="Enable content filtering",
            json_schema_extra={"ui": {"component": "toggle"}}
        )
        
        # Select dropdown for processing mode
        processing_mode: str = Field(
            default="clean",
            description="Content processing mode",
            json_schema_extra={
                "ui": {
                    "component": "select",
                    "options": [
                        {"value": "clean", "label": "Clean Content"},
                        {"value": "strict", "label": "Strict Filtering"},
                        {"value": "moderate", "label": "Moderate Filtering"}
                    ]
                }
            }
        )
        
        # Text input for custom patterns
        custom_pattern: str = Field(
            default="",
            description="Custom regex pattern to filter",
            json_schema_extra={
                "ui": {
                    "component": "input",
                    "placeholder": "Enter regex pattern..."
                }
            }
        )

    def __init__(self):
        self.valves = self.Valves()
        
    def inlet(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process messages before sending to LLM.
        Add context, validate, or modify incoming messages.
        """
        if not self.valves.enable_filtering:
            return body
            
        messages = body.get("messages", [])
        if messages and self.valves.processing_mode == "strict":
            # Add system context for strict mode
            body["system"] = body.get("system", "") + "\n\nPlease be professional and avoid informal language."
        
        return body
        
    def stream(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process streaming response chunks in real-time.
        Useful for content moderation and modification.
        """
        if not self.valves.enable_filtering or "content" not in event:
            return event
            
        content = event["content"]
        
        # Apply filtering based on mode
        if self.valves.processing_mode == "strict":
            # Remove potentially inappropriate content
            content = re.sub(r'\b(bad|wrong|terrible)\b', 'inappropriate', content, flags=re.IGNORECASE)
        elif self.valves.processing_mode == "moderate":
            # Light filtering
            content = re.sub(r'\b(hate|awful)\b', 'dislike', content, flags=re.IGNORECASE)
        
        # Apply custom pattern if provided
        if self.valves.custom_pattern:
            try:
                content = re.sub(self.valves.custom_pattern, '[FILTERED]', content)
            except re.error:
                pass  # Invalid regex pattern
        
        event["content"] = content
        return event
        
    def outlet(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process final response after LLM generation.
        Post-process responses, add citations, or apply formatting.
        """
        if not self.valves.enable_filtering or "content" not in body:
            return body
            
        content = body["content"]
        
        # Final cleanup
        if self.valves.processing_mode == "clean":
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content).strip()
        
        body["content"] = content
        return body
```

## Advanced Example

```python
def inlet(self, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add research context for academic queries.
    """
    messages = body.get("messages", [])
    if not messages:
        return body
        
    last_message = messages[-1].get("content", "").lower()
    
    # Detect research-related queries
    research_keywords = ["research", "study", "paper", "academic", "journal"]
    if any(keyword in last_message for keyword in research_keywords):
        # Add academic context
        if "system" not in body:
            body["system"] = ""
        body["system"] += "\n\nYou are a research assistant. Cite sources and use academic language."
    
    return body
```

## Best Practices

1. **Performance**: Keep filter operations lightweight, especially in `stream()` for real-time processing
2. **Error Handling**: Always handle edge cases and malformed input gracefully
3. **State Management**: Use instance variables carefully - filters may be reused across multiple requests
4. **Content Types**: Handle both streaming and non-streaming responses appropriately

## Related Documentation
- [Filter Functions](https://docs.openwebui.com/features/plugin/functions/filter/)
- [UI Components Guide](https://docs.openwebui.com/features/plugin/ui-components/)
- [Pydantic Configuration](https://docs.openwebui.com/features/plugin/functions/)