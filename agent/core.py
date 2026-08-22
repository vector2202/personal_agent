import json
from typing import List, Dict, Any
from google import genai
from google.genai import types
from skills.base import BaseSkill

class AgentCore:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initializes the agent core with the new google-genai Client and registers available skills.
        """
        # Initialize the modern Client
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.skills: Dict[str, BaseSkill] = {}
        
    def register_skill(self, skill: BaseSkill):
        """Registers a skill in the agent's toolbox."""
        self.skills[skill.name] = skill
        print(f"[Core] Successfully registered skill: '{skill.name}'")

    def _build_system_instruction(self) -> str:
        """
        Constructs the system instructions, explaining the ReAct loop
        and dynamically listing the available tools and their JSON schemas.
        """
        tools_desc = []
        for name, skill in self.skills.items():
            schema_json = skill.input_schema.model_json_schema()
            tools_desc.append(
                f"- Tool: `{name}`\n"
                f"  Description: {skill.description}\n"
                f"  Input Schema (JSON): {json.dumps(schema_json)}"
            )
            
        skills_formatted = "\n\n".join(tools_desc)
        
        instruction = (
            "You are an autonomous personal intelligent assistant. Your goal is to solve user requests "
            "using a reasoning and action (ReAct) loop.\n\n"
            "You have access to the following local tools:\n\n"
            f"{skills_formatted}\n\n"
            "LOOP INSTRUCTIONS:\n"
            "You must respond in a structured JSON format containing the following keys:\n"
            "{\n"
            '  "thought": "Your thought process on what to do next.",\n'
            '  "action": "The name of the tool to execute (or null if you are providing the final answer)",\n'
            '  "action_input": { ... tool arguments matching the schema ... } or null,\n'
            '  "final_answer": "Your final answer to the user (or null if you are calling a tool)"\n'
            "}\n\n"
            "RULES:\n"
            "1. If you need to use a tool, set 'action' to its name, 'action_input' to its parameters, and set 'final_answer' to null.\n"
            "2. When you have enough information or consider the task complete, set both 'action' and 'action_input' to null, and write your answer under 'final_answer'.\n"
            "3. IMPORTANT: Always respond only with the valid JSON object. Do not include any text outside the JSON."
        )
        return instruction

    def execute(self, user_prompt: str, max_steps: int = 5) -> str:
        """
        Executes the main ReAct control loop.
        """
        # Internal execution history using raw messages matching Gemini schema format
        history = [
            types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])
        ]
        
        print(f"\n[Core] Starting ReAct loop for: '{user_prompt}'")
        
        for step in range(1, max_steps + 1):
            print(f"\n--- STEP {step} ---")
            
            # 1. Call the LLM to get the next step
            # We pass system_instruction and set response_mime_type inside GenerateContentConfig
            config = types.GenerateContentConfig(
                system_instruction=self._build_system_instruction(),
                response_mime_type="application/json",
                temperature=0.1
            )
            
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=history,
                    config=config
                )
            except Exception as e:
                print(f"[Error] Gemini API generation failed: {e}")
                return f"Error connecting to LLM service: {e}"
            
            # Attempt to parse response JSON
            try:
                response_data = json.loads(response.text)
            except (json.JSONDecodeError, TypeError):
                print(f"[Error] Model failed to return valid JSON. Raw output: {response.text}")
                return "Error: Invalid response format from LLM."
            
            thought = response_data.get("thought")
            action = response_data.get("action")
            action_input = response_data.get("action_input")
            final_answer = response_data.get("final_answer")
            
            print(f"[Thought]: {thought}")
            
            # Record the model's response in history
            history.append(types.Content(role="model", parts=[types.Part.from_text(text=response.text)]))
            
            # If the model emits a final answer, return it
            if final_answer and not action:
                print(f"[Final Answer]: {final_answer}")
                return final_answer
                
            # If the model calls a tool
            if action:
                if action not in self.skills:
                    observation = f"Error: Tool '{action}' is not registered."
                else:
                    skill = self.skills[action]
                    print(f"[Action] Invoking tool '{action}' with parameters: {action_input}")
                    
                    # 2. Execute the local tool
                    result = skill.execute(action_input)
                    observation = json.dumps(result)
                    
                print(f"[Observation]: {observation}")
                
                # Feed observation back as a user response to continue the conversation context
                history.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"Observation from tool '{action}': {observation}")]
                ))
            else:
                print("[Warning] Model provided neither action nor final answer. Aborting loop.")
                break
                
        return "Agent failed to complete the task within the maximum steps limitation."
