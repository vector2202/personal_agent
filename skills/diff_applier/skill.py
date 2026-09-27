import os
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class DiffApplierInput(BaseModel):
    file_path: str = Field(..., description="Target file path to modify.")
    target_block: str = Field(..., description="The exact contiguous block of code to find and replace.")
    replacement_block: str = Field(..., description="The new replacement code block.")

class TargetedDiffApplier(BaseSkill):
    """
    Applies surgical diff replacements to specific code blocks in files
    without rewriting or corrupting the rest of the file.
    """

    @property
    def name(self) -> str:
        return "targeted_diff_applier"

    @property
    def description(self) -> str:
        return "Applies surgical block replacements to existing files without rewriting entire files."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return DiffApplierInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)

        if not os.path.exists(data.file_path):
            return {"success": False, "error": f"File '{data.file_path}' does not exist."}

        try:
            with open(data.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if data.target_block not in content:
                return {
                    "success": False,
                    "error": "The target block was not found in the specified file. Ensure whitespace matches precisely."
                }

            occurrences = content.count(data.target_block)
            if occurrences > 1:
                return {
                    "success": False,
                    "error": f"Ambiguous match: Target block appears {occurrences} times. Provide a larger unique context."
                }

            updated_content = content.replace(data.target_block, data.replacement_block, 1)

            with open(data.file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return {
                "success": True,
                "file_path": data.file_path,
                "status": "APPLIED_SUCCESSFULLY"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to apply diff: {str(e)}"}
