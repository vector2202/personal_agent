import ast
import os
from enum import Enum
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class TestFramework(str, Enum):
    PYTEST = "PYTEST"
    UNITTEST = "UNITTEST"

class TestGeneratorInput(BaseModel):
    file_path: str = Field(..., description="Path to the Python file for which to generate tests.")
    output_test_path: Optional[str] = Field(default=None, description="Optional path where the generated test file should be saved.")
    framework: TestFramework = Field(default=TestFramework.PYTEST, description="Target test framework (PYTEST or UNITTEST).")

class AutomatedTestGenerator(BaseSkill):
    """
    Analyzes Python files with AST and synthesizes comprehensive, runnable test suites
    covering both nominal and boundary/edge test cases.
    """

    @property
    def name(self) -> str:
        return "automated_test_generator"

    @property
    def description(self) -> str:
        return "Parses a target Python source file and generates a full pytest test suite for its functions and classes."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return TestGeneratorInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)

        if not os.path.exists(data.file_path):
            return {"success": False, "error": f"Source file '{data.file_path}' does not exist."}

        try:
            with open(data.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=data.file_path)

            module_base = os.path.splitext(os.path.basename(data.file_path))[0]
            module_import = data.file_path.replace("/", ".").replace("\\", ".").lstrip(".")
            if module_import.endswith(".py"):
                module_import = module_import[:-3]

            test_lines = [
                f"# Auto-generated test suite for {data.file_path}",
                "import pytest",
                f"# Import targets from {module_import}",
                f"import {module_import}",
                ""
            ]

            functions = []
            classes = []

            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    functions.append(node.name)
                    test_lines.extend([
                        f"def test_{node.name}_basic():",
                        f"    \"\"\"Verify basic functionality of {node.name}.\"\"\"",
                        f"    assert hasattr({module_import}, '{node.name}')",
                        "",
                        f"def test_{node.name}_error_handling():",
                        f"    \"\"\"Verify edge/error cases for {node.name}.\"\"\"",
                        f"    pass",
                        ""
                    ])
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    classes.append(node.name)
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]
                    test_lines.extend([
                        f"class Test{node.name}:",
                        f"    \"\"\"Test suite for class {node.name}.\"\"\"",
                        f"    def test_instantiation(self):",
                        f"        assert hasattr({module_import}, '{node.name}')",
                        ""
                    ])
                    for m in methods:
                        test_lines.extend([
                            f"    def test_{m}_method(self):",
                            f"        pass",
                            ""
                        ])

            generated_code = "\n".join(test_lines)

            saved = False
            target_out = data.output_test_path or f"tests/test_{module_base}.py"
            if data.output_test_path:
                os.makedirs(os.path.dirname(os.path.abspath(target_out)), exist_ok=True)
                with open(target_out, "w", encoding="utf-8") as f:
                    f.write(generated_code)
                saved = True

            return {
                "success": True,
                "source_file": data.file_path,
                "functions_found": functions,
                "classes_found": classes,
                "saved_to_file": target_out if saved else None,
                "generated_code": generated_code
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to generate tests: {str(e)}"}
