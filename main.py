import time
from evoarm.sim import Simulation
from evoarm.robot import RobotArm
from evoarm.planner import LLMPlanner
from evoarm.referee import Referee
from evoarm.critic import LLMCritic

def main():
    # 1. Setup Environment
    sim = Simulation(gui=True)
    sim.setup_environment()
    robot = RobotArm()
    
    # 2. Initialize Agents
    planner = LLMPlanner()
    referee = Referee(robot.robot_id, sim.cube_id, sim.table_id)
    critic = LLMCritic()
    
    # 3. The Tricky Instruction (Force a Failure first)
    instruction = "Try picking up the cube, but DO NOT close the gripper when you descend to the cube"
    
    # 4. The Self-Correction Loop
    max_retries = 3
    critique_history = []
    
    for attempt in range(max_retries):
        print(f"\n=== ATTEMPT {attempt + 1} / {max_retries} ===")
        
        # A. Reset Robot for a fresh start
        robot.reset() 
        # (Optional: Reset objects here if they moved too far)
        
        # B. Plan (Passing history allows the LLM to learn)
        try:
            plan = planner.generate_plan(instruction, past_critiques=critique_history)
        except Exception:
            print("Planning failed completely. Retrying...")
            continue

        print(f"Executing Plan ID: {plan.plan_id}")

        # C. Execute the Plan
        for step in plan.steps:
            print(f"Action: {step.action_type}")
            
            if step.action_type == "MOVE_EE":
                robot.move_to(step.xyz)
            elif step.action_type == "OPEN_GRIPPER":
                robot.open_gripper()
            elif step.action_type == "CLOSE_GRIPPER":
                robot.close_gripper()
            elif step.action_type == "DESCEND":
                current = robot.get_current_pose()
                robot.move_to([current[0], current[1], current[2] - step.dz])
            elif step.action_type == "LIFT":
                current = robot.get_current_pose()
                robot.move_to([current[0], current[1], current[2] + step.dz])
            
            # Wait for physics to settle
            for _ in range(80): sim.step()

        # D. Judge the Outcome
        outcome = referee.evaluate_episode()
        
        if outcome['success']:
            print(f"✅ SUCCESS! The robot learned after {attempt} failures.")
            break # Exit loop on victory
        else:
            print(f"❌ FAILURE: {outcome['failure_reason']}")
            
            # E. Critique (Learn from Failure)
            analysis = critic.analyze_failure(instruction, plan, outcome)
            print(f"💡 Critic Diagnosis: {analysis['diagnosis']}")
            print(f"🔧 Critic Suggestion: {analysis['suggestion']}")
            
            # Add to history so the planner sees it next time
            critique_history.append(analysis)
            
            # Pause briefly to read output
            time.sleep(1)

    print("Experiment Complete.")
    sim.keep_alive()

if __name__ == "__main__":
    main()
