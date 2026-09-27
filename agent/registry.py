"""
Discovers skill folders, binds each manifest to its class, and serves the
progressive-disclosure tiers the prompt builder asks for.

Everything that can be wrong with a skill — missing manifest, name drift,
unknown capability, two skills claiming one name — is caught here, at startup,
rather than surfacing mid-conversation as a confusing tool failure.
"""
import importlib
import inspect
import json
import os
from typing import Any, Dict, Iterator, List, Optional

from agent.manifest import ManifestError, SkillManifest, bind, load_manifest
from skills.base import BaseSkill


class RegisteredSkill:
    def __init__(self, manifest: SkillManifest, skill: BaseSkill):
        self.manifest = manifest
        self.skill = skill

    @property
    def name(self) -> str:
        return self.manifest.name

    def schema_json(self) -> Dict[str, Any]:
        return self.skill.input_schema.model_json_schema()


class SkillRegistry:
    """Config is passed in per skill — nothing here reads a hardcoded path."""

    def __init__(self, skills_dir: str, config: Optional[Dict[str, Dict[str, Any]]] = None):
        self.skills_dir = os.path.abspath(skills_dir)
        self.config = config or {}
        self._skills: Dict[str, RegisteredSkill] = {}

    def discover(self) -> "SkillRegistry":
        for entry in sorted(os.scandir(self.skills_dir), key=lambda e: e.name):
            if not entry.is_dir() or entry.name.startswith(("_", ".")):
                continue
            if not os.path.exists(os.path.join(entry.path, "SKILL.md")):
                continue
            self._load_one(entry.name, entry.path)
        return self

    def _load_one(self, folder: str, path: str) -> None:
        manifest = load_manifest(path)

        module = importlib.import_module(f"skills.{folder}.skill")
        classes = [
            obj
            for _, obj in inspect.getmembers(module, inspect.isclass)
            if issubclass(obj, BaseSkill) and obj is not BaseSkill
            and obj.__module__ == module.__name__
        ]
        if len(classes) != 1:
            raise ManifestError(
                f"{path}: expected exactly one BaseSkill subclass in skill.py, "
                f"found {len(classes)}"
            )

        skill = classes[0](**self.config.get(manifest.name, {}))
        bind(manifest, skill)

        if manifest.name in self._skills:
            raise ManifestError(f"duplicate skill name '{manifest.name}' (folder '{folder}')")
        self._skills[manifest.name] = RegisteredSkill(manifest, skill)

    # --- progressive disclosure -------------------------------------------

    def catalog(self) -> str:
        """Tier 1 — always in context. Names and one-liners only, no schemas."""
        return "\n".join(
            f"- `{r.name}`: {r.manifest.description}" for r in self.values()
        )

    def detail(self, name: str) -> str:
        """Tier 2+3 — loaded once a skill is actually chosen."""
        r = self[name]
        return (
            f"# Tool: {r.name}\n"
            f"{r.manifest.description}\n\n"
            f"## Input schema (JSON)\n{json.dumps(r.schema_json())}\n\n"
            f"{r.manifest.body}"
        )

    # --- mapping-ish accessors --------------------------------------------

    def __getitem__(self, name: str) -> RegisteredSkill:
        if name not in self._skills:
            raise KeyError(name)
        return self._skills[name]

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def __len__(self) -> int:
        return len(self._skills)

    def names(self) -> List[str]:
        return list(self._skills)

    def values(self) -> Iterator[RegisteredSkill]:
        return iter(self._skills.values())
