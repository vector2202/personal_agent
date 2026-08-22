from abc import ABC, abstractmethod
from typing import Type, Any, Dict
from pydantic import BaseModel

class BaseSkill(ABC):
    """
    Abstract base class for all agent skills.
    Ensures a strict input/output contract utilizing Pydantic.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name of the skill (e.g., 'calculator')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Clear and detailed description of what the skill does.
        Crucial for the LLM to decide when and how to invoke it.
        """
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Type[BaseModel]:
        """Pydantic model class validating the input arguments for this skill."""
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Any:
        """
        Execution logic of the skill.
        Must validate input parameters against the input_schema before running.
        """
        pass
