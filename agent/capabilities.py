"""
Capabilities a skill declares, and the policies derived from them.

A skill declares what it *needs* (an objective fact about the code), not how
risky it *is* (a subjective judgment). Policy and timeouts are derived here,
centrally, so changing how a capability is treated is a one-line edit rather
than a re-labelling of every skill.
"""
from enum import Enum
from typing import Iterable


class Capability(str, Enum):
    DB_WRITE = "db_write"
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"    # creates new files
    FILESYSTEM_MODIFY = "filesystem_modify"  # rewrites existing ones — can destroy work
    NETWORK = "network"
    SUBPROCESS = "subprocess"


class Decision(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    ASK_ALWAYS = "ask_always"


_ORDER = {Decision.ALLOW: 0, Decision.ASK: 1, Decision.ASK_ALWAYS: 2}

_POLICY = {
    Capability.FILESYSTEM_READ: Decision.ALLOW,
    Capability.NETWORK: Decision.ALLOW,
    Capability.DB_WRITE: Decision.ASK,
    Capability.FILESYSTEM_WRITE: Decision.ASK,
    Capability.FILESYSTEM_MODIFY: Decision.ASK,
    Capability.SUBPROCESS: Decision.ASK_ALWAYS,
}

# Whether an approval may outlive the session. Orthogonal to _POLICY: the
# decision says whether to ask, this says how long a "yes" is good for.
# Overwriting existing files is recoverable enough to wave through for one
# session, never safe enough to bless forever from a config file.
_NEVER_PERSIST = {Capability.SUBPROCESS, Capability.FILESYSTEM_MODIFY}

_TIMEOUTS = {
    Capability.FILESYSTEM_READ: 10,
    Capability.FILESYSTEM_WRITE: 10,
    Capability.FILESYSTEM_MODIFY: 10,
    Capability.DB_WRITE: 10,
    Capability.NETWORK: 30,
    Capability.SUBPROCESS: 120,
}

LOCAL_TIMEOUT = 10


def decide(capabilities: Iterable[Capability]) -> Decision:
    """Most restrictive capability wins."""
    return max(
        (_POLICY[c] for c in capabilities),
        key=lambda d: _ORDER[d],
        default=Decision.ALLOW,
    )


def timeout_for(capabilities: Iterable[Capability]) -> int:
    """Longest applicable timeout wins — a call doing both network and disk
    needs room for the slower of the two."""
    return max((_TIMEOUTS[c] for c in capabilities), default=LOCAL_TIMEOUT)


def is_session_rememberable(capabilities: Iterable[Capability]) -> bool:
    """Whether a 'yes' can be reused for the rest of this session."""
    return decide(capabilities) is not Decision.ASK_ALWAYS


def is_persistable(capabilities: Iterable[Capability]) -> bool:
    """Whether a 'yes' may be written to the on-disk allowlist and outlive
    the session."""
    caps = set(capabilities)
    return is_session_rememberable(caps) and not (caps & _NEVER_PERSIST)
