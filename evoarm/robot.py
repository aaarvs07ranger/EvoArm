import pybullet as p
import math

class RobotArm:
    def __init__(self):
        # Load Franka Panda arm
        # We start it slightly elevated so it doesn't clip into the ground
        start_pos = [0, 0, 0]
        start_orientation = p.getQuaternionFromEuler([0, 0, 0])
        
        self.robot_id = p.loadURDF("franka_panda/panda.urdf", start_pos, start_orientation, useFixedBase=True)
        self.num_joints = p.getNumJoints(self.robot_id)

        self.ee_id = 11
        
        # Reset to a neutral "ready" pose
        self.reset()

    def reset(self):
        # Joint angles for a neutral standing position
        ready_pose = [0, -0.78, 0, -2.35, 0, 1.57, 0.78, 0.04, 0.04]
        
        for i in range(len(ready_pose)):
            p.resetJointState(self.robot_id, i, ready_pose[i])

    def get_current_pose(self):
        # Get End Effector (Hand) position
        # Link 11 is usually the tip of the Panda hand
        state = p.getLinkState(self.robot_id, self.ee_id)
        return state[0] # Returns (x, y, z) of the hand
    
    def move_to(self, target_pos):
        # moves the robot hand to target_pos [x, y, z]
        # uses inverse kinematics (IK) to calculate joint angles

        target_orn = p.getQuaternionFromEuler([math.pi, 0, 0])
        # calculating the IK
        joint_poses = p.calculateInverseKinematics(
            self.robot_id,
            self.ee_id,
            target_pos,
            target_orn
        )

        for i in range(7):
            p.setJointMotorControl2(
                bodyUniqueId = self.robot_id,
                jointIndex = i,
                controlMode = p.POSITION_CONTROL,
                targetPosition = joint_poses[i],
                force = 500
            )

    
    def open_gripper(self):
        # opens the fingers to their maximum possible width 0.04m each side
        # Finger joints are indices 7 and
        p.setJointMotorControl2(self.robot_id, 9, p.POSITION_CONTROL, targetPosition=0.04, force=100)
        p.setJointMotorControl2(self.robot_id, 10, p.POSITION_CONTROL, targetPosition=0.04, force=100)

    def close_gripper(self):
        # closes the fingers. We set the target to 0.0 (touching).
        # if an object is in the way, the motors will stall against it, creating grip force.
        p.setJointMotorControl2(self.robot_id, 9, p.POSITION_CONTROL, targetPosition=0.00, force=100)
        p.setJointMotorControl2(self.robot_id, 10, p.POSITION_CONTROL, targetPosition=0.00, force=100)
    