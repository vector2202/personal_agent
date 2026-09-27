"""
The tool-call pipeline: resolve -> validate -> assess -> gate -> execute ->
observe, with a telemetry event at every stage.

Two invariants hold this together:

1. **Dispatch never raises.** Every failure becomes an observation the model
   can read and correct against. The agent cannot heal from what it cannot see.

2. **Risk is assessed only on validated input.** A malformed action value must
   never reach the gate — parse first, decide second, act third.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

from pydantic import ValidationError

from agent.approvals import ApprovalRequest, Gate, AutoApproveGate
from agent.capabilities import timeout_for
from agent.registry import SkillRegistry

MAX_OBSERVATION_CHARS = 4000
HEAD_RATIO = 0.6


class Outcome(str, Enum):
    OK = "ok"
    UNKNOWN_SKILL = "unknown_skill"
    INVALID_INPUT = "invalid_input"
    DENIED = "denied"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class DispatchResult:
    outcome: Outcome
    observation: str
    duration_ms: int = 0
    truncated: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.outcome is Outcome.OK


def truncate(text: str, limit: int = MAX_OBSERVATION_CHARS) -> tuple[str, bool]:
    """Head + tail, eliding the middle — a file's shape stays legible.

    TODO: the real destination is spill-to-disk (write the full result to a
    file and hand the model its path) so nothing is permanently lost.
    """
    if len(text) <= limit:
        return text, False
    head = int(limit * HEAD_RATIO)
    tail = limit - head
    elided = len(text) - limit
    return f"{text[:head]}\n\n...[{elided} characters elided]...\n\n{text[-tail:]}", True


class Dispatcher:
    def __init__(
        self,
        registry: SkillRegistry,
        gate: Optional[Gate] = None,
        emit: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        max_observation_chars: int = MAX_OBSERVATION_CHARS,
    ):
        self.registry = registry
        self.gate = gate or AutoApproveGate()
        self.emit = emit or (lambda event, payload: None)
        self.max_observation_chars = max_observation_chars
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="skill")

    def dispatch(self, skill_name: str, arguments: Optional[Dict[str, Any]]) -> DispatchResult:
        started = time.monotonic()
        arguments = arguments or {}
        self.emit("SKILL_START", {"skill": skill_name, "arguments": arguments})

        # 1. resolve
        if skill_name not in self.registry:
            return self._done(
                Outcome.UNKNOWN_SKILL,
                f"Error: no skill named '{skill_name}'. Available skills: "
                f"{', '.join(self.registry.names())}.",
                started,
                skill_name,
            )

        registered = self.registry[skill_name]
        manifest = registered.manifest

        # 2. validate — before any risk decision is made on this input
        try:
            params = registered.skill.input_schema(**arguments)
        except ValidationError as e:
            return self._done(
                Outcome.INVALID_INPUT,
                f"Error: invalid arguments for '{skill_name}'. "
                f"{self._explain(e)} Correct the arguments and try again.",
                started,
                skill_name,
            )
        except TypeError as e:
            return self._done(
                Outcome.INVALID_INPUT,
                f"Error: invalid arguments for '{skill_name}': {e}",
                started,
                skill_name,
            )

        # 3. assess
        capabilities = manifest.capabilities_for(params)
        action = None
        if manifest.action_field:
            raw = getattr(params, manifest.action_field, None)
            action = getattr(raw, "value", raw)
            action = str(action) if action is not None else None

        # 4. gate
        request = ApprovalRequest(
            skill=skill_name,
            action=action,
            capabilities=capabilities,
            arguments=arguments,
        )
        verdict = self.gate.check(request)
        if not verdict.approved:
            reason = verdict.feedback or "No reason given."
            return self._done(
                Outcome.DENIED,
                f"Action '{skill_name}' was not permitted. {reason} "
                f"Do not retry the same call — find another approach or ask the user.",
                started,
                skill_name,
                capabilities=capabilities,
            )

        # 5. execute, under the timeout its capabilities earn it
        limit = timeout_for(capabilities)
        future = self._pool.submit(registered.skill.execute, arguments)
        try:
            raw_result = future.result(timeout=limit)
        except FutureTimeout:
            # NOTE: Python cannot cancel a running thread — the skill keeps
            # going in the background. Real cancellation needs subprocess
            # isolation, which is deferred along with the concurrency work.
            future.cancel()
            return self._done(
                Outcome.TIMEOUT,
                f"Error: '{skill_name}' exceeded its {limit}s timeout and was abandoned.",
                started,
                skill_name,
                capabilities=capabilities,
            )
        except Exception as e:
            return self._done(
                Outcome.ERROR,
                f"Error: '{skill_name}' failed with {type(e).__name__}: {e}",
                started,
                skill_name,
                capabilities=capabilities,
            )

        # 6. observe
        try:
            rendered = json.dumps(raw_result, default=str)
        except (TypeError, ValueError):
            rendered = str(raw_result)
        observation, was_truncated = truncate(rendered, self.max_observation_chars)

        return self._done(
            Outcome.OK,
            observation,
            started,
            skill_name,
            truncated=was_truncated,
            capabilities=capabilities,
        )

    @staticmethod
    def _explain(error: ValidationError) -> str:
        """Pydantic's full dump is noisy; the model needs the field and the
        problem, not a stack of URLs."""
        parts = []
        for err in error.errors()[:5]:
            loc = ".".join(str(p) for p in err["loc"]) or "(root)"
            parts.append(f"'{loc}': {err['msg']}")
        return "; ".join(parts) + "."

    def _done(
        self,
        outcome: Outcome,
        observation: str,
        started: float,
        skill_name: str,
        truncated: bool = False,
        capabilities=None,
    ) -> DispatchResult:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = DispatchResult(
            outcome=outcome,
            observation=observation,
            duration_ms=duration_ms,
            truncated=truncated,
            meta={
                "skill": skill_name,
                "capabilities": sorted(c.value for c in capabilities) if capabilities else [],
            },
        )
        self.emit(
            "SKILL_END",
            {
                "skill": skill_name,
                "outcome": outcome.value,
                "duration_ms": duration_ms,
                "truncated": truncated,
            },
        )
        return result
