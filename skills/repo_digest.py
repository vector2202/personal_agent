import ast
import os
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class RepoDigestInput(BaseModel):
    file_path: str = Field(..., description="Path of the Python file to inspect and parse with AST.")

class RepoArchitectureDigest(BaseSkill):
    """
    Analyzes Python files using Abstract Syntax Trees (AST) to map classes, methods,
    and functions with zero LLM inference cost.
    """

    @property
    def name(self) -> str:
        return "repo_architecture_digest"

    @property
    def description(self) -> str:
        return "Extracts architectural signatures (classes, functions, methods, docstrings) from Python files using AST."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return RepoDigestInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)

        if not os.path.exists(data.file_path):
            return {"success": False, "error": f"File '{data.file_path}' does not exist."}

        try:
            with open(data.file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=data.file_path)

            classes: List[Dict[str, Any]] = []
            functions: List[Dict[str, Any]] = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        "class_name": node.name,
                        "docstring": ast.get_docstring(node),
                        "methods": methods,
                        "line_number": node.lineno
                    })
                elif isinstance(node, ast.FunctionDef):
                    functions.append({
                        "function_name": node.name,
                        "docstring": ast.get_docstring(node),
                        "args": [arg.arg for arg in node.args.args],
                        "line_number": node.lineno
                    })

            return {
                "success": True,
                "file_path": data.file_path,
                "total_classes": len(classes),
                "total_functions": len(functions),
                "classes": classes,
                "functions": functions
            }
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error in file: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"AST extraction failed: {str(e)}"}
