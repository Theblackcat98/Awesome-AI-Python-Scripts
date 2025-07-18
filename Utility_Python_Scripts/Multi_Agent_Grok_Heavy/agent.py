import json
import yaml
import google.generativeai as genai
from tools import discover_tools

class GeminiAgent:
    def __init__(self, config_path="config.yaml", silent=False):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Silent mode for orchestrator (suppresses debug output)
        self.silent = silent
        
        # Initialize Gemini client
        genai.configure(api_key=self.config['gemini']['api_key'])
        self.client = genai.GenerativeModel(self.config['gemini']['model'])
        
        # Discover tools dynamically
        self.discovered_tools = discover_tools(self.config, silent=self.silent)
        
        # Build Gemini tools array
        self.tools = [tool.to_gemini_schema() for tool in self.discovered_tools.values()]
        
        # Build tool mapping
        self.tool_mapping = {name: tool.execute for name, tool in self.discovered_tools.items()}
    
    def call_gemini_llm(self, messages):
        """Make Gemini API call with tools"""
        try:
            chat = self.client.start_chat(history=messages)
            response = chat.send_message("", tools=self.tools)
            return response
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")
    
    def handle_tool_call(self, tool_call):
        """Handle a tool call and return the result message"""
        tool_name = tool_call.function_call.name
        tool_args = {key: value for key, value in tool_call.function_call.args.items()}
        
        try:
            if tool_name in self.tool_mapping:
                tool_result = self.tool_mapping[tool_name](**tool_args)
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}
            
            return {
                "role": "function",
                "parts": [{
                    "function_response": {
                        "name": tool_name,
                        "response": tool_result
                    }
                }]
            }
        except Exception as e:
            return {
                "role": "function",
                "parts": [{
                    "function_response": {
                        "name": tool_name,
                        "response": {"error": f"Tool execution failed: {str(e)}"}
                    }
                }]
            }

    def run(self, user_input: str):
        """Run the agent with user input and return FULL conversation content"""
        # Initialize messages with system prompt and user input
        messages = [
            {'role': 'user', 'parts': [self.config['system_prompt']]},
            {'role': 'model', 'parts': ["Okay, I understand my instructions."]},
            {'role': 'user', 'parts': [user_input]}
        ]
        
        full_response_content = []
        
        max_iterations = self.config.get('agent', {}).get('max_iterations', 10)
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            if not self.silent:
                print(f"🔄 Agent iteration {iteration}/{max_iterations}")
            
            response = self.call_gemini_llm(messages)
            
            assistant_message = response.candidates[0].content
            messages.append(assistant_message)
            
            text_parts = [part.text for part in assistant_message.parts if hasattr(part, 'text')]
            if any(text_parts):
                full_response_content.append(" ".join(text_parts))

            tool_calls = [part for part in assistant_message.parts if hasattr(part, 'function_call')]

            if tool_calls:
                if not self.silent:
                    print(f"🔧 Agent making {len(tool_calls)} tool call(s)")
                
                task_completed = False
                for tool_call in tool_calls:
                    if not self.silent:
                        print(f"   📞 Calling tool: {tool_call.function_call.name}")
                    
                    tool_result_message = self.handle_tool_call(tool_call)
                    messages.append(tool_result_message)
                    
                    if tool_call.function_call.name == "mark_task_complete":
                        task_completed = True
                        if not self.silent:
                            print("✅ Task completion tool called - exiting loop")
                        return "\n\n".join(full_response_content)
                
                if task_completed:
                    return "\n\n".join(full_response_content)
            else:
                if not self.silent:
                    print("💭 Agent responded without tool calls - continuing loop")

        return "\n\n".join(full_response_content) if full_response_content else "Maximum iterations reached. The agent may be stuck in a loop."