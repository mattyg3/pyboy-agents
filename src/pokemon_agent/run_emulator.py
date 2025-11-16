from pyboy import PyBoy#, WindowEvent
from perception import DialogPerception, DialogFlag #PokemonPerceptionAgent, 
# from planner import SimplePlanner
from skills import SkillExecutor
import time
# from typing import Any, TypedDict, Annotated
# from langgraph.graph import StateGraph, END
from langchain_core.runnables.config import RunnableConfig
# from agents.pathing_agent import *
from path_finder import *
from agents.battle_agent import  create_battle_agent_state, BattleAgent
from agents.pathing_agent import PathingAgent
from agents.goals_agent import create_goal_agent_state, GoalsAgent
from agents.unstuck_agent import create_unstuck_agent_state, UnstuckAgent
import fnmatch
import cv2
import lmstudio as lms
# from progress_tracking import ProgressTracker

ROM_PATH = 'ROMS/pokemon_red.gb'
# SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV.sav'
# SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV_oak_task.sav'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV_got_townmap.sav'
# LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'
# LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'
# SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'
# LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV_oak_task.sav'

# # ------ LangSmith Set-Up ------
# import os
# import keyring
# SERVICE = "langsmith"
# USERNAME = "api_key"
# os.environ["LANGSMITH_API_KEY"] = keyring.get_password(SERVICE, USERNAME)
# os.environ["LANGSMITH_PROJECT"] = "pokemon_red_agent"
# os.environ["LANGSMITH_TRACING"] = "true"

