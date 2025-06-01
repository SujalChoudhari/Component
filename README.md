# 🤖 Self-Modifying AI Agent with Component Architecture

This project explores the fascinating intersection of modular software design and generative AI, aiming to build an AI agent that can not only utilize tools (components) but also **dynamically create, modify, and manage its own capabilities.**

## Project Overview

At its core, this project demonstrates a robust component-based architecture for AI agents. It features:

*   **Modular Components:** Define specific functionalities (e.g., weather lookup, logging) as independent Python classes.
*   **Dynamic Component Management:** A `ComponentManager` automatically discovers, imports, and manages the lifecycle (load, use, destroy) of these components from a specified directory.
*   **AI Integration (Gemini):** A `ComponentManager` interfaces with Google's Gemini LLM, converting discovered components into `FunctionDeclaration` tools that the AI can perceive and choose to `use`.
*   **Interactive CLI:** A command-line interface allows users to chat with the AI, observing its decisions to use tools and the results of those tool calls.
*   **Rate Limiting:** Built-in mechanisms to respect API rate limits for seamless operation.

## The Grand Vision: Self-Evolving AI

The initial phase lays the groundwork for a much more ambitious goal: **giving the AI the power to introspect, modify, and even regenerate its own components.**

My ultimate plan is to enable the AI to:

1.  **Analyze its own code:** Understand its current set of available components/tools.
2.  **Identify limitations/needs:** Determine what new capabilities it requires to better solve problems or interact with its environment.
3.  **Generate new components:** Write Python code for new `BaseComponent` subclasses based on identified needs, complete with `onload`, `use`, and `destroy` methods.
4.  **Modify existing components:** Improve or adapt the logic of its current tools.
5.  **Restart and integrate:** Trigger a reload of the `ComponentManager` to integrate its newly written or modified components without human intervention.

This project will serve as a foundational experiment to observe:
*   How far can an AI agent push the boundaries of self-modification?
*   What emergent behaviors or problem-solving strategies will it develop?
*   What are the practical and theoretical challenges of creating such a self-evolving system?

## Getting Started

Follow these steps to set up and run the AI agent:

### 1. Project Structure

Ensure your project directory is organized as follows:

```
your_project/
├── .env                    # Environment variables (e.g., API key) - DO NOT COMMIT!
├── .gitignore              # Add `.env` to this file
├── main.py                 # Entry point for the AI chat interface
├── requirements.txt        # List of Python dependencies
└── src/
    ├── base_component.py   # Abstract base class for all components
    ├── manager.py          # Core component discovery and lifecycle manager
    ├── ai_manager.py       # Interfaces ComponentManager with Gemini LLM
    └── components/         # Directory for your custom components (tools)
        ├── my_first_component.py
        ├── logger_component.py
        └── weather_component.py
        └── ... (your AI-generated components might land here!)
```

### 2. Installation

Clone this repository and install the necessary Python dependencies.
Suggested use of `uv-astral` package manager and venv.

```bash
uv sync
```

**`requirements.txt` content:**
```
google-genai
python-dotenv
```

### 3. API Key Configuration

You need a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Create a `.env` file in the root of your project directory (`your_project/.env`) and add your API key:

```
GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
```

**Important:** Add `.env` to your `.gitignore` file to prevent accidentally committing your API key to version control.

### 4. Run the AI Agent

Once setup is complete, simply run the `main.py` script:

```bash
python main.py
```

The AI chat interface will start, and you can begin interacting with it and observing its tool-use capabilities.

## Usage

*   **Chat with the AI:** Type your questions and observe the AI's responses.
*   **Tool Usage:** Ask questions that might require the AI to use one of its internal components (e.g., "What's the weather in London?", "Log a critical error: 'Database offline'").
*   **Observe Tool Output:** The console will show when the AI decides to use a tool, what arguments it provides, and the result returned by your component.
*   **Exit:** Type `exit` or `quit` to end the chat session.

## Components

All custom components must inherit from `src.base_component.BaseComponent` and implement the `onload`, `use`, and `destroy` methods.

Example component structure:

```python
# src/components/my_component.py
from src.base_component import BaseComponent

class MyComponent(BaseComponent):
    def onload(self):
        # Initialization logic
        pass

    def use(self, *args, **kwargs):
        # Main functionality of the component
        # This is what the AI will call
        return "Result of component's operation"

    def destroy(self):
        # Cleanup logic
        pass
```

## Future Development

This project is a living experiment. Key areas for future development towards the self-modifying AI goal include:

*   **Component Generation Logic:** Implementing an AI-driven module that generates Python code for new components.
*   **Code Sandbox/Execution:** A secure environment to test and integrate AI-generated code.
*   **Feedback Loops:** Mechanisms for the AI to evaluate the performance of its tools and iteratively improve them.
*   **Code Editing:** Capabilities for the AI to modify existing component files.
*   **Self-Restart Mechanism:** A controlled way for the AI to trigger a reload of its component manager.

Stay tuned for updates as this fascinating journey unfolds!