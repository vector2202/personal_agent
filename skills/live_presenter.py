import time
import os
import json
from enum import Enum
from typing import Type, Dict, Any, List, Generator
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class EventType(str, Enum):
    THINKING = "THINKING"
    SKILL_START = "SKILL_START"
    SKILL_END = "SKILL_END"
    EVAL_SCORE = "EVAL_SCORE"
    EXPENSE_LOGGED = "EXPENSE_LOGGED"
    SYSTEM_ALERT = "SYSTEM_ALERT"

class LivePresenterInput(BaseModel):
    event_type: EventType = Field(..., description="The type of event to broadcast to the UI HUD.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured event data to send to the UI.")

class LiveSystemPresenter(BaseSkill):
    """
    UI Bridge Skill. Emits structured telemetry events to connected dashboards (SSE / WebSocket).
    Maintains an in-memory event buffer and persists events to logs/events.jsonl for replay.
    """

    _event_buffer: List[Dict[str, Any]] = []
    LOG_FILE = "logs/events.jsonl"

    def __init__(self):
        os.makedirs("logs", exist_ok=True)

    @property
    def name(self) -> str:
        return "live_system_presenter"

    @property
    def description(self) -> str:
        return "Emits real-time state transitions, thoughts, and skill outputs to the user interface HUD."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return LivePresenterInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)
        
        event = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": data.event_type.value,
            "payload": data.payload
        }
        
        # Append to live buffer (capped at last 200 events)
        LiveSystemPresenter._event_buffer.append(event)
        if len(LiveSystemPresenter._event_buffer) > 200:
            LiveSystemPresenter._event_buffer.pop(0)

        # Append to persistent JSONL log
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass

        return {
            "success": True,
            "status": "EMITTED",
            "event": event
        }

    @classmethod
    def get_latest_events(cls, count: int = 20) -> List[Dict[str, Any]]:
        """Returns the latest events in chronological order."""
        return cls._event_buffer[-count:]

    @classmethod
    def format_sse(cls, event: Dict[str, Any]) -> str:
        """Helper to format an event as a Server-Sent Events (SSE) data string."""
        return f"event: {event.get('event_type')}\ndata: {json.dumps(event)}\n\n"
