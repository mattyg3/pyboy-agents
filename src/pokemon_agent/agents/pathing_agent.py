from pokemon_agent.plugins.path_finder import *
from pokemon_agent.plugins.skills import SkillExecutor
from pokemon_agent.agents.unstuck_agent import create_unstuck_agent_state, UnstuckAgent
from pokemon_agent.plugins.perception import BattleFlag, DialogFlag
import lmstudio as lms
import fnmatch
import re
import numpy as np
import cv2
# import random
from langchain_core.runnables.config import RunnableConfig


def center_of_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    return (cx, cy)
def nearest_even(n):
    return int(round(n / 2) * 2)

def center_even(points):
    cx, cy = center_of_points(points)
    return (nearest_even(cx), nearest_even(cy))


class PathingAgent:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.skills = SkillExecutor(self.pyboy)
        self.unstuck_agent_state=create_unstuck_agent_state()
        self.unstuck_agent=UnstuckAgent(self.pyboy)
        self.unstuck_agent.compile_workflow(self.unstuck_agent_state)
        self.battle_flag = BattleFlag(self.pyboy)
        self.dialog_flag = DialogFlag(self.pyboy)

    def run_unstuck_agent(self):
        screen_frame = self.pyboy.screen.ndarray
        cv2.imwrite("src/pokemon_agent/saves/unstuck_agent_frame.png", screen_frame)
        self.unstuck_agent_state["screenshot"] = lms.prepare_image("src/pokemon_agent/saves/unstuck_agent_frame.png")
        config = RunnableConfig(recursion_limit=4)
        self.unstuck_agent_state = self.unstuck_agent.app.invoke(self.unstuck_agent_state, config)
        try:
            # print(f"CORRECTIVE_ACTIONS: {unstuck_agent_state["corrective_action"]}")
            for action in self.unstuck_agent_state["corrective_action"]: #{"type": "GO_DOWN"}
                self.skills.execute(action)
        except Exception as e: 
            print(e)
            pass


    def go_to_destination_xy(self, CUSTOM_DEST):
        map_id = get_current_map(self.pyboy)
        map_filename = find_map_by_id(MAP_HEADERS, map_id).get("file")
        
        if fnmatch.fnmatch(CUSTOM_DEST, "*enter*"):
            match = re.search(r"'([^']*)'", CUSTOM_DEST)
            dest_key = match.group(1)
            print(f"DEST_KEY: {dest_key}")
            warp_tiles = get_warp_tiles(map_filename)
            warps = []
            warp_x = []
            warp_y = []
            for warp in warp_tiles:
                if warp.get("destination")==dest_key:
                    warps.append((warp.get("xy_coord")[0], warp.get("xy_coord")[1]))
                    warp_x.append(warp.get("xy_coord")[0])
                    warp_y.append(warp.get("xy_coord")[1])
            goal_xy = (int(np.mean(warp_x)), int(np.mean(warp_y)))
            try:
                map_id, px, py, direction = get_player_position(self.pyboy)
                walk_matrix, map_width, map_height, warp_tiles = read_map(self.pyboy)
                print(f"Player at map {map_id}, X={px}, Y={py}, Looking={direction}") #(0: down, 4: up, 8: left, 12: right)
                walk_matrix[py][px] = 'P' #player location
                walk_matrix[goal_xy[1]][goal_xy[0]] = 'G' #goal location
            except:
                pass
            print("\nWalkable tile matrix ('-' = walkable, '#' = blocked):")
            print_tile_walk_matrix(walk_matrix)
            print(f"GOAL: {goal_xy}")  
            prev_map_id = map_id
            retry_ctn = 0
            while prev_map_id == map_id:
                battle_info = self.battle_flag.read_memory_state()
                dialog_info = self.dialog_flag.read_memory_state()
                if battle_info["battle_type"] != 0:
                    break
                if dialog_info:
                    break
                map_id, px, py, direction = get_player_position(self.pyboy)
                walk_matrix, map_width, map_height, warp_tiles = read_map(self.pyboy)
                retry_ctn+=1
                # if retry_ctn > 5:
                #     break
                if not astar(walk_matrix, (px, py), goal_xy):
                    path_dict={}
                    break
                else:
                    if retry_ctn % 4 == 0:
                        self.run_unstuck_agent()
                        
                    path_dict = path_finder(self.pyboy, goal=goal_xy)
                    path_dict["goal_xy"] = goal_xy
                    print(f"PERSISTENT_GOAL: {retry_ctn}" )
                
            
        elif fnmatch.fnmatch(CUSTOM_DEST, "*move*"):
            match = re.search(r"'([^']*)'", CUSTOM_DEST)
            dest_key = match.group(1).lower() #north, south, east, west
            print(f"DEST_KEY: {dest_key}")
            connection_coords = get_map_connections(map_id, dest_key) #ADD RETRY FOR ALL POSSIBLE CONNECTIONS
            goal_xy = center_even(connection_coords)
            # print(f"connection_coords: {connection_coords}")
            # print(type(connection_coords))
            # formated_coords = (connection_coords[0][0], connection_coords[0][1])
            # print(f"GOAL(from connection key): {formated_coords}")
            # warp_x = []
            # warp_y = []
            # warps = []
            # for connection in connection_coords:
            #     if connection[0] % 2 == 0 and connection[1] % 2 == 0:
            #         warps.append((connection[0], connection[1]))
            #         warp_x.append(connection[0])
            #         warp_y.append(connection[1])
            # goal_avg = (int(np.mean(warp_x)), int(np.mean(warp_y)))
            # goal_xy = random.choice(warps)
            # goal_xy = (connection_coords[0][0], connection_coords[0][1])
            try:
                map_id, px, py, direction = get_player_position(self.pyboy)
                walk_matrix, map_width, map_height, warp_tiles = read_map(self.pyboy)
                print(f"Player at map {map_id}, X={px}, Y={py}, Looking={direction}") #(0: down, 4: up, 8: left, 12: right)
                walk_matrix[py][px] = 'P' #player location
                walk_matrix[goal_xy[1]][goal_xy[0]] = 'G' #goal location
            except:
                pass
            print(f"GOAL: {goal_xy}")
            prev_map_id = map_id
            retry_ctn=0
            while prev_map_id == map_id:
                battle_info = self.battle_flag.read_memory_state()
                dialog_info = self.dialog_flag.read_memory_state()
                if battle_info["battle_type"] != 0:
                    break
                if dialog_info:
                    break
                map_id, px, py, direction = get_player_position(self.pyboy)
                walk_matrix, map_width, map_height, warp_tiles = read_map(self.pyboy)
                retry_ctn+=1
                # if retry_ctn > 5:
                #     break
                if not astar_2wide(walk_matrix, (px, py), goal_xy):
                    path_dict={}
                    break
                else:
                    if retry_ctn % 4 == 0:
                        self.run_unstuck_agent()
                        
                    path_dict = path_finder(self.pyboy, goal=goal_xy, astar_2=True)
                    path_dict["goal_xy"] = goal_xy
                    print(f"PERSISTENT_GOAL: {retry_ctn}" )
                map_id = get_current_map(self.pyboy)
            # last_move = path_dict["prev_move"]
            if dest_key == "north":
                self.skills.execute({"type": "GO_UP"})
                self.skills.execute({"type": "GO_UP"})
                self.skills.execute({"type": "GO_UP"})
                print("UP_EXTRA")
            elif dest_key == "south":
                self.skills.execute({"type": "GO_DOWN"})
                self.skills.execute({"type": "GO_DOWN"})
                self.skills.execute({"type": "GO_DOWN"})
                print("DOWN_EXTRA")
            elif dest_key == "east":
                self.skills.execute({"type": "GO_RIGHT"})
                self.skills.execute({"type": "GO_RIGHT"})
                self.skills.execute({"type": "GO_RIGHT"})
                print("RIGHT_EXTRA")
            elif dest_key == "west":
                self.skills.execute({"type": "GO_LEFT"})
                self.skills.execute({"type": "GO_LEFT"})
                self.skills.execute({"type": "GO_LEFT"})
                print("LEFT_EXTRA")
            for _ in range(60):  # wait a few frames for movement
                self.pyboy.tick()

        elif fnmatch.fnmatch(CUSTOM_DEST, "*talk*"):
            match = re.search(r"'([^']*)'", CUSTOM_DEST)
            dest_key = match.group(1)
            print(f"DEST_KEY: {dest_key}")
            npc_xy = get_npc_coords(map_filename)
            npc_coords = []
            for npc in npc_xy:
                if npc.get("name")==dest_key:
                    if npc.get("text")[-1] != '2':
                        npc_coords.append((npc.get("x"), npc.get("y")))
            for coords in npc_coords:
                print(f"GOAL: {coords}")  
                goal_xy = coords
                try:
                    map_id, px, py, direction = get_player_position(self.pyboy)
                    walk_matrix, map_width, map_height, warp_tiles = read_map(self.pyboy)
                    print(f"Player at map {map_id}, X={px}, Y={py}, Looking={direction}") #(0: down, 4: up, 8: left, 12: right)
                    walk_matrix[py][px] = 'P' #player location
                    walk_matrix[goal_xy[1]][goal_xy[0]] = 'G' #goal location
                except:
                    pass
                path_dict = path_finder(self.pyboy, goal=goal_xy) #{"prev_move":prev_move, "try_next_xy":try_next_xy}
                if not path_dict["try_next_xy"]:
                    path_dict["goal_xy"] = goal_xy
                    break
            # last_move = path_dict["prev_move"]
            self.skills.execute({"type": "PRESS_A"})
            print("START_DIALOG")
            for _ in range(60):  # wait a few frames for movement
                self.pyboy.tick()

        else:
            path_dict = {}


        return path_dict





