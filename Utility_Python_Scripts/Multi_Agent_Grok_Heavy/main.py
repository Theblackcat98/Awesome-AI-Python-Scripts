from agent import GeminiAgent

def main():
    """Main entry point for the Gemini agent"""
    print("Gemini Agent with DuckDuckGo Search")
    print("Type 'quit', 'exit', or 'bye' to exit")
    print("-" * 50)
    
    try:
        agent = GeminiAgent()
        print("Agent initialized successfully!")
        print(f"Using model: {agent.config['gemini']['model']}")
        print("Note: Make sure to set your Gemini API key in config.yaml")
        print("-" * 50)
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("Make sure you have:")
        print("1. Set your Gemini API key in config.yaml")
        print("2. Installed all dependencies with: pip install -r requirements.txt")
        return
    
    while True:
        try:
            user_input = input("\nUser: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question or command.")
                continue
            
            print("Agent: Thinking...")
            response = agent.run(user_input)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()