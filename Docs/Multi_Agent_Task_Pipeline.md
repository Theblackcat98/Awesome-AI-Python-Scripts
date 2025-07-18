# Multi-Agent Task Pipeline

The `Multi_Agent_Task_Pipeline` project is a Python script that creates and executes a multi-step task pipeline using an AI agent. It's designed to break down a complex task into smaller, manageable steps and then execute them sequentially.

## Features

- **Task Decomposition**: Breaks down a high-level task into a series of smaller, atomic steps.
- **AI-Powered Step Generation**: Uses an AI model (Ollama) to generate the steps, including descriptions, inputs, tools, and output specifications.
- **Sequential Execution**: Executes the steps in the pipeline in order, using the output of one step as the input for the next.
- **Extensible**: The script can be modified to work with different AI models and to support a wider range of tools.

## How it Works

1.  **Task Input**: The user provides a high-level task as a command-line argument.
2.  **Step Generation**: The `AgenticTaskPipeline` class sends a prompt to the Ollama model to generate a series of steps for the given task.
3.  **Step Execution**: The pipeline then executes each step sequentially. For each step, it sends another prompt to the Ollama model with the details of the step, including the inputs from previous steps.
4.  **Final Output**: The script prints the final results of the pipeline, including the output of each step.

## File Structure

The project consists of a single Python script:

```
Multi_Agent_Task_Pipeline/
└── multiagent_task_pipeline.py    # The main script
```

## How to Use

To use the script, you need to have Python and Ollama installed. You can then run the script from the command line, providing the task you want to perform as an argument.

```bash
python Utility_Python_Scripts/Multi_Agent_Task_Pipeline/multiagent_task_pipeline.py "Your task here"
```

For example:

```bash
python Utility_Python_Scripts/Multi_Agent_Task_Pipeline/multiagent_task_pipeline.py "Write a blog post about the benefits of using a multi-agent system for complex tasks."
```

The script will then generate and execute a pipeline of tasks to accomplish the goal, printing the final result to the console.
