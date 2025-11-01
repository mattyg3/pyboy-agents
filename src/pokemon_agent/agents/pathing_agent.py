from .init_llm import llm
from pydantic import BaseModel
from path_finder import *

class AnswerSchema(BaseModel):
    destination_x: int
    destination_y: int

structered_llm = llm.with_structured_output(AnswerSchema)

def pathing_agent(state):
    system_prompt = f"""
# Role
You are an expert at determining destination (x,y) coordinates given a grid of walkable/unwalkable tiles, the start location, and a description of the desired destination. 

# Task
Determine the DESTINATION_X and DESTINATION_Y integers.

# Grid Information
**grid** is a representing a map with walkable and unwalkable tiles. For orientation, tile (0,0) is the **top-left** of grid. 
can only walk over tiles that have values **TRUE**

# Inputs
grid: {state["walkable_grid"]}
grid_width: {state["grid_width"]}
grid_height: {state["grid_height"]}
start_tuple: {state["start_xy"]}
desired_destination: {state["destination_wanted"]}

# Output 
**ONLY** X, Y integers
"""
    response = structered_llm.invoke(system_prompt)
    state["messages"].append({"role":"pathing", "content": response.model_dump()})
    state["destination"] = response.model_dump()
    return state