"""
The approval gate — enforced in code, never left to the model's discretion.

A 'yes' is scoped three ways, decided in agent.capabilities:
  ALLOW        never asks
  ASK          asks once, may be remembered for the session or persisted
  ASK_ALWAYS   asks every single time, never cached

Persistence is deliberately a plain readable file: a permission you cannot
find is a permission you cannot revoke.
"""
import json
import os
from dataclasses import dataclass
from typing import Optional, Set

from agent.capabilities import (
    Capability,
    Decision,
    decide,
    is_persistable,
    is_session_rememberable,
)


@dataclass(frozen=True)
class ApprovalRequest:
    skill: str
    action: Optional[str]
    capabilities: Set[Capability]
    arguments: dict

    @property
    def key(self) -> str:
        """What a remembered 'yes' actually covers — approving LOG must not
        silently approve a DELETE added later."""
        return f"{self.skill}:{self.action}" if self.action else self.skill


@dataclass(frozen=True)
class ApprovalOutcome:
    approved: bool
    feedback: Optional[str] = None
    remember_session: bool = False
    remember_forever: bool = False


class ApprovalStore:
    def __init__(self, path: Optional[str] = None):
        self.path = path
        self._session: Set[str] = set()
        self._persisted: Set[str] = set()
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self._persisted = set(json.load(f).get("always_allow", []))
            except (json.JSONDecodeError, OSError):
                self._persisted = set()

    def is_remembered(self, key: str) -> bool:
        return key in self._session or key in self._persisted

    def remember_session(self, key: str) -> None:
        self._session.add(key)

    def remember_forever(self, key: str) -> None:
        self._persisted.add(key)
        self._session.add(key)
        if not self.path:
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"always_allow": sorted(self._persisted)}, f, indent=2)


class Gate:
    """Decides whether a validated call may run. Subclass to change how the
    question gets asked — the policy logic stays here."""

    def __init__(self, store: Optional[ApprovalStore] = None):
        self.store = store or ApprovalStore()

    def check(self, request: ApprovalRequest) -> ApprovalOutcome:
        decision = decide(request.capabilities)

        if decision is Decision.ALLOW:
            return ApprovalOutcome(approved=True)

        if decision is not Decision.ASK_ALWAYS and self.store.is_remembered(request.key):
            return ApprovalOutcome(approved=True)

        outcome = self.ask(request, decision)

        if outcome.approved:
            if outcome.remember_forever and is_persistable(request.capabilities):
                self.store.remember_forever(request.key)
            elif outcome.remember_session and is_session_rememberable(request.capabilities):
                self.store.remember_session(request.key)
        return outcome

    def ask(self, request: ApprovalRequest, decision: Decision) -> ApprovalOutcome:
        raise NotImplementedError


class AutoApproveGate(Gate):
    """For tests and unattended runs. Never prompts."""

    def ask(self, request: ApprovalRequest, decision: Decision) -> ApprovalOutcome:
        return ApprovalOutcome(approved=True)


class DenyAllGate(Gate):
    """For evals — anything needing approval is refused rather than executed."""

    def ask(self, request: ApprovalRequest, decision: Decision) -> ApprovalOutcome:
        return ApprovalOutcome(
            approved=False,
            feedback="Running in read-only mode; this action was not performed.",
        )


class CLIGate(Gate):
    def ask(self, request: ApprovalRequest, decision: Decision) -> ApprovalOutcome:
        caps = ", ".join(sorted(c.value for c in request.capabilities)) or "none"
        print("\n" + "=" * 58)
        print("  APPROVAL REQUIRED")
        print("=" * 58)
        print(f"  skill        : {request.skill}")
        if request.action:
            print(f"  action       : {request.action}")
        print(f"  capabilities : {caps}")
        print(f"  arguments    : {request.arguments}")
        if decision is Decision.ASK_ALWAYS:
            print("  note         : this one is never remembered")
        print("-" * 58)

        choices = "[y]es / [n]o"
        if decision is not Decision.ASK_ALWAYS:
            choices += " / [s]ession"
            if is_persistable(request.capabilities):
                choices += " / [a]lways"

        try:
            answer = input(f"  Approve? {choices}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return ApprovalOutcome(approved=False, feedback="Approval aborted by user.")

        if answer in ("y", "yes"):
            return ApprovalOutcome(approved=True)
        if answer in ("s", "session"):
            return ApprovalOutcome(approved=True, remember_session=True)
        if answer in ("a", "always"):
            return ApprovalOutcome(approved=True, remember_forever=True)
        if answer in ("n", "no", ""):
            return ApprovalOutcome(approved=False, feedback="User declined this action.")
        # Anything else is treated as instructions, not a yes.
        return ApprovalOutcome(approved=False, feedback=f"User declined: {answer}")
