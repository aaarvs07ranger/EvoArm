import os
import json
from openai import OpenAI
from typing import Dict, Any

class LLMCritic:
    def __init__(self):
        filename = 'api_key.txt'
        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, 'r', encoding = 'utf-8') as file:
            key = file.read()
        self.client = OpenAI(base_url = "https://api.groq.com/openai/v1", api_key = key)
        
        self.system_prompt = """
        You are the Failure Analysis Engine for a robotic arm.
        
        You will be given:
        1. The user's original INSTRUCTION.
        2. The PLAN the robot executed (sequence of actions).
        3. The FAILURE MODE detected by the referee (e.g., MISSED_GRASP).
        4. The METRICS (final height, contact points).
        
        Your Goal:
        Explain WHY the robot failed and suggest a fix.
        
        Failure Definitions:
        - MISSED_GRASP: The gripper closed on thin air. Usually means bad alignment or the gripper didn't close at all.
        - GRASP_SLIP: The robot touched the object but lost it. Usually means low friction or weak force.
        - UNSTABLE_LIFT: The object fell off during the lift.
        
        Output Format (JSON):
        {
            "diagnosis": "One sentence explaining the physical cause.",
            "suggestion": "One sentence on how the planner should change the next attempt."
        }
        """

    def analyze_failure(self, instruction: str, plan: Dict, outcome: Dict) -> Dict:
        print("🤔 Critic is analyzing the failure...")
        
        # Construct the "Evidence" packet
        evidence = {
            "instruction": instruction,
            "failure_mode": outcome['failure_reason'],
            "metrics": outcome['metrics'],
            "executed_plan_steps": [s.model_dump() for s in plan.steps]
        }
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": json.dumps(evidence)}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Critic failed: {e}")
            return {"diagnosis": "Unknown", "suggestion": "Retry"}
        