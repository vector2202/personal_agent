# Personal AI Agent

A modular, deterministic, and reliable personal AI agent engineered from scratch with production-grade standards. Built with Python 3.11+, Pydantic v2 strict schemas, and the official Google GenAI SDK (`google-genai`).

---

## Vision & Core Objectives

Unlike generic AI wrappers or brittle chat bots, this system is designed as an autonomous, observable, and extensible personal assistant:
* **Strict Type Safety & Schemas**: Every skill enforces validated inputs and outputs using Pydantic models.
* **Deterministic Execution**: Local Python tools perform actual actions (file I/O, SQLite operations, AST parsing) with zero math or logic hallucinations.
* **Privacy & Local Ownership**: Financial data, knowledge graphs, and execution telemetry remain 100% local on your machine.
* **Autonomous Reasoning Loop**: Implements a ReAct (Reason + Act) loop with dynamic JSON tool calling and step-by-step observation cycles.
* **Multilingual Flexibility**: Native support for prompts in English, Spanish, or any language with automatic schema alignment.

---

## Architecture Overview

```
                                +-----------------------------------+
                                |            User Input             |
                                |     (CLI / Web UI Dashboard)      |
                                +-----------------+-----------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
| AGENT CORE (ReAct Loop)                                                                           |
|                                                                                                   |
|  1. Context Assembly  --->  2. Gemini Flash  --->  3. JSON Thought & Action Parsing               |
|            ^                                                      |                               |
|            |                                                      v                               |
|            +----------------- [ Tool Observation ] <--- 4. Skill Dispatcher                       |
+-------------------------------------------------------------------|-------------------------------+
                                                                    |
                                                                    v
+-------------------------------------------------------------------+-------------------------------+
| SKILLS LAYER (13 Modular Tools)                                                                   |
|                                                                                                   |
|  [Finance]           [Dev & Code]             [Career & Memory]      [Safety & System]            |
|  - Expense Tracker   - File Access            - GitHub Portfolio     - Secure Terminal            |
|                      - AST Repo Digest        - GraphRAG Memory      - Human Intervention         |
|                      - Diff Applier           - Live UI Presenter    - Health Monitor             |
|                      - Test Generator         - Eval Benchmark       - Web Doc Retriever          |
+---------------------------------------------------------------------------------------------------+
```

---

## Directory Structure

```text
personal_agent/
├── agent/
│   ├── __init__.py
│   └── core.py                 # Core ReAct control loop & GenAI client integration
├── skills/
│   ├── __init__.py             # Central skill export registry
│   ├── base.py                 # BaseSkill abstract class with Pydantic validation
│   ├── expense_tracker.py      # SQLite-backed expense tracking & analytics
│   ├── file_access.py          # Sandboxed workspace reading, writing & listing
│   ├── secure_terminal.py      # Sandboxed subshell runner with command timeouts
│   ├── repo_digest.py          # Zero-token AST inspection of Python files
│   ├── diff_applier.py         # Surgical block search-and-replace code editor
│   ├── test_generator.py       # Automated pytest suite generator via AST
│   ├── graph_memory.py         # GraphRAG knowledge memory (BFS pathfinder & queries)
│   ├── live_presenter.py       # Real-time UI HUD telemetry & SSE formatters
│   ├── eval_benchmark.py       # Automated live benchmark runner for tool accuracy
│   ├── health_monitor.py       # Local machine CPU, RAM, and Disk telemetry
│   ├── web_retriever.py        # Web documentation scraper with HTML sanitization
│   ├── human_intervention.py   # Human-in-the-Loop interactive approval gate
│   └── github_portfolio.py     # Live GitHub repository and career portfolio viewer
├── logs/                       # Telemetry logs and events (e.g. events.jsonl)
├── tests/                      # Unit and integration test suites
├── expenses.db                 # Local SQLite database for expenses (generated on use)
├── main.py                     # Interactive CLI entrypoint
├── requirements.txt            # Python dependencies (google-genai, pydantic, etc.)
└── README.md                   # System documentation and architecture guide
```

