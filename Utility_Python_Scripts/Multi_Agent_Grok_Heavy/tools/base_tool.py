from abc import ABC, abstractmethod
from typing import Any, Dict
import google.generativeai.protos as protos

class BaseTool(ABC):
    """
    Abstract Base Class for all tools. Defines the common interface and
    provides a method to convert the tool to Gemini's function declaration schema.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the tool with a configuration dictionary.
        Subclasses should call super().__init__(config).
        """
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The unique name of the tool, used by the LLM to call it.
        Example: "calculate", "read_file"
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        A detailed description of what the tool does, for the LLM.
        This is crucial for the LLM to understand when and how to use the tool.
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        The OpenAPI schema for the tool's input parameters.
        Defines the expected arguments for the 'execute' method.
        Example:
        {
            "type": "object",
            "properties": {
                "arg1": {"type": "string", "description": "Desc of arg1"}
            },
            "required": ["arg1"]
        }
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes the tool's core functionality with the provided arguments.
        This method will be called by the ToolManager based on LLM suggestions.
        Must return a dictionary indicating success/failure and relevant output.
        """
        pass

    def to_gemini_schema(self) -> protos.FunctionDeclaration:
        """
        Converts the tool instance into the Gemini API's FunctionDeclaration format.
        This method is concrete because all tools will use the same structure
        based on their abstract properties.
        """
        # Mapping from JSON Schema types to proto.Type enum
        type_map = {
            "string": protos.Type.STRING,
            "number": protos.Type.NUMBER,
            "integer": protos.Type.INTEGER,
            "boolean": protos.Type.BOOLEAN,
            "array": protos.Type.ARRAY,
            "object": protos.Type.OBJECT,
        }

        schema_properties = self.parameters.get("properties", {})
        
        proto_properties = {}
        for key, value in schema_properties.items():
            # Get the correct enum type, defaulting to STRING if not found
            prop_type_str = value.get("type", "string")
            prop_type = type_map.get(prop_type_str.lower(), protos.Type.STRING)
            
            proto_properties[key] = protos.Schema(
                type=prop_type,
                description=value.get("description", "")
            )

        return protos.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties=proto_properties,
                required=self.parameters.get("required", [])
            )
        )