import json
import uuid
import sys
import requests
import re
from dataclasses import dataclass, field
from typing import List, Dict

# === CONFIGURATION ===
OLLAMA_MODEL = "jan-nano:latest"  # Change to "mistral", "codellama", etc.
OLLAMA_URL = "http://localhost:11434/api/chat"

# === PROMPT TEMPLATES ===

STEP_GENERATION_PROMPT = """
You are an expert AI architect designing a task decomposition for an autonomous agentic system.

TASK: "{task}"

INSTRUCTIONS:
- Break this task into 1–10 atomic, well-scoped steps.
- Each step must assume it is being executed by an AI agent, not a human.
- All tools should be executable or callable by code (e.g., Python libraries, APIs, shell commands).
- Do NOT use human-facing apps (e.g., Scrivener, Evernote).
- Do NOT reference human cognitive skills (e.g., "storytelling", "writing knowledge").
- Each step must include:
  - step_id
  - title
  - description
  - inputs_required (list)
  - tools (list of packages or commands)
  - output_spec (describe the structure of the output clearly)
  - assumptions (only those relevant to automated systems)

IMPORTANT: Output must be raw JSON only. Do not include markdown formatting or explanations.
"""

STEP_EXECUTION_PROMPT = """
You are executing step "{step_id}: {title}" of a multi-step agentic task pipeline.

DESCRIPTION:
{description}

TOOLS: {tools}
INPUTS: {inputs}
EXPECTED OUTPUT FORMAT: {output_spec}
ASSUMPTIONS:
{assumptions}

Generate Python code or structured content that satisfies this step. Return ONLY the final output (no commentary or markdown).
"""

# === OLLAMA INTERFACE ===

class OllamaLLM:
    def __init__(self, model: str = OLLAMA_MODEL, url: str = OLLAMA_URL):
        self.model = model
        self.url = url

    def call(self, prompt: str) -> str:
        headers = {'Content-Type': 'application/json'}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        response = requests.post(self.url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['message']['content']

# === PIPELINE STRUCTURES ===

@dataclass
class Step:
    step_id: str
    title: str
    description: str
    inputs_required: List[str]
    tools: List[str]
    output_spec: str
    assumptions: List[str]

@dataclass
class PipelineContext:
    task: str
    steps: List[Step] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)

class AgenticTaskPipeline:
    def __init__(self, llm: OllamaLLM):
        self.llm = llm

    def extract_json_block(self, text: str) -> str:
        """Extract valid JSON list from model output, removing markdown and non-JSON preambles."""
        code_match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        array_match = re.search(r"(\[\s*{.*?}\s*\])", text, re.DOTALL)
        if array_match:
            return array_match.group(1).strip()
        return text.strip()

    def generate_steps(self, task: str) -> List[Step]:
        prompt = STEP_GENERATION_PROMPT.format(task=task)
        print("\n🧠 Generating intermediary steps...")
        response = self.llm.call(prompt)
        cleaned = self.extract_json_block(response)

        try:
            steps_raw = json.loads(cleaned)
            steps = [Step(**step) for step in steps_raw]
        except Exception as e:
            print("❌ Failed to parse JSON from step generation.")
            print("Raw response:\n", response)
            sys.exit(1)

        print(f"✅ {len(steps)} step(s) generated.\n")
        return steps

    def execute_step(self, step: Step, context: PipelineContext) -> str:
        print(f"⚙️  Executing: {step.step_id} - {step.title}")
        inputs = {k: context.outputs.get(k, "") for k in step.inputs_required}
        prompt = STEP_EXECUTION_PROMPT.format(
            step_id=step.step_id,
            title=step.title,
            description=step.description,
            tools=", ".join(step.tools),
            inputs=json.dumps(inputs, indent=2),
            output_spec=step.output_spec,
            assumptions="\n".join(step.assumptions)
        )
        result = self.llm.call(prompt)
        context.outputs[step.step_id] = result
        print(f"✅ Step {step.step_id} completed.\n")
        return result

    def run(self, task: str) -> PipelineContext:
        context = PipelineContext(task=task)
        context.steps = self.generate_steps(task)
        for step in context.steps:
            self.execute_step(step, context)
        return context

# === MAIN EXECUTION ===

def main():
    if len(sys.argv) < 2:
        print("❌ Please provide a task to run.")
        print("Usage: python agentic_pipeline.py \"Your task here.\"")
        sys.exit(1)

    user_task = sys.argv[1]
    print(f"\n🚀 Running agentic pipeline for task:\n> {user_task}")

    llm = OllamaLLM()
    pipeline = AgenticTaskPipeline(llm)
    result = pipeline.run(user_task)

    print("\n🎯 Final Results")
    for step in result.steps:
        print(f"\n🔹 Step: {step.step_id} - {step.title}")
        print("Output:")
        print(result.outputs[step.step_id])
        print("-" * 60)

if __name__ == "__main__":
    main()
