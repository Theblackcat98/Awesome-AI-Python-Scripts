# Multi-Agent Grok Heavy

The `Multi_Agent_Grok_Heavy` project is a Python framework that emulates the functionality of "Grok heavy" mode. It utilizes a multi-agent system to deliver a comprehensive, multi-perspective analysis of a user's query. The project is built on OpenRouter's API and features intelligent agent orchestration.

## Features

- **Grok heavy Emulation**: A multi-agent system that provides deep and comprehensive analysis.
- **Parallel Intelligence**: Deploys four specialized agents simultaneously for maximum insight coverage.
- **Dynamic Question Generation**: An AI creates custom research questions tailored to each query.
- **Real-time Orchestration**: Provides live visual feedback during multi-agent execution.
- **Hot-Swappable Tools**: Automatically discovers and loads tools from the `tools/` directory.
- **Intelligent Synthesis**: Combines multiple agent perspectives into a unified, comprehensive answer.
- **Single Agent Mode**: Allows running individual agents for simpler tasks with full tool access.

## How it Works

1.  **AI Question Generation**: The system generates four specialized research questions from the user's query.
2.  **Parallel Intelligence**: It runs four agents simultaneously, each with a different analytical perspective.
3.  **Live Progress**: Shows real-time agent status with visual progress bars.
4.  **Intelligent Synthesis**: The system combines all perspectives into one comprehensive, Grok heavy-style answer.

## File Structure

The project is organized as follows:

```
Multi_Agent_Grok_Heavy/
├── main.py                 # Single agent CLI
├── make_it_heavy.py         # Multi-agent orchestrator CLI
├── agent.py                # Core agent implementation
├── orchestrator.py         # Multi-agent orchestration logic
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── README.md               # Project README
└── tools/                  # Tool system
    ├── __init__.py         # Auto-discovery system
    ├── base_tool.py        # Tool base class
    ├── ...                 # Other tools
```

## How to Use

### Single Agent Mode

To run a single intelligent agent with full tool access:

```bash
python Utility_Python_Scripts/Multi_Agent_Grok_Heavy/main.py
```

The agent will process your query step-by-step, using tools like web search, calculator, and file operations to provide a comprehensive response.

### Grok heavy Mode (Multi-Agent Orchestration)

To emulate Grok heavy's deep analysis with four parallel intelligent agents:

```bash
python Utility_Python_Scripts/Multi_Agent_Grok_Heavy/make_it_heavy.py
```

This will trigger the full multi-agent orchestration process, resulting in a comprehensive, multi-faceted analysis of your query.
