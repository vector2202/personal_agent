import time
from enum import Enum
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class EventType(str, Enum):
    THINKING = "THINKING"
    SKILL_START = "SKILL_START"
    SKILL_END = "SKILL_END"
    EVAL_SCORE = "EVAL_SCORE"
    SYSTEM_ALERT = "SYSTEM_ALERT"

class LivePresenterInput(BaseModel):
    event_type: EventType = Field(..., description="The type of event to broadcast to the UI HUD.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured event data to send to the UI.")

class LiveSystemPresenter(BaseSkill):
    """
    UI Bridge Skill. Emits structured telemetry events to connected dashboards (SSE / WebSocket).
    Maintains an in-memory event buffer for real-time observability.
    """

    _event_buffer: List[Dict[str, Any]] = []

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
            "event_type": data.event_type.value,
            "payload": data.payload
        }
        
        # Append to buffer (capped at last 100 events)
        LiveSystemPresenter._event_buffer.append(event)
        if len(LiveSystemPresenter._event_buffer) > 100:
            LiveSystemPresenter._event_buffer.pop(0)

        # In production this also triggers an SSE/WebSocket broadcast
        return {
            "success": True,
            "status": "EMITTED",
            "event": event
        }

    @classmethod
    def get_latest_events(cls, count: int = 10) -> List[Dict[str, Any]]:
        """Utility method to inspect the live event buffer from API endpoints."""
        return cls._event_buffer[-count:]
