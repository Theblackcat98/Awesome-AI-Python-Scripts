from ollama import chat
from ollama import ChatResponse
import os

# Learn more about calling the LLM: https://the-pocket.github.io/PocketFlow/utility_function/llm.html

def call_llm(prompt):
     from ollama import chat
     response = chat(
         model="phi4:latest",
         messages=[{"role": "user", "content": prompt}]
     )
     return response.message.content
    
if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
