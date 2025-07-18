import json
import yaml
import google.generativeai as genai
from tools.tool_manager import ToolManager

class GeminiAgent:
    def __init__(self, config_path="config.yaml", silent=False):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.silent = silent
        genai.configure(api_key=self.config['gemini']['api_key'])
        
        # Initialize the tool manager
        self.tool_manager = ToolManager(self.config.get('tool_configs', {}))
        
        # Get tool schemas and execution mapping from the manager
        self.tools = self.tool_manager.get_all_gemini_schemas()
        self.tool_mapping = {name: self.tool_manager.get_tool(name).execute for name in self.tool_manager.get_registered_tool_names()}

    def handle_tool_call(self, tool_call_part):
        """Handles a tool call and returns a serializable part for the next API call."""
        tool_call = tool_call_part.function_call
        tool_name = tool_call.name
        tool_args = {key: value for key, value in tool_call.args.items()}
        
        try:
            # Use the tool manager to execute the tool
            tool_result = self.tool_manager.execute_tool(tool_name, **tool_args)
            
            # Ensure the tool output is always JSON serializable
            try:
                json.dumps(tool_result)
            except (TypeError, OverflowError) as e:
                tool_result = {"error": f"Tool output not JSON serializable: {str(e)}"}

            return {"function_response": {"name": tool_name, "response": tool_result}}
        
        except Exception as e:
            # Broad exception for any failure during tool execution
            return {"function_response": {"name": tool_name, "response": {"error": f"Tool execution failed: {str(e)}"}}}

    def run(self, user_input: str, json_mode: bool = False):
        """
        Initializes a chat session and runs the agent loop.
        If json_mode is True, it configures the model for JSON output.
        """
        print(f"DEBUG: GeminiAgent.run called with user_input: {user_input[:100]}...")
        client = genai.GenerativeModel(
            self.config['gemini']['model'],
            tools=self.tools,
            system_instruction=self.config['system_prompt']
        )
        
        chat = client.start_chat()
        
        try:
            if json_mode:
                # Use generation_config to enforce JSON output
                response = chat.send_message(
                    user_input,
                    generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
                )
            else:
                response = chat.send_message(user_input)
        except Exception as e:
            raise Exception(f"Initial LLM call failed: {e}")

        # If in JSON mode, we expect a direct answer without tool calls
        if json_mode:
            print(f"DEBUG: Gemini API raw response (json_mode): {response}")
            print(f"DEBUG: Gemini API text response (json_mode): {response.text}")
            # The response text is expected to be a JSON string.
            # We'll load it to ensure it's valid, then dump it back to a string to return.
            # This validates the output and ensures consistent string formatting.
            try:
                final_json_output = json.loads(response.text)
                json_output_str = json.dumps(final_json_output)
                print(f"DEBUG: Returning JSON output: {json_output_str}")
                return json_output_str
            except json.JSONDecodeError:
                # If it's not valid JSON, return the raw text and let the caller handle it.
                print(f"DEBUG: Failed to decode JSON from response. Returning raw text.")
                return response.text

        full_response_content = []
        max_iterations = self.config.get('agent', {}).get('max_iterations', 10)
        
        for iteration in range(max_iterations):
            if not self.silent:
                print(f"🔄 Agent iteration {iteration + 1}/{max_iterations}")

            assistant_message = response.candidates[0].content
            
            text_parts = [part.text for part in assistant_message.parts if part.text]
            if text_parts:
                full_response_content.append(" ".join(text_parts))

            tool_call_parts = [part for part in assistant_message.parts if part.function_call]

            if not tool_call_parts:
                if not self.silent:
                    print("💭 Agent responded without tool calls. Task may be complete.")
                return "\n\n".join(full_response_content)

            if not self.silent:
                print(f"🔧 Agent making {len(tool_call_parts)} tool call(s)")

            tool_response_parts = []
            task_completed = False
            for tool_call_part in tool_call_parts:
                tool_name = tool_call_part.function_call.name
                if not self.silent:
                    print(f"   📞 Calling tool: {tool_name}")
                
                tool_result_part = self.handle_tool_call(tool_call_part)
                tool_response_parts.append(tool_result_part)
                
                if tool_name == "mark_task_complete":
                    task_completed = True
            
            if task_completed:
                if not self.silent:
                    print("✅ Task completion tool called - exiting loop")
                return "\n\n".join(full_response_content)

            try:
                response = chat.send_message(
                    tool_response_parts
                )
            except Exception as e:
                raise Exception(f"LLM call with tool response failed: {e}")

        return "\n\n".join(full_response_content) if full_response_content else "Maximum iterations reached."