# Personal AI Agent

Building a Personal AI Agent :)


## Structure

*   `agent/`: ReAct loop control with system instructions.
*   `skills/`: Agent modules with strict input/output schemas (Pydantic).
*   `evals/`: Automated test suite to measure accuracy and performance.
*   `ui/`: Interface to interact with and monitor the agent.

## Installation

1.  Create a virtual environment and install the dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  Create a `.env` file in the root directory and add your API key:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```

3.  Run the basic agent prototype in the console:
    ```bash
    python main.py
    ```
