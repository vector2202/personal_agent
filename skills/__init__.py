"""
Skills are discovered at runtime by agent.registry, which walks this package
for folders containing a SKILL.md. There is no central export list to keep in
sync — adding a skill means adding a folder, nothing else.
"""
from skills.base import BaseSkill

__all__ = ["BaseSkill"]
