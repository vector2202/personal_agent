from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class HumanInterventionInput(BaseModel):
    reason: str = Field(..., description="The explicit reason human approval/input is requested.")
    sensitive_action: str = Field(..., description="Description of the action or command the agent wants to perform.")
    payload_to_approve: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Detailed parameters for the proposed action.")

class HumanInterventionRequester(BaseSkill):
    """
    Human-in-the-Loop (HITL) Interceptor.
    Pauses autonomous loop execution to request approval from the developer via the CLI/UI.
    """

    @property
    def name(self) -> str:
        return "human_intervention_requester"

    @property
    def description(self) -> str:
        return "Pauses autonomous execution and requests user approval or input for sensitive operations."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return HumanInterventionInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)

        print("\n" + "=" * 55)
        print(" [HUMAN-IN-THE-LOOP INTERVENTION REQUIRED] ")
        print("=" * 55)
        print(f"Reason: {data.reason}")
        print(f"Sensitive Action: {data.sensitive_action}")
        if data.payload_to_approve:
            print(f"Proposed Parameters: {data.payload_to_approve}")
        print("-" * 55)

        try:
            user_decision = input("Do you approve this action? (y/n/feedback): ").strip()
            if user_decision.lower() in ["y", "yes"]:
                return {
                    "success": True,
                    "approved": True,
                    "feedback": None
                }
            elif user_decision.lower() in ["n", "no"]:
                return {
                    "success": True,
                    "approved": False,
                    "feedback": "Action rejected by user."
                }
            else:
                return {
                    "success": True,
                    "approved": False,
                    "feedback": f"User denied with instructions: {user_decision}"
                }
        except (EOFError, KeyboardInterrupt):
            return {
                "success": False,
                "approved": False,
                "error": "Intervention session aborted by user signal."
            }
