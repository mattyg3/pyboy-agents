from pyboy import PyBoy#, WindowEvent
from perception import PokemonPerceptionAgent
# from planner import SimplePlanner
from skills import SkillExecutor
import time
from typing import Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.runnables.config import RunnableConfig
# from agents.pathing_agent import *
from path_finder import *
from agents.battle_agent import  create_battle_agent_state, BattleAgent

ROM_PATH = 'ROMS/pokemon_red.gb'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV.sav'
# LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'
# LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'
# SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'

# ------ LangSmith Set-Up ------
import os
import keyring
SERVICE = "langsmith"
USERNAME = "api_key"
os.environ["LANGSMITH_API_KEY"] = keyring.get_password(SERVICE, USERNAME)
os.environ["LANGSMITH_PROJECT"] = "pokemon_red_agent"
os.environ["LANGSMITH_TRACING"] = "true"

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
    perception = PokemonPerceptionAgent(pyboy)
    skills = SkillExecutor(pyboy)
   

    # Battle Agent
    agent_state = create_battle_agent_state()
    battle_agent = BattleAgent(pyboy)
    battle_agent.compile_workflow(agent_state)

    # # ------ Define State ------
    # class AgentState(TypedDict):
    #     messages: list[dict[str, Any]]
    #     # messages: Annotated[list]
    #     pathing_info: dict[Any]
    #     destination: dict[Any]
    #     # battle_details: dict[Any]
    #     battle_thoughts: list[dict[str, Any]]
    #     battle_move: str
    #     prev_turn: int

    # def create_agent_state(
    #         messages=[],
    #         pathing_info={},
    #         destination={},
    #         # battle_details={},
    #         battle_thoughts=[],
    #         battle_move=None,
    #         prev_turn=-1,
    # ) -> AgentState:
    #     return AgentState(
    #         messages=messages, 
    #         pathing_info=pathing_info,
    #         destination=destination,
    #         # battle_details=battle_details,
    #         battle_thoughts=battle_thoughts,
    #         battle_move=battle_move,
    #         prev_turn=prev_turn,
    #     )
    # # ------ Define Nodes ------
    # def start_node(state: AgentState):
    #     for _ in range(60):  # wait 60 frames screen to load
    #         pyboy.tick()
    #     while True: # get through any opening dialog
    #         game_state = perception.get_game_state()
    #         if game_state.get("menu_state"):
    #             return state
    #         else:
    #             skills.execute({"type": "PRESS_A"})
    #             print("PRESS_A")
    #             for _ in range(5):  # wait 5 frames
    #                 pyboy.tick()
        
    # def routing_node(state: AgentState):
    #     battle_flag = BattleFlag(pyboy)
    #     battle_info = battle_flag.read_memory_state()
    #     if battle_info["battle_type"] != 0:
    #         print(f"BATTLE TYPE: {battle_info["battle_type"]}")
    #         print("ROUTING -> BATTLE")
    #         return "battle"
    #     else:
    #         print("ROUTING -> END")
    #         return "end"
        
    # def battle_action_node(state: AgentState):
    #     """
    #     # Possible Moves Dictionary
    #     - "Move #1"
    #     - "Move #2"
    #     - "Move #3"
    #     - "Move #4"
    #     - "Run"
    #     """
    #     # battle_flag = BattleFlag(pyboy)
    #     # battle_info = battle_flag.read_memory_state()
    #     # if state["prev_turn"] != battle_info["battle_turn"]:
    #     #     state["prev_turn"] = battle_info["battle_turn"]
    #     if state["battle_move"] == "Move #1":
    #         #Press Fight
    #         skills.execute({"type": "PRESS_A"})
    #         print("PRESS_A: Select 'Fight' Option")
    #         for _ in range(5):  # wait 5 frames
    #             pyboy.tick()
    #         #Press First Move
    #         skills.execute({"type": "PRESS_A"})
    #         print("PRESS_A: Select First Move")
    #         for _ in range(5):  # wait 5 frames
    #             pyboy.tick()
    #     # else:
    #     #     for _ in range(60):  # wait 60 frames
    #     #             pyboy.tick()
    #         # skills.execute({"type": "PRESS_A"})
    #         # print("\n...WAITING...PRESS_A")

    #     return state
        
            
    # # def pathing_node(state: AgentState):
    # #     return pathing_agent(state)
    # def battle_node(state: AgentState):
    #     return battle_agent(state, pyboy)
    # def routing(state: AgentState):
    #     # for _ in range(5):  # wait 5 frames
    #     #     pyboy.tick()
    #     # mem_state = perception.read_memory_state()
    #     # if mem_state["opponent"]["hp"] <= 0:
    #     #     skills.execute({"type": "PRESS_A"})
    #     #     print("PRESS_A: opponent hp <= 0")
    #     #     for _ in range(5):  # wait 5 frames
    #     #         pyboy.tick()
    #     return state
    # # ------ Define Workflow ------
    # workflow = StateGraph(state_schema=AgentState)
    # workflow.add_node("start", start_node)
    # workflow.add_node("routing", routing)
    # workflow.add_node("battle", battle_node)
    # workflow.add_node("battle_action", battle_action_node)
    
    # workflow.set_entry_point("start")
    # workflow.add_edge("start", "routing")
    # workflow.add_conditional_edges("routing", routing_node, 
    #                            {
    #                                "battle":"battle", 
    #                                "end":END
    #                                })
    # workflow.add_edge("battle", "battle_action")
    # workflow.add_edge("battle_action", "routing")
    # # ------ Compile Workflow ------
    # app = workflow.compile()


    

    frame = 0
    try:
        # if frame % 10 == 0:
        
        while pyboy.tick(100):  # returns False when ROM done / exit 60, 100
            # Get state
            # percept_state = perception.get_game_state()
            walkable_grid, map_width, map_height, warp_tiles = read_map(pyboy)
            map_id, px, py, direction = get_player_position(pyboy)
            
            print(f"[frame {frame}]")
            print(f"Current map={map_id}, map=(Width: {map_width}, Height: {map_height}) ,player=(Width: {px}, Height: {py})")

            def go_to_destination_xy(CUSTOM_DEST):
                import fnmatch
                import re
                map_id = get_current_map(pyboy)
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
                    path_finder(pyboy, goal=warps[0])
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
                        pyboy.tick()
                        
                    
                elif fnmatch.fnmatch(CUSTOM_DEST, "*move*"):
                    match = re.search(r"'([^']*)'", CUSTOM_DEST)
                    dest_key = match.group(1).lower() #north, south, east, west
                    print(f"DEST_KEY: {dest_key}")
                    connection_coords = get_map_connections(map_id, dest_key) #ADD RETRY FOR ALL POSSIBLE CONNECTIONS
                    print(f"connection_coords: {connection_coords}")
                    formated_coords = (connection_coords[0][0], connection_coords[0][1])
                    # print(f"GOAL(from connection key): {formated_coords}")
                    path_finder(pyboy, goal=formated_coords)
                    if dest_key == "north":
                        skills.execute({"type": "GO_UP"})
                        print("UP_EXTRA")
                    elif dest_key == "south":
                        skills.execute({"type": "GO_DOWN"})
                        print("DOWN_EXTRA")
                    elif dest_key == "east":
                        skills.execute({"type": "GO_RIGHT"})
                        print("RIGHT_EXTRA")
                    elif dest_key == "west":
                        skills.execute({"type": "GO_LEFT"})
                        print("LEFT_EXTRA")
                    for _ in range(60):  # wait a few frames for movement
                        pyboy.tick()

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
                    path_finder(pyboy, goal=npc_coords)
                    skills.execute({"type": "PRESS_A"})
                    print("START_DIALOG")
                    for _ in range(60):  # wait a few frames for movement
                        pyboy.tick()





            if frame > 10:
                break
            battle_flag = BattleFlag(pyboy)
            battle_info = battle_flag.read_memory_state()       
            if frame==0:
                # CUSTOM_DEST="Enter 'REDS_HOUSE_1F'" 
                # CUSTOM_DEST="Enter 'BLUES_HOUSE'" 
                CUSTOM_DEST="Move to 'NORTH'" #leave pallettown to route1
                go_to_destination_xy(CUSTOM_DEST)
                
                CUSTOM_DEST="Move to 'NORTH'" #go through route1
                go_to_destination_xy(CUSTOM_DEST)

                # CUSTOM_DEST="Enter  'OAKS_LAB'" 
                # go_to_destination_xy(CUSTOM_DEST)

                # CUSTOM_DEST="Talk to  'OAK'" 
                # go_to_destination_xy(CUSTOM_DEST)
                # percept_state = perception.get_game_state()
            elif battle_info["battle_type"] != 0:
                agent_state = create_battle_agent_state()
                config = RunnableConfig(recursion_limit=500) #max number of graph nodes to process
                agent_state = battle_agent.app.invoke(agent_state, config)
            else:
                pass

            frame += 1
            time.sleep(0.001)
    finally:
        print(f"Raw Dialog History: {perception.dialog_history}")
        with open(SAVE_STATE_PATH, "wb") as f:
            pyboy.save_state(f)
        pyboy.stop()
        print("Stopped emulator.")

if __name__ == "__main__":
    run()