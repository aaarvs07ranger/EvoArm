import pybullet as p
import pybullet_data
import time

class Simulation:
    def __init__(self, gui=True):
        self.gui = gui
        self.client_id = p.connect(p.GUI if gui else p.DIRECT)
        
        # Configure PyBullet
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        p.resetDebugVisualizerCamera(cameraDistance=1.5, cameraYaw=90, cameraPitch=-30, cameraTargetPosition=[0, 0, 0])

    def setup_environment(self):
        # Load the ground plane
        self.plane_id = p.loadURDF("plane.urdf")
        
        # Load a table
        self.table_id = p.loadURDF("table/table.urdf", basePosition=[0.5, 0, -0.63], globalScaling=1.0)
        
        # Load a simple cube (the manipulation target)
        self.cube_id = p.loadURDF("cube_small.urdf", basePosition=[0.5, 0, 0.05], globalScaling=1.0)

    def step(self):
        p.stepSimulation()
        if self.gui:
            time.sleep(1./240.) # Real-time simulation speed

    def keep_alive(self):
        # Helper to keep the window open for debugging
        print("Simulation running. Press Ctrl+C to exit.")
        while True:
            self.step()