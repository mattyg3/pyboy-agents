from path_finder import *
from skills import SkillExecutor
import fnmatch
import re

class PathingAgent:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.skills = SkillExecutor(self.pyboy)

    def go_to_destination_xy(self, CUSTOM_DEST):
        
        map_id = get_current_map(self.pyboy)
        map_filename = find_map_by_id(MAP_HEADERS, map_id).get("file")
        if fnmatch.fnmatch(CUSTOM_DEST, "*enter*"):
            match = re.search(r"'([^']*)'", CUSTOM_DEST)
            dest_key = match.group(1)
            print(f"DEST_KEY: {dest_key}")
            warp_tiles = get_warp_tiles(map_filename)
            warps = []
            for warp in warp_tiles:
                if warp.get("destination")==dest_key:
                    warps.append((warp.get("xy_coord")[0], warp.get("xy_coord")[1]))
            print(f"GOAL: {warps[0]}")  
            path_finder(self.pyboy, goal=warps[0])
            # cntr = 0
            # new_map_id, px, py, direction = get_player_position(pyboy)
            # while map_id == new_map_id:
            #     print("\n\nEXTRA LOOP\n\n")
            #     cntr+=1
            #     new_map_id, px, py, direction = get_player_position(pyboy)
            #     if cntr <= 3:
            #         skills.execute({"type": "GO_UP"})
            #         print("UP_EXTRA")
            #     else: 
            #         skills.execute({"type": "GO_DOWN"})
            #         print("DOWN_EXTRA")
            for _ in range(60):  # wait a second for new map to load
                self.pyboy.tick()
                
            
        elif fnmatch.fnmatch(CUSTOM_DEST, "*move*"):
            match = re.search(r"'([^']*)'", CUSTOM_DEST)
            dest_key = match.group(1).lower() #north, south, east, west
            print(f"DEST_KEY: {dest_key}")
            connection_coords = get_map_connections(map_id, dest_key) #ADD RETRY FOR ALL POSSIBLE CONNECTIONS
            print(f"connection_coords: {connection_coords}")
            formated_coords = (connection_coords[0][0], connection_coords[0][1])
            # print(f"GOAL(from connection key): {formated_coords}")
            path_finder(self.pyboy, goal=formated_coords)
            if dest_key == "north":
                self.skills.execute({"type": "GO_UP"})
                print("UP_EXTRA")
            elif dest_key == "south":
                self.skills.execute({"type": "GO_DOWN"})
                print("DOWN_EXTRA")
            elif dest_key == "east":
                self.skills.execute({"type": "GO_RIGHT"})
                print("RIGHT_EXTRA")
            elif dest_key == "west":
                self.skills.execute({"type": "GO_LEFT"})
                print("LEFT_EXTRA")
            for _ in range(60):  # wait a few frames for movement
                self.pyboy.tick()

        elif fnmatch.fnmatch(CUSTOM_DEST, "*talk*"):
            match = re.search(r"'([^']*)'", CUSTOM_DEST)
            dest_key = match.group(1)
            print(f"DEST_KEY: {dest_key}")
            npc_xy = get_npc_coords(map_filename)
            for npc in npc_xy:
                if npc.get("name")==dest_key:
                    if npc.get("text")[-1] != '2':
                        npc_coords = (npc.get("x"), npc.get("y"))
            print(f"GOAL: {npc_coords}")  
            path_finder(self.pyboy, goal=npc_coords)
            self.skills.execute({"type": "PRESS_A"})
            print("START_DIALOG")
            for _ in range(60):  # wait a few frames for movement
                self.pyboy.tick()










# from .init_llm import llm
# from pydantic import BaseModel
# from path_finder import *

# class AnswerSchema(BaseModel):
#     dest_x: int
#     dest_y: int

# structered_llm = llm.with_structured_output(AnswerSchema)

# def pathing_agent(state):
#     system_prompt = f"""
# You are controlling a character in the following map.
# P = player, # = wall/blocker, - = walkable
# Your task: {state["pathing_info"]["task"]}

# Map:
# {state["pathing_info"]["map"]}

# Player Location [x,y]:
# {state["pathing_info"]["player_position"]}

# Known Doorways:
# {state["pathing_info"]["known_door_tiles"]}

# Question: Which destination coordinate should the player move to so that the task is accomplished?
# Return only JSON: "dest_x": x, "dest_y": y

# """
#     response = structered_llm.invoke(system_prompt)
#     state["messages"].append({"role":"pathing", "content": response.model_dump()})
#     state["destination"] = response.model_dump()
#     return state