---

## Available Skills (13 Plug-and-Play Modules)

| Skill Name | Class | Primary Purpose |
| :--- | :--- | :--- |
| **`expense_tracker`** | `ExpenseTrackerSkill` | Logs expenses to local SQLite and performs deterministic category breakdowns and savings analysis. |
| **`file_access`** | `FileAccessSkill` | Reads, writes, and lists workspace files with directory traversal guardrails. |
| **`secure_terminal`** | `SecureTerminalSkill` | Runs shell commands safely with hard timeout boundaries and denylist protection. |
| **`repo_architecture_digest`** | `RepoArchitectureDigest` | Extracts classes, functions, and docstrings using Python's `ast` without consuming LLM tokens. |
| **`targeted_diff_applier`** | `TargetedDiffApplier` | Applies precision block diffs to files without risking whole-file corruption. |
| **`automated_test_generator`** | `AutomatedTestGenerator` | Generates complete, runnable pytest test suites based on AST signatures. |
| **`graph_rag_memory_indexer`** | `GraphRAGMemoryIndexer` | Stores and traverses knowledge triples (nodes/edges) with shortest-path BFS exploration. |
| **`live_system_presenter`** | `LiveSystemPresenter` | Streams structured telemetry events (`THINKING`, `SKILL_START`, `SKILL_END`) over SSE/WebSockets. |
| **`automated_eval_benchmark`** | `AutomatedEvalBenchmark` | Evaluates live model tool accuracy, argument matching, and latency in milliseconds. |
| **`system_health_monitor`** | `SystemHealthMonitor` | Reports CPU count, OS details, and storage/RAM usage. |
| **`web_doc_retriever`** | `WebDocRetriever` | Fetches live web pages and documentation, stripping HTML tags to prevent stale knowledge. |
| **`human_intervention_requester`** | `HumanInterventionRequester`| Human-in-the-Loop interceptor to request developer authorization for sensitive actions. |
| **`github_portfolio_discoverer`** | `GitHubPortfolioDiscoverer` | Connects to the GitHub API to discover public repos, topics, and star metrics. |

---

## Setup & Getting Started

### 1. Prerequisites
* Python 3.11 or higher
* Google AI Studio API Key (Free tier works seamlessly)

### 2. Installation
Clone the repository and set up a virtual environment:

```bash
git clone <your-repo-url>
cd personal_agent

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```

### 4. Running the Agent
Start the interactive CLI:

```bash
python main.py
```

---

## Usage Examples

### 1. Expense Tracking & Financial Analysis
Prompt the agent in English or Spanish:
* *"spent 45 on an amazon toy for my nephew"*
* *"gasté 180 pesos en uber al aeropuerto"*
* *"where did I spend my money and how can I save?"*

The agent calls `ExpenseTrackerSkill`, persists records to `expenses.db`, and aggregates spending by category.

### 2. Registering Additional Skills
Activating any of the other 12 skills is a single line in `main.py`:

```python
from agent.core import AgentCore
from skills import ExpenseTrackerSkill, FileAccessSkill, RepoArchitectureDigest

agent = AgentCore(api_key=api_key)

# Register plug-and-play skills
agent.register_skill(ExpenseTrackerSkill())
agent.register_skill(FileAccessSkill())
agent.register_skill(RepoArchitectureDigest())
```

---

## Next Milestones on the Roadmap

1. **Context & State Management (`agent/memory.py`)**: Persistent session history across CLI restarts and automatic observation summarization.
2. **Loop Guardrails & Reflection**: Loop repetition detection and self-healing when tools return errors.
3. **Dynamic Tool Retrieval**: Intent-based tool routing to prevent attention dilution when using 10+ skills simultaneously.
4. **Lightweight Dashboard (`/ui`)**: Fast web UI displaying the Parker HUD, live SSE logs, and interactive approval modals.
