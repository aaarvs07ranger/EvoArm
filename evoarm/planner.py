# mock LLM at the start, eventually it will call LLaMa or OpenAI

import json
from evoarm.schemas import ManipulationPlan
import os
from openai import OpenAI
from typing import List, Dict

class LLMPlanner:
    def __init__(self):
        # Initialize the OpenAI Client
        filename = 'api_key.txt'
        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, 'r', encoding = 'utf-8') as file:
            key = file.read()
        self.client = OpenAI(base_url = "https://api.groq.com/openai/v1", api_key = key.strip())
        
        # This is the "System Prompt" - The instructions that define who the AI is.
        self.system_prompt = """
        You are the high-level planner for a 7-DOF Franka Emika Panda robot arm.
        
        The Environment:
        - Table surface is at z=0.0.
        - Safe travel height is z=0.3.
        - The robot base is at [0,0,0].
        - Objects are typically located around x=0.5, y=0.0.
        
        Your Goal:
        Convert the user's natural language instruction into a sequence of precise actions.
        
        Allowed Actions (JSON Schema):
        1. "MOVE_EE": Move to specific [x, y, z] coordinates.
        2. "OPEN_GRIPPER": Open fingers.
        3. "CLOSE_GRIPPER": Close fingers (use force=100).
        4. "DESCEND": Move straight down by distance 'dz'.
        5. "LIFT": Move straight up by distance 'dz'.
        
        Output Format:
        You must output strictly valid JSON conforming to this structure:
        {
            "plan_id": "unique_string",
            "instruction": "original instruction",
            "steps": [
                {"action_type": "ACTION_NAME", "xyz": [x,y,z], ...},
                ...
            ]
        }
        
        Rules:
        - Always open the gripper before approaching an object.
        - Always descend to grasp height (z approx 0.02) before closing.
        - Always lift after closing the gripper.
        CRITICAL INSTRUCTION:
        If you are provided with "Previous Critiques", you MUST analyze them.
        ...
        You must adjust your new plan to address the "Suggestion" provided in the critique.
        """
    
    def generate_plan(self, instruction: str, past_critiques: List[Dict] = []) -> ManipulationPlan:
        print(f"🧠 Asking OpenAI to plan: '{instruction}'...")
        # 1. Start with the original instruction
        user_content = f"Instruction: {instruction}"
        
        # 2. Check if we have baggage (past failures)
        if past_critiques:
            print(f"   ...with knowledge of {len(past_critiques)} previous failures.")
            
            # 3. Add a clear header so the LLM knows this is Context, not a new command
            user_content += "\n\nPREVIOUS ATTEMPTS & FEEDBACK:"
            
            # 4. Loop through every mistake we made
            for i, critique in enumerate(past_critiques):
                # We paste the exact Diagnosis and Suggestion from the Critic
                user_content += f"\nAttempt {i+1} Diagnosis: {critique['diagnosis']}"
                user_content += f"\nAttempt {i+1} Suggestion: {critique['suggestion']}"
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}, # FORCES valid JSON
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1 # Low randomness = more reliable plans
            )
            
            # 1. Get raw text
            raw_content = response.choices[0].message.content
            print(f"📝 Raw JSON received:\n{raw_content}")
            
            # 2. Parse into Python Dictionary
            json_plan = json.loads(raw_content)
            
            # 3. Validate with Pydantic (The Bridge)
            validated_plan = ManipulationPlan(**json_plan)
            return validated_plan
            
        except Exception as e:
            print(f"❌ Planning Failed: {e}")
            # Return an empty plan or re-raise
            raise e