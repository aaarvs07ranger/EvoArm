import pybullet as p
from typing import Dict, Any

class Referee:
    def __init__(self, robot_id, cube_id, table_id):
        self.robot_id = robot_id
        self.cube_id = cube_id
        self.table_id = table_id

    def evaluate_episode(self) -> Dict[str, Any]:
        # inspects the simulation state to determine if the task was successful
        # 1. Get Cube State
        cube_pos, _ = p.getBasePositionAndOrientation(self.cube_id)
        cube_z = cube_pos[2]
        
        # 2. Check Height (Did we lift it?)
        # Table is at z=0 (surface). If cube_z > 0.1, it's in the air.
        is_lifted = cube_z > 0.1
        
        # 3. Check Contact (Is the robot actually holding it?)
        # We ask PyBullet: "Is the gripper touching the cube?"
        contact_points = p.getContactPoints(bodyA=self.robot_id, bodyB=self.cube_id)
        is_held = len(contact_points) > 0
        
        # 4. Determine Verdict
        success = is_lifted and is_held
        
        # 5. Classify Failure Mode (Crucial for the LLM Critic later)
        failure_reason = "NONE"
        if not success:
            if not is_held and is_lifted:
                # Paradox: It's in the air but we aren't holding it? 
                # (Maybe we threw it, or it's resting on the arm)
                failure_reason = "UNSTABLE_LIFT"
            elif not is_lifted:
                # It's still on the table.
                # Did we at least touch it?
                if len(contact_points) > 0:
                    failure_reason = "GRASP_SLIP"  # We touched it but failed to lift
                else:
                    failure_reason = "MISSED_GRASP" # We grabbed thin air
        
        return {
            "success": success,
            "failure_reason": failure_reason,
            "metrics": {
                "final_height": round(cube_z, 3),
                "contacts": len(contact_points)
            }
        }
    
