from pyboy import PyBoy#, WindowEvent
from perception import PokemonPerceptionAgent
# from planner import SimplePlanner
from skills import SkillExecutor
import time
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.runnables.config import RunnableConfig
from agents.pathing_agent import *

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
    # pyboy.set_emulation_speed(0)

    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    
    with open('src/pokemon_agent/saves/dialog_log.txt', 'w') as file:
        file.write('====== Saved Dialog ======\n')

    # ------ Define State ------
    class AgentState(TypedDict):
        messages: list[dict[str, Any]]
        pathing_info: dict[Any]
        destination: dict[Any]

    def create_agent_state(
            messages=[],
            pathing_info={},
            destination={},
    ) -> AgentState:
        return AgentState(
            messages=messages, 
            pathing_info=pathing_info,
            destination=destination,
        )
    # ------ Define Nodes ------
    def pathing_node(state: AgentState):
        return pathing_agent(state)
    # ------ Define Workflow ------
    workflow = StateGraph(state_schema=AgentState)
    workflow.add_node("pathing", pathing_node)
    workflow.set_entry_point("pathing")
    workflow.add_edge("pathing", END)
    # ------ Compile Workflow ------
    app = workflow.compile()


    perception = PokemonPerceptionAgent(pyboy)
    # planner = SimplePlanner() #LLM Step eventually
    skills = SkillExecutor(pyboy)

    frame = 0
    try:
        # if frame % 10 == 0:
        
        while pyboy.tick():  # returns False when ROM done / exit 60, 100
            # Get state
            percept_state = perception.get_game_state()
            walkable_grid, map_width, map_height, warp_tiles = read_map(pyboy)
            map_id, px, py, direction = get_player_position(pyboy)
            
            print(f"[frame {frame}]")
            print(f"Current map={map_id}, map=(Width: {map_width}, Height: {map_height}) ,player=(Width: {px}, Height: {py})")
            # walkable_grid[py][px] = "PLAYER"
            # print("\nWalkable tile matrix ('.' = walkable, '#' = blocked):")
            # print_tile_walk_matrix(walkable_grid)
            # walkable_grid_clean = "\n".join(
            #     # "".join("PLAYER" if cell in ("P", "PLAYER") else str(cell) for cell in row) #
            #     "".join("PLAYER" if cell in ("P", "PLAYER") else "." if cell else "#" for cell in row)
            #     for row in walkable_grid
            # )
            # walkable_grid = 
            # rows = []
            # # rows.append(str("#"*map_width))
            # for row in walkable_grid:
            #     # line = ""
            #     line = []
            #     for cell in row:
            #         if cell in ("P", "PLAYER"):
            #             # line += "P"
            #             line.append("P")
            #         # elif cell in ("W","WARP"):
            #         #     # line += "W"
            #         #     line.append("W")
            #         elif cell:
            #             # line += "-"
            #             line.append("-")
            #         else:
            #             # line += "#"
            #             line.append("#")
            #     # line += "#"
            #     rows.append(line)
            # # rows.append(str("#"*map_width))
            # # walkable_grid_clean = "\n".join(rows)
            # walkable_grid_clean = rows
            def go_to_destination_xy(CUSTOM_DEST):
                import fnmatch
                import re
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
                elif fnmatch.fnmatch(CUSTOM_DEST, "*move*"):
                    match = re.search(r"'([^']*)'", CUSTOM_DEST)
                    dest_key = match.group(1).lower() #north, south, east, west
                    print(f"DEST_KEY: {dest_key}")
                    connection_coords = get_map_connections(map_id, dest_key) #ADD RETRY FOR ALL POSSIBLE CONNECTIONS
                    # if dest_key == "north":
                    #     formated_coords = (connection_coords[0][0], connection_coords[0][1]-1)
                    formated_coords = (connection_coords[0][0], connection_coords[0][1])
                    print(f"GOAL: {formated_coords}")
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
                    for _ in range(10):  # wait a few frames for movement
                        pyboy.tick()

            if frame==0:
                # CUSTOM_DEST="Enter 'REDS_HOUSE_1F'" 
                # CUSTOM_DEST="Enter 'BLUES_HOUSE'" 
                CUSTOM_DEST="Move to 'NORTH'" #leave pallettown to route1
                go_to_destination_xy(CUSTOM_DEST)
                
                CUSTOM_DEST="Move to 'NORTH'" #go through route1
                go_to_destination_xy(CUSTOM_DEST)

            # else:
            #     pass

            # state = create_agent_state(walkable_grid=walkable_grid_clean, grid_width=map_width, grid_height=map_height, start_xy=(px,py), destination_wanted=CUSTOM_DEST)

            # pathing_info_dict = {
            #     "player_position": [px, py],
            #     "known_door_tiles": warp_tiles,
            #     "map": walkable_grid_clean,
            #     "task": CUSTOM_DEST
            # }
            # state = create_agent_state(pathing_info=pathing_info_dict)
            # # Initial full pipeline run
            # config = RunnableConfig(recursion_limit=50) #max number of graph nodes to process
            # state = app.invoke(state, config) 
            # dest_goal = (state["destination"].get("dest_x"), state["destination"].get("dest_y"))
            # print(f"GOAL: {dest_goal}")
            # if frame==0:
            #     path_finder(pyboy, goal=(10,11)) #dest_goal
            # else:
            #     pass
            # pyboy.stop()
            # if frame < 2500:
            #     state = {}
            # else:
            #     state = perception.get_game_state()
            # if frame < 3800:
            #     plan = planner.gamestart_plan(frame)
            # else:
            #     plan = planner.plan(state, frame)
            # if frame < 1000:
            #     state = perception.get_game_state()
            #     plan = planner.fightstart_plan(frame)
            # # elif frame < 900:
            # #     state = perception.get_game_state()
            # #     plan = planner.findwildpokemon_plan(frame)
            # else:
            #     state = perception.get_game_state()
            #     plan = planner.plan(state, frame)
            # status = skills.execute(plan) #, state

            # if frame % 100 == 0:
                # print(f"[frame {frame}] scene={state.get('scene')} plan={plan.get('type')} status={status}")
            # print(f"\n\n[frame {frame}] \nSTATE: {percept_state}\n") #\nstatus={status}  
                # print(pyboy.memory[0xD014])

            

            # if frame>2000:
            #     break

            # optional: small sleep to avoid hogging CPU unnecessarily



            frame += 1
            time.sleep(0.001)
        # else:
        #     frame+=9
    finally:
        print(f"Raw Dialog History: {perception.dialog_history}")
        with open(SAVE_STATE_PATH, "wb") as f:
            pyboy.save_state(f)
        pyboy.stop()
        print("Stopped emulator.")

if __name__ == "__main__":
    run()