from typing import Dict, List, Any, Type
from .base_tool import BaseTool
from .calculator_tool import CalculatorTool
from .read_file_tool import ReadFileTool

class ToolManager:
    """
    Manages all available tools, providing methods to register them,
    generate Gemini API schemas, and execute tools by name.
    """
    def __init__(self, tool_configs: Dict[str, Dict[str, Any]] = None):
        """
        Initializes the ToolManager and registers default tools.
        Args:
            tool_configs: A dictionary mapping tool names to their specific
                          configuration dictionaries.
                          e.g., {"read_file": {"max_size_mb": 10}}
        """
        self._tools: Dict[str, BaseTool] = {}
        if tool_configs is None:
            tool_configs = {}

        # Register your tools here
        # Instantiate each tool and register it.
        # You could also pass a list of Tool *classes* and instantiate them here.
        self.register_tool(CalculatorTool(tool_configs.get("calculator", {})))
        self.register_tool(ReadFileTool(tool_configs.get("read_file", {})))
        # Add other tools as you develop them:
        # self.register_tool(NewToolClass(tool_configs.get("new_tool", {})))

    def register_tool(self, tool_instance: BaseTool):
        """
        Registers an instance of a BaseTool subclass.
        Args:
            tool_instance: An initialized instance of a BaseTool.
        Raises:
            TypeError: If the provided object is not a BaseTool instance.
            ValueError: If a tool with the same name is already registered.
        """
        if not isinstance(tool_instance, BaseTool):
            raise TypeError("Only instances of BaseTool can be registered.")
        if tool_instance.name in self._tools:
            raise ValueError(f"Tool with name '{tool_instance.name}' is already registered.")
        self._tools[tool_instance.name] = tool_instance
        print(f"Tool '{tool_instance.name}' registered successfully.")


    def get_tool(self, name: str) -> BaseTool:
        """
        Retrieves a registered tool by its name.
        Args:
            name: The name of the tool to retrieve.
        Returns:
            The BaseTool instance.
        Raises:
            ValueError: If the tool is not found.
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")
        return tool

    def get_all_gemini_schemas(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all registered tool schemas, ready for the Gemini API.
        Each item in the list is a single function declaration dictionary.
        """
        return [tool.to_gemini_schema() for tool in self._tools.values()]

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Executes a registered tool by its name with the given arguments.
        Args:
            tool_name: The name of the tool to execute.
            **kwargs: Arguments to pass to the tool's execute method,
                      as provided by the LLM's function call.
        Returns:
            The dictionary result from the tool's execution.
        """
        tool = self.get_tool(tool_name)
        print(f"Executing tool '{tool_name}' with arguments: {kwargs}")
        return tool.execute(**kwargs)

    def get_registered_tool_names(self) -> List[str]:
        """Returns a list of names of all registered tools."""
        return list(self._tools.keys())