def run(ROM_PATH=ROM_PATH, LOAD_STATE_PATH=LOAD_STATE_PATH, SAVE_STATE_PATH=SAVE_STATE_PATH):
    # Use headless for fastest "null", or use "SDL2" if you want a window or "OpenGL"
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    # Optionally set unlimited speed
    pyboy.set_emulation_speed(0)

    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    
    with open('src/pokemon_agent/saves/dialog_log.txt', 'w') as file:
        file.write('====== Saved Dialog ======\n')

    # Utilities
    # perception = PokemonPerceptionAgent(pyboy)
    skills = SkillExecutor(pyboy)
    # progress = ProgressTracker(pyboy)
   

    # Battle Agent
    battle_agent_state = create_battle_agent_state()
    battle_agent = BattleAgent(pyboy)
    battle_agent.compile_workflow(battle_agent_state)

    # Goal Agent
    goal_agent_state = create_goal_agent_state()
    goal_agent = GoalsAgent(pyboy)
    goal_agent.compile_workflow(goal_agent_state)

    # Pathing Agent
    pathing_agent = PathingAgent(pyboy)

    # Dialog
    dialog_flag = DialogFlag(pyboy)
    dialog_reader = DialogPerception(pyboy)

    # Unstuck Agent
    unstuck_agent_state = create_unstuck_agent_state()
    unstuck_agent = UnstuckAgent(pyboy)
    unstuck_agent.compile_workflow(unstuck_agent_state)

    frame = 0
    prev_iter = {
        "player_xy": (0,0),
        "last_action": None,
        "map_id": 0,
        "iter_counter": 0,
    }
    try:
        # if frame % 10 == 0:
        
        while pyboy.tick(100):  # returns False when ROM done / exit 60, 100
            # LONGTERM_GOAL = progress.check_progress()
            # print(f"LONGTERM_GOAL: {LONGTERM_GOAL}")
            
            # Get state
            # percept_state = perception.get_game_state()
            walkable_grid, map_width, map_height, warp_tiles = read_map(pyboy)
            map_id, px, py, direction = get_player_position(pyboy)
            
            map_label = get_map_label(map_id)
            # map_connections = get_all_map_connections(map_id)
            # map_doorways = get_warp_tiles(get_map_filename(map_id))
            print(f"[frame {frame}]")
            print(f"Current map={map_label}, Current mapID={map_id}, map=(Width: {map_width}, Height: {map_height}) ,player=(Width: {px}, Height: {py})")

            # if frame > 10:
            #     break

            
            battle_flag = BattleFlag(pyboy)
            battle_info = battle_flag.read_memory_state()       
            if dialog_flag.read_memory_state():
                # print("DIALOG_FLAG")
                while dialog_flag.read_memory_state():
                    skills.execute({"type": "PRESS_A"})
                    # print("PRESS_A: advance dialog")
                    for _ in range(200):  # wait 200 frames
                        pyboy.tick()
                    dialog_reader.read_dialog()
                    
                dialog_reader.log_dialog()
                # map_id, px, py, direction = get_player_position(pyboy)
                # if fnmatch.fnmatch(goal_agent_state["next_best_action"], "*talk*") and goal_xy in [(px + dx, py + dy) for dx in (-2,-1, 0, 1, 2) for dy in (-2,-1, 0, 1, 2)]: #and next to NPC
                #     # Goal Agent
                #     goal_agent_state = create_goal_agent_state()
                #     goal_agent = GoalsAgent(pyboy, preprompt=f'You just completed the previous goal: {goal_agent_state["next_best_action"]}!\nDecide the Next Best Action based on the Longterm Goal.')
                #     goal_agent.compile_workflow(goal_agent_state)
                #     # goal_agent_state = create_goal_agent_state()
                #     config = RunnableConfig(recursion_limit=500) #max number of graph nodes to process
                #     goal_agent_state = goal_agent.app.invoke(goal_agent_state, config)
                #     # print("GOALS_AGENT_FLAG")
                #     print(f"GOAL AGENT OUTPUT: {goal_agent_state["next_best_action"]}")
                #     last_move, goal_xy = pathing_agent.go_to_destination_xy(goal_agent_state["next_best_action"])



            elif battle_info["battle_type"] != 0:
                # print("BATTLE_FLAG")
                # Battle Agent
                battle_agent_state = create_battle_agent_state()
                # battle_agent = BattleAgent(pyboy)
                # battle_agent.compile_workflow(battle_agent_state)
                # battle_agent_state = create_battle_agent_state()
                config = RunnableConfig(recursion_limit=500) #max number of graph nodes to process
                battle_agent_state = battle_agent.app.invoke(battle_agent_state, config)

            else:
                try:
                    # Goal Agent
                    goal_agent_state = create_goal_agent_state()
                    # goal_agent = GoalsAgent(pyboy)
                    # goal_agent.compile_workflow(goal_agent_state)
                    # goal_agent_state = create_goal_agent_state()
                    config = RunnableConfig(recursion_limit=500) #max number of graph nodes to process
                    goal_agent_state = goal_agent.app.invoke(goal_agent_state, config)
                    # print("GOALS_AGENT_FLAG")
                    print(f"GOAL AGENT OUTPUT: {goal_agent_state["next_best_action"]}")
                    path_dict = pathing_agent.go_to_destination_xy(goal_agent_state["next_best_action"]) #last_move, goal_xy
                    # CHECK IF PLAYER STUCK
                    map_id, px, py, direction = get_player_position(pyboy)
                    curr_iter = {
                    "player_xy": (px,py),
                    "last_action": path_dict["prev_move"],
                    "map_id": map_id,
                    "iter_counter": prev_iter["iter_counter"],
                    }
                    # print(f"LAST ITERATION: {prev_iter}")
                    # print(f"CURRENT ITERATION: {curr_iter}")
                    if curr_iter["last_action"] == prev_iter["last_action"] and curr_iter["map_id"] == prev_iter["map_id"] and  (curr_iter["player_xy"] == prev_iter["player_xy"] or curr_iter["player_xy"] in [(px + dx, py + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]): #
                    #goal in [(px + dx, py + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
                        # print("PASSED_IF_STMT")
                        iter_counter = prev_iter["iter_counter"]+1
                        # if iter_counter > 1:
                        if iter_counter > 0:
                                # Unstuck Agent
                            unstuck_agent_state = create_unstuck_agent_state()
                            # unstuck_agent = UnstuckAgent(pyboy)
                            # unstuck_agent.compile_workflow(unstuck_agent_state)
                            # unstuck_agent_state = create_unstuck_agent_state()
                            unstuck_agent_state["messages"] = []
                            # print("CREATED_STATE")
                            screen_frame = pyboy.screen.ndarray
                            cv2.imwrite("src/pokemon_agent/saves/unstuck_agent_frame.png", screen_frame)
                            unstuck_agent_state["screenshot"] = lms.prepare_image("src/pokemon_agent/saves/unstuck_agent_frame.png")
                            # print(unstuck_agent_state["screenshot"])
                            render_map_png(map_id, (px,px), path_dict["goal_xy"], save_path="src/pokemon_agent/saves/render_map.png")
                            unstuck_agent_state["map_render"] = lms.prepare_image("src/pokemon_agent/saves/render_map.png")
                            unstuck_agent_state["map_render"] = None

                            if fnmatch.fnmatch(goal_agent_state["next_best_action"], "*last_map*"):
                                unstuck_agent_state["attempted_goal"] = "exit the building"
                                unstuck_agent_state["map_render"] = None
                            else:
                                unstuck_agent_state["attempted_goal"]=goal_agent_state["next_best_action"]
                            # print(f"SET_PREV_GOAL: {unstuck_agent_state}")
                            config = RunnableConfig(recursion_limit=4) #max number of graph nodes to process
                            unstuck_agent_state = unstuck_agent.app.invoke(unstuck_agent_state, config)
                            # print(f"AGENT_STATE: {unstuck_agent_state}")
                            # last_move = pathing_agent.go_to_destination_xy(goal_agent_state["next_best_action"])
                            try:
                                # print(f"CORRECTIVE_ACTIONS: {unstuck_agent_state["corrective_action"]}")
                                for action in unstuck_agent_state["corrective_action"]: #{"type": "GO_DOWN"}
                                    skills.execute(action)
                                    # print("PRESS_A: advance dialog")
                                    for _ in range(10):  # wait 200 frames
                                        pyboy.tick()
                            except Exception as e: 
                                print(e)
                                pass

                        prev_iter = {
                        "player_xy": (px,py),
                        "last_action": path_dict["prev_move"],
                        "map_id": map_id,
                        "iter_counter": iter_counter,
                        }
                    else: #reset counter
                        prev_iter = {
                            "player_xy": (px,py),
                            "last_action": path_dict["prev_move"],
                            "map_id": map_id,
                            "iter_counter": 0,
                            }

                    # map_id, px, py, direction = get_player_position(pyboy)
                    # if fnmatch.fnmatch(goal_agent_state["next_best_action"], "*talk*") and goal_xy in [(px + dx, py + dy) for dx in (-2,-1, 0, 1, 2) for dy in (-2,-1, 0, 1, 2)]: #and next to NPC
                    #     print("PASSED IF STMT")
                    #     # Goal Agent
                    #     goal_agent_state = create_goal_agent_state()
                    #     goal_agent = GoalsAgent(pyboy, preprompt=f'You just completed the previous goal: {goal_agent_state["next_best_action"]}!\nDecide the Next Best Action based on the Longterm Goal.')
                    #     goal_agent.compile_workflow(goal_agent_state)
                    #     # goal_agent_state = create_goal_agent_state()
                    #     config = RunnableConfig(recursion_limit=500) #max number of graph nodes to process
                    #     goal_agent_state = goal_agent.app.invoke(goal_agent_state, config)
                    #     # print("GOALS_AGENT_FLAG")
                    #     print(f"GOAL AGENT OUTPUT: {goal_agent_state["next_best_action"]}")
                    #     last_move, goal_xy = pathing_agent.go_to_destination_xy(goal_agent_state["next_best_action"])


                except Exception as e: 
                    print(e)
                    pass
                

            # elif frame==0:
            #     # CUSTOM_DEST="Enter 'REDS_HOUSE_1F'" 
            #     # CUSTOM_DEST="Enter 'BLUES_HOUSE'" 
            #     # CUSTOM_DEST="Move to 'NORTH'" #leave pallettown to route1
            #     # pathing_agent.go_to_destination_xy(CUSTOM_DEST)
                
            #     # CUSTOM_DEST="Move to 'NORTH'" #go through route1
            #     # pathing_agent.go_to_destination_xy(CUSTOM_DEST)

            #     CUSTOM_DEST="Enter  'OAKS_LAB'" 
            #     pathing_agent.go_to_destination_xy(CUSTOM_DEST)

            #     CUSTOM_DEST="Talk to  'OAK'" 
            #     pathing_agent.go_to_destination_xy(CUSTOM_DEST)
            #     # percept_state = perception.get_game_state()
            
            # else:
            #     pass


            
            if frame > 30:
                break
            frame += 1
            time.sleep(0.001)
    finally:
        # print(f"Raw Dialog History: {perception.dialog_history}")
        with open(SAVE_STATE_PATH, "wb") as f:
            pyboy.save_state(f)
        pyboy.stop()
        print("Stopped emulator.")

if __name__ == "__main__":
    run()