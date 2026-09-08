import time
import os
import json
from typing import Type, Dict, Any, List, Optional
from pydantic import BaseModel, Field
from skills.base import BaseSkill
from google import genai
from google.genai import types

class TestCase(BaseModel):
    prompt: str = Field(..., description="The user prompt to test.")
    expected_tool: Optional[str] = Field(None, description="The expected tool to be invoked.")
    expected_args_subset: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Subset of arguments expected in tool input.")

class EvalBenchmarkInput(BaseModel):
    test_cases: List[TestCase] = Field(..., description="List of test cases to benchmark.")
    agent_model: Optional[str] = Field(default="gemini-2.5-flash", description="Model identifier to evaluate.")

class AutomatedEvalBenchmark(BaseSkill):
    """
    Production-grade Automated Evaluation Benchmark Skill.
    Runs real prompts against Gemini's decision engine and measures:
    - Tool Selection Accuracy (%)
    - Argument Conformance (Schema matching)
    - Real-world Latency (ms)
    - Detailed failure diagnostics
    """

    @property
    def name(self) -> str:
        return "automated_eval_benchmark"

    @property
    def description(self) -> str:
        return "Runs automated benchmark test cases against the agent to measure tool selection accuracy, latency, and conformance."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return EvalBenchmarkInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            return {"success": False, "error": "GEMINI_API_KEY is not set. Cannot run live evaluation."}

        # Import here to prevent circular imports
        from skills import __all__ as all_skill_names
        import skills

        # Collect JSON schemas for registered skills
        tools_desc = []
        registered_skills = {}
        for skill_name in all_skill_names:
            if skill_name == "BaseSkill":
                continue
            skill_cls = getattr(skills, skill_name, None)
            if skill_cls and issubclass(skill_cls, BaseSkill):
                try:
                    instance = skill_cls()
                    registered_skills[instance.name] = instance
                    schema_json = instance.input_schema.model_json_schema()
                    tools_desc.append(
                        f"- Tool: `{instance.name}`\n"
                        f"  Description: {instance.description}\n"
                        f"  Input Schema (JSON): {json.dumps(schema_json)}"
                    )
                except Exception:
                    continue

        skills_formatted = "\n\n".join(tools_desc)
        system_instruction = (
            "You are an autonomous personal intelligent assistant. Analyze the user prompt and decide which tool to call.\n\n"
            f"Available tools:\n\n{skills_formatted}\n\n"
            "Respond ONLY with a JSON object: "
            '{"thought": "...", "action": "tool_name_or_null", "action_input": {...}, "final_answer": "..."}'
        )

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.0
        )

        start_total = time.time()
        results = []
        passed_count = 0

        for idx, tc in enumerate(data.test_cases):
            case_start = time.time()
            prompt = tc.prompt
            expected = tc.expected_tool
            expected_args = tc.expected_args_subset or {}

            try:
                response = client.models.generate_content(
                    model=data.agent_model,
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                    config=config
                )
                latency_ms = int((time.time() - case_start) * 1000)
                parsed = json.loads(response.text)
                chosen_tool = parsed.get("action")
                chosen_args = parsed.get("action_input") or {}

                # Check accuracy
                tool_match = (chosen_tool == expected)
                
                # Check args conformance if specified
                args_match = True
                if expected_args and isinstance(chosen_args, dict):
                    for k, v in expected_args.items():
                        if chosen_args.get(k) != v:
                            args_match = False
                            break
                elif expected_args and not isinstance(chosen_args, dict):
                    args_match = False

                passed = tool_match and args_match
                if passed:
                    passed_count += 1

                results.append({
                    "test_index": idx + 1,
                    "prompt": prompt,
                    "expected_tool": expected,
                    "chosen_tool": chosen_tool,
                    "tool_match": tool_match,
                    "args_match": args_match,
                    "passed": passed,
                    "latency_ms": latency_ms,
                    "thought": parsed.get("thought")
                })
            except Exception as e:
                latency_ms = int((time.time() - case_start) * 1000)
                results.append({
                    "test_index": idx + 1,
                    "prompt": prompt,
                    "expected_tool": expected,
                    "error": str(e),
                    "passed": False,
                    "latency_ms": latency_ms
                })

        total = len(data.test_cases)
        total_duration = round(time.time() - start_total, 2)
        accuracy = round((passed_count / total) * 100, 1) if total > 0 else 0.0

        return {
            "success": True,
            "total_tests": total,
            "passed": passed_count,
            "accuracy_percentage": accuracy,
            "total_duration_seconds": total_duration,
            "model_evaluated": data.agent_model,
            "test_results": results
        }
