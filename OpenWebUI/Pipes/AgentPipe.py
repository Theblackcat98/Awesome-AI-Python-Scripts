from typing import Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import aiohttp
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Pipe:
    class Valves(BaseModel):
        ENABLED: bool = Field(
            default=True,
            description="Enable or disable the Agentic Pipe"
        )
        MAX_ITERATIONS: int = Field(
            default=5,
            description="Maximum number of tool iterations before stopping"
        )
        TOOL_TIMEOUT: int = Field(
            default=30,
            description="Timeout for tool execution in seconds"
        )
        LLM_MODEL: str = Field(
            default="jan-nano:latest",
            description="The LLM model to use for generating responses"
        )
        LLM_TEMPERATURE: float = Field(
            default=0.7,
            ge=0.0,
            le=2.0,
            description="Temperature for LLM generation (0.0 to 2.0)"
        )
        LLM_MAX_TOKENS: int = Field(
            default=2000,
            description="Maximum number of tokens to generate"
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()
        self.__user__ = None
        self.__request__ = None
        self.__event_emitter__ = None
        self.__event_call__ = None
        self.__task__ = None
        self.__model__ = None
        
        # Define available tools
        # Note: These are just example tools. To add real functionality:
        # 1. Define the tool specification here
        # 2. Implement the corresponding method (e.g., tool_echo)
        # 3. Add error handling in execute_tool_calls
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "echo",
                    "description": "Echo back the input text (for testing)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "The text to echo back"}
                        },
                        "required": ["text"]
                    }
                }
            }
            # To add more tools, uncomment and modify the example below:
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "web_search",
            #         "description": "Search the web for information",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "query": {"type": "string", "description": "The search query"},
            #                 "num_results": {"type": "integer", "description": "Number of results to return", "default": 3}
            #             },
            #             "required": ["query"]
            #         }
            #     }
            # }
        ]

    async def pipe(
        self,
        body: Dict[str, Any],
        __event_emitter__: Optional[Callable[[Dict], Awaitable[None]]] = None,
        __user__: Optional[Dict] = None,
        __event_call__: Optional[Callable[[Dict], Awaitable[Any]]] = None,
        __task__: Optional[Any] = None,
        __model__: Optional[str] = None,
        __request__: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Main entry point for the pipe."""
        logger.info("Pipe called with body: %s", body)
        
        # Store the event call function
        self.__event_emitter__ = __event_emitter__
        self.__event_call__ = __event_call__
        self.__user__ = __user__
        self.__task__ = __task__
        self.__model__ = __model__
        self.__request__ = __request__
        
        logger.info("Processing message through inlet and outlet")
        try:
            # Process the message through inlet and outlet
            body = await self.inlet(body, __event_emitter__, __user__)
            logger.info("Inlet processing complete")
            
            body = await self.outlet(body, __event_emitter__, __user__)
            logger.info("Outlet processing complete")
            
            logger.info("Returning body: %s", body)
            return body
        except Exception as e:
            logger.exception("Error in pipe method")
            return {"error": str(e)}

    async def inlet(
        self,
        body: Dict[str, Any],
        __event_emitter__: Optional[Callable[[Dict], Awaitable[None]]] = None,
        __user__: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Process incoming messages and initialize the agent state."""
        self.__event_emitter__ = __event_emitter__
        self.__user__ = __user__
        return body

    async def outlet(
        self,
        body: Dict[str, Any],
        __event_emitter__: Optional[Callable[[Dict], Awaitable[None]]] = None,
        __user__: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Process outgoing messages and handle tool calls."""
        logger.info("Outlet called with body: %s", body)
        
        if not self.valves.ENABLED:
            logger.warning("Pipe is disabled, returning unmodified body")
            return body

        message = body.get("message", "")
        if not message:
            return body

        # Initialize conversation history if not present
        if "conversation" not in body:
            body["conversation"] = []

        # Add user message to conversation
        body["conversation"].append({"role": "user", "content": message})
        
        # Initialize agent state if not present
        if "agent_state" not in body:
            body["agent_state"] = {
                "iteration": 0,
                "completed": False,
                "tool_results": []
            }

        # Main agent loop
        while (not body["agent_state"]["completed"] and 
               body["agent_state"]["iteration"] < self.valves.MAX_ITERATIONS):
            
            # Generate response (potentially with tool calls)
            response = await self.generate_agent_response(
                body["conversation"],
                body["agent_state"]["tool_results"]
            )
            
            # Process tool calls if any
            if "tool_calls" in response:
                tool_results = await self.execute_tool_calls(
                    response["tool_calls"]
                )
                body["agent_state"]["tool_results"].extend(tool_results)
            else:
                body["agent_state"]["completed"] = True
                body["response"] = response["content"]
            
            body["agent_state"]["iteration"] += 1

        return body

    async def generate_agent_response(self, conversation, tool_results):
        """Generate a response using the LLM, potentially with tool calls."""
        try:
            # Prepare messages for the LLM
            messages = conversation.copy()
            
            # Add tool results to the conversation if any
            if tool_results:
                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": str(result["result"])
                    })

            # Prepare the request to the LLM
            llm_request = {
                "messages": messages,
                "model": self.valves.LLM_MODEL,
                "temperature": self.valves.LLM_TEMPERATURE,
                "max_tokens": self.valves.LLM_MAX_TOKENS,
                "tools": self.tools,
                "tool_choice": "auto"
            }
            
            logger.info("Calling LLM with request: %s", llm_request)
            
            # Call the LLM with tool use capability
            response = await self.__event_call__(llm_request)
            logger.info("Received LLM response: %s", response)

            # Extract the response content and tool calls
            response_message = response.get("choices", [{}])[0].get("message", {})
            
            return {
                "content": response_message.get("content", ""),
                "tool_calls": response_message.get("tool_calls", [])
            }

        except Exception as e:
            # Fallback response in case of errors
            return {
                "content": f"I encountered an error while generating a response: {str(e)}",
                "tool_calls": []
            }

    async def execute_tool_calls(self, tool_calls):
        """Execute the requested tool calls."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"]
            
            try:
                if tool_name == "echo":
                    result = await self.tool_echo(**tool_args)
                # Add more tools here as you implement them
                # elif tool_name == "web_search":
                #     result = await self.tool_web_search(**tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"
                
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "tool_name": tool_name,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "tool_name": tool_name,
                    "error": str(e)
                })
        
        return results

    async def tool_echo(self, text: str) -> str:
        """Echo back the input text (for testing)."""
        return f"Echo: {text}"

    # Example of how to implement a real tool:
    # async def tool_web_search(self, query: str, num_results: int = 3):
    #     """Search the web for information."""
    #     # Implementation using your preferred search API
    #     # For example, using the requests library:
    #     # response = requests.get(f"https://api.searchprovider.com/search?q={query}&limit={num_results}")
    #     # return response.json()
    #     pass
    # 
    # async def tool_scrape_website(self, url: str):
    #     """Scrape content from a website."""
    #     # Implementation using requests/beautifulsoup
    #     # For example:
    #     # import requests
    #     # from bs4 import BeautifulSoup
    #     # response = requests.get(url)
    #     # soup = BeautifulSoup(response.text, 'html.parser')
    #     # return soup.get_text()
    #     pass