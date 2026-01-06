from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Tuple

# we will define the allowed actions which the robot can execute

class Action(BaseModel):
    action_type: Literal[
        "MOVE_EE",
        "APPROACH",
        "DESCEND", 
        "CLOSE_GRIPPER", 
        "OPEN_GRIPPER", 
        "LIFT",
        "RETRACT"
    ]
    # Optional parameters depending on the action type
    # We use Optional because 'OPEN_GRIPPER' needs no params, but 'MOVE_EE' does.
    xyz: Optional[Tuple[float, float, float]] = Field(None, description="Target coordinates [x,y,z]")
    target_object: Optional[str] = Field(None, description="ID of the object to interact with")
    force: Optional[float] = Field(100.0, description="Gripper force in Newtons")
    dz: Optional[float] = Field(None, description="Vertical distance for lift/descend")

class ManipulationPlan(BaseModel):
    plan_id: str
    instruction: str = Field(..., description="The original natural language command")
    steps: List[Action]
