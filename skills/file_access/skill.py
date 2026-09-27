import os
from enum import Enum
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class FileOperation(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    LIST = "LIST"

class FileAccessInput(BaseModel):
    operation: FileOperation = Field(..., description="File operation: READ, WRITE, or LIST.")
    file_path: str = Field(..., description="Target relative or absolute path within the workspace.")
    content: Optional[str] = Field(default=None, description="Text content required when operation is WRITE.")

class FileAccessSkill(BaseSkill):
    """
    Skill to interact with the local file system safely.
    Enforces directory guardrails to avoid escaping the allowed workspace directory.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = os.path.abspath(workspace_root or os.getcwd())

    def _resolve_safe_path(self, path: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.workspace_root, path))
        # Ensure path does not escape the workspace root
        if not abs_path.startswith(self.workspace_root):
            raise PermissionError(f"Access denied: path '{path}' is outside the workspace root.")
        return abs_path

    @property
    def name(self) -> str:
        return "file_access"

    @property
    def description(self) -> str:
        return "Safely reads, writes, and lists files within the current workspace directory."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return FileAccessInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)

        try:
            target_path = self._resolve_safe_path(data.file_path)

            if data.operation == FileOperation.READ:
                if not os.path.exists(target_path):
                    return {"success": False, "error": f"File '{data.file_path}' does not exist."}
                with open(target_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"success": True, "file_path": data.file_path, "content": content}

            elif data.operation == FileOperation.WRITE:
                if data.content is None:
                    return {"success": False, "error": "Content must be provided for WRITE operation."}
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(data.content)
                return {"success": True, "file_path": data.file_path, "bytes_written": len(data.content.encode('utf-8'))}

            elif data.operation == FileOperation.LIST:
                if not os.path.exists(target_path):
                    return {"success": False, "error": f"Directory '{data.file_path}' does not exist."}
                entries = []
                for entry in os.scandir(target_path):
                    entries.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else None
                    })
                return {"success": True, "path": data.file_path, "entries": entries}

        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": f"Unsupported operation '{data.operation}'"}
