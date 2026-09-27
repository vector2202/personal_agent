import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from agent.approvals import ApprovalStore, CLIGate
from agent.core import AgentCore
from agent.dispatcher import Dispatcher
from agent.registry import SkillRegistry

load_dotenv()

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(ROOT, "logs", "events.jsonl")

# Every path a skill touches is passed in explicitly — nothing defaults to the
# current working directory.
SKILL_CONFIG = {
    "expense_tracker": {"db_path": os.path.join(ROOT, "expenses.db")},
    "graph_rag_memory_indexer": {"storage_path": os.path.join(ROOT, "memory_graph.json")},
    "file_access": {"workspace_root": ROOT},
}


def make_emitter(path):
    """Structured telemetry, one JSON object per line. Separate channel from
    the human-readable prints in the loop."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    def emit(event, payload):
        record = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **payload}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    return emit


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Error] GEMINI_API_KEY environment variable not found in environment or .env file.")
        print("Please create a .env file in the root directory with: GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)

    registry = SkillRegistry(os.path.join(ROOT, "skills"), config=SKILL_CONFIG).discover()
    if not len(registry):
        print("[Error] No skills found. A skill needs its own folder with a SKILL.md.")
        sys.exit(1)

    gate = CLIGate(ApprovalStore(path=os.path.join(ROOT, "approvals.json")))
    dispatcher = Dispatcher(registry, gate=gate, emit=make_emitter(LOG_PATH))
    agent = AgentCore(api_key=api_key, registry=registry, dispatcher=dispatcher)

    print("\n=======================================================")
    print("         Personal AI Agent (ReAct CLI Prototype)        ")
    print("=======================================================")
    print(f"Skills loaded : {', '.join(registry.names())}")
    print(f"Telemetry     : {os.path.relpath(LOG_PATH, ROOT)}")
    print("Type your query (or 'exit' / 'q' to quit):")

    while True:
        try:
            prompt = input("\nYou > ")
            if prompt.strip().lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            if not prompt.strip():
                continue

            response = agent.execute(prompt)
            print(f"\nAgent > {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[System Error] Unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
