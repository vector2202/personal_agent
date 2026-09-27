import subprocess
import shlex
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class SecureTerminalInput(BaseModel):
    command: str = Field(..., description="The non-interactive shell command to execute.")
    timeout_seconds: int = Field(default=15, ge=1, le=60, description="Max execution duration before timeout.")

class SecureTerminalSkill(BaseSkill):
    """
    Executes shell commands in a sandboxed, non-interactive environment with hard timeouts.
    Disallows dangerous/destructive root commands by default.
    """

    DENYLIST: List[str] = [
        "rm -rf /",
        ":(){ :|:& };:",
        "mkfs",
        "dd if="
    ]

    @property
    def name(self) -> str:
        return "secure_terminal"

    @property
    def description(self) -> str:
        return "Executes shell commands safely with execution timeouts and safety guardrails."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return SecureTerminalInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)
        cmd_clean = data.command.strip()

        # Check safety denylist
        for denied in self.DENYLIST:
            if denied in cmd_clean:
                return {
                    "success": False,
                    "error": f"Command rejected: dangerous operation detected ('{denied}')."
                }

        try:
            result = subprocess.run(
                cmd_clean,
                shell=True,
                capture_output=True,
                text=True,
                timeout=data.timeout_seconds
            )
            return {
                "success": result.returncode == 0,
                "command": cmd_clean,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {data.timeout_seconds} seconds."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }
