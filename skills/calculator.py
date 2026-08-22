from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class CalculatorInput(BaseModel):
    operation: str = Field(
        ..., 
        description="The mathematical operation to perform. Options: '+', '-', '*', '/'"
    )
    a: float = Field(..., description="The first number/operand")
    b: float = Field(..., description="The second number/operand")

class CalculatorSkill(BaseSkill):
    """
    Deterministic skill to solve basic mathematical operations.
    Demonstrates how to enforce correct datatypes and prevent math hallucinations.
    """
    
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Solves basic mathematical operations like addition, subtraction, multiplication, and division."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return CalculatorInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Validate and parse parameters using the Pydantic schema
        validated_data = self.input_schema(**params)
        
        op = validated_data.operation
        a = validated_data.a
        b = validated_data.b
        
        try:
            if op == '+':
                result = a + b
            elif op == '-':
                result = a - b
            elif op == '*':
                result = a * b
            elif op == '/':
                if b == 0:
                    raise ZeroDivisionError("Division by zero is not allowed.")
                result = a / b
            else:
                raise ValueError(f"Operation '{op}' is not supported.")
                
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
