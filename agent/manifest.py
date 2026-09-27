"""
Parses SKILL.md and binds it to the Python skill class.

Markdown owns prose, Python owns types — the schema is never duplicated here.
The manifest carries only what the dispatcher, the policy gate and the prompt
builder need, plus the usage body that is loaded lazily.
"""
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import yaml
from pydantic import BaseModel

from agent.capabilities import Capability


class ManifestError(Exception):
    """Raised at load time — a broken manifest should never reach the loop."""


@dataclass(frozen=True)
class SkillManifest:
    name: str
    description: str
    category: str
    capabilities: Set[Capability]
    body: str
    action_field: Optional[str] = None
    capability_overrides: Dict[str, Set[Capability]] = field(default_factory=dict)

    def capabilities_for(self, params: Any) -> Set[Capability]:
        """Capabilities this specific call needs, given already-validated input.

        Never call this with raw model output — risk decisions must be made on
        parsed input, or a malformed action value could dodge the gate.
        """
        if not self.action_field:
            return self.capabilities

        value = getattr(params, self.action_field, None)
        if value is None and isinstance(params, dict):
            value = params.get(self.action_field)
        if hasattr(value, "value"):  # unwrap enum members
            value = value.value

        # Fail closed: an action with no explicit override inherits the
        # skill-level default, which is the more privileged set.
        return self.capability_overrides.get(str(value), self.capabilities)


def _parse_capabilities(raw: Any, where: str) -> Set[Capability]:
    if raw is None:
        return set()
    if not isinstance(raw, list):
        raise ManifestError(f"{where}: capabilities must be a list, got {type(raw).__name__}")
    out = set()
    for item in raw:
        try:
            out.add(Capability(item))
        except ValueError:
            known = ", ".join(c.value for c in Capability)
            raise ManifestError(f"{where}: unknown capability '{item}'. Known: {known}")
    return out


def _split_frontmatter(text: str, path: str) -> tuple[str, str]:
    if not text.startswith("---"):
        raise ManifestError(f"{path}: must begin with a '---' frontmatter block")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ManifestError(f"{path}: frontmatter block is not closed with '---'")
    return parts[1], parts[2].strip()


def load_manifest(skill_dir: str) -> SkillManifest:
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(path):
        raise ManifestError(f"{skill_dir}: no SKILL.md")

    with open(path, encoding="utf-8") as f:
        front, body = _split_frontmatter(f.read(), path)

    try:
        meta = yaml.safe_load(front) or {}
    except yaml.YAMLError as e:
        raise ManifestError(f"{path}: invalid YAML frontmatter — {e}")

    for required in ("name", "description", "category"):
        if not meta.get(required):
            raise ManifestError(f"{path}: missing required field '{required}'")

    overrides = {
        str(action): _parse_capabilities(caps, f"{path} (override '{action}')")
        for action, caps in (meta.get("capability_overrides") or {}).items()
    }

    if overrides and not meta.get("action_field"):
        raise ManifestError(
            f"{path}: capability_overrides needs 'action_field' naming the input "
            f"field that selects the action"
        )

    return SkillManifest(
        name=meta["name"],
        description=meta["description"].strip(),
        category=meta["category"],
        capabilities=_parse_capabilities(meta.get("capabilities"), path),
        body=body,
        action_field=meta.get("action_field"),
        capability_overrides=overrides,
    )


def bind(manifest: SkillManifest, skill: Any) -> None:
    """Drift guard — the manifest and the class must agree, or we fail at
    startup rather than silently dispatching on stale metadata."""
    if manifest.name != skill.name:
        raise ManifestError(
            f"name mismatch: SKILL.md says '{manifest.name}', "
            f"{type(skill).__name__}.name says '{skill.name}'"
        )

    schema = skill.input_schema
    if not (isinstance(schema, type) and issubclass(schema, BaseModel)):
        raise ManifestError(f"{skill.name}: input_schema is not a Pydantic model")

    if manifest.action_field and manifest.action_field not in schema.model_fields:
        raise ManifestError(
            f"{skill.name}: action_field '{manifest.action_field}' is not a field "
            f"of {schema.__name__}"
        )
