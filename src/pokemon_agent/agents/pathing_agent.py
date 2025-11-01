from .init_llm import llm
from pydantic import BaseModel
from path_finder import *

class AnswerSchema(BaseModel):
    dest_x: int
    dest_y: int

structered_llm = llm.with_structured_output(AnswerSchema)

def pathing_agent(state):
    system_prompt = f"""
You are controlling a character in the following map.
P = player, # = wall/blocker, - = walkable
Your task: {state["pathing_info"]["task"]}

Map:
{state["pathing_info"]["map"]}

Player Location [x,y]:
{state["pathing_info"]["player_position"]}

Known Doorways:
{state["pathing_info"]["known_door_tiles"]}

Question: Which destination coordinate should the player move to so that the task is accomplished?
Return only JSON: "dest_x": x, "dest_y": y

"""
    response = structered_llm.invoke(system_prompt)
    state["messages"].append({"role":"pathing", "content": response.model_dump()})
    state["destination"] = response.model_dump()
    return state