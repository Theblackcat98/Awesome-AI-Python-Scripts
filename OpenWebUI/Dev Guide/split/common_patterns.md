# Common Patterns

This section provides common patterns and code examples that can be used across all OpenWebUI Function components.

## Accessing User Information

```python
# In any component
async def my_method(self, __user__: Dict, **kwargs):
    user_id = __user__.get("id")
    user_email = __user__.get("email")
    # Access valve settings
    my_setting = __user__.get("valves", {}).get("my_component", {}).get("my_setting")
```

### User Object Structure
The `__user__` object typically contains:
- `id`: User's unique identifier
- `email`: User's email address
- `valves`: User-specific configuration values for components
- Additional user metadata depending on your setup

## Sending UI Updates

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

### Event Types

#### Status Updates
```python
{
    "type": "status",
    "data": {
        "description": "Processing step...",
        "done": False,
        "is_error": False
    }
}
```

#### Citations
```python
{
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
}
```

#### Error Messages
```python
{
    "type": "status",
    "data": {
        "description": f"Error: {str(e)}",
        "done": True,
        "is_error": True
    }
}
```

## Error Handling

```python
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def my_method(self, **kwargs):
    try:
        # Your logic here
        result = await some_operation()
        return result
    except Exception as e:
        logger.error(f"Error in my_method: {str(e)}", exc_info=True)
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
```

## Best Practices

1. **Always handle errors gracefully** - Use try/catch blocks and provide meaningful error messages
2. **Use proper logging** - Set up logging to help with debugging
3. **Validate inputs** - Check input parameters before processing
4. **Provide UI feedback** - Use event emitters to keep users informed of progress
5. **Follow naming conventions** - Use clear, descriptive names for methods and variables
6. **Document your code** - Add docstrings and comments for maintainability