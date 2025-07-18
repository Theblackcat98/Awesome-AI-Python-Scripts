from typing import Any, Dict, Optional
import os
from .base_tool import BaseTool

class ReadFileTool(BaseTool):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # You can use config here, e.g., self.max_file_size = config.get("max_size_mb", 10) * 1024 * 1024

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the complete contents of a text file from the file system. Can return the full content or just the first/last N lines. Handles various text encodings and provides detailed error messages."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative file path to read (e.g., 'documents/report.txt', 'C:/data/log.csv')."
                },
                "head": {
                    "type": "integer",
                    "description": "If provided, returns only the first N lines of the file. Cannot be used with 'tail'."
                },
                "tail": {
                    "type": "integer",
                    "description": "If provided, returns only the last N lines of the file. Cannot be used with 'head'."
                },
                "encoding": {
                    "type": "string",
                    "description": "The character encoding of the file (e.g., 'utf-8', 'latin-1'). Defaults to 'utf-8'.",
                    "default": "utf-8"
                }
            },
            "required": ["path"]
        }

    def execute(self, path: str, head: Optional[int] = None, tail: Optional[int] = None, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Reads the content of a file.

        Args:
            path: The file path to read.
            head: Optional. If provided, returns only the first N lines.
            tail: Optional. If provided, returns only the last N lines.
            encoding: Optional. The character encoding of the file. Defaults to 'utf-8'.

        Returns:
            A dictionary containing the file content or an error message.
        """
        try:
            # Validate parameters
            if head is not None and tail is not None:
                return {"error": "Cannot specify both 'head' and 'tail' parameters. Please choose one or neither.", "success": False}
            if head is not None and head < 0:
                 return {"error": "'head' parameter must be a non-negative integer.", "success": False}
            if tail is not None and tail < 0:
                 return {"error": "'tail' parameter must be a non-negative integer.", "success": False}


            # Normalize path for security and consistency
            # os.path.abspath and os.path.normpath help prevent directory traversal attacks
            # but you might want more stringent checks if exposing this to untrusted input.
            normalized_path = os.path.normpath(os.path.abspath(path))

            # Basic security check: prevent reading outside a designated directory (if applicable)
            # Example: if your tools are meant to operate only within a 'data' directory
            # if not normalized_path.startswith(os.path.abspath("./data")):
            #     return {"error": f"Access to path '{path}' is denied. Restricted to data directory.", "success": False}

            # Check if file exists
            if not os.path.exists(normalized_path):
                return {"error": f"File not found: '{path}' (resolved to '{normalized_path}')", "success": False}

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(normalized_path):
                return {"error": f"Path is not a file: '{path}' (resolved to '{normalized_path}')", "success": False}

            # Read file content based on head/tail/full
            content: str = ""
            with open(normalized_path, 'r', encoding=encoding) as f:
                if head is not None:
                    lines = []
                    for i in range(head):
                        line = f.readline()
                        if not line:  # EOF reached
                            break
                        lines.append(line)
                    content = ''.join(lines).rstrip('\n') # rstrip to remove trailing newline if it's the last char
                elif tail is not None:
                    lines = f.readlines()
                    content = ''.join(lines[-tail:]).rstrip('\n') if lines else ""
                else:
                    content = f.read()

            return {
                "path": path,
                "content": content,
                "success": True
            }

        except UnicodeDecodeError as e:
            return {"error": f"Failed to decode file with encoding '{encoding}': {str(e)}. Try a different encoding.", "success": False}
        except PermissionError:
            return {"error": f"Permission denied to read file: '{path}'", "success": False}
        except FileNotFoundError: # Should be caught by os.path.exists earlier, but good for robustness
            return {"error": f"File not found: '{path}'", "success": False}
        except Exception as e:
            return {"error": f"An unexpected error occurred while reading file: {type(e).__name__}: {str(e)}", "success": False}