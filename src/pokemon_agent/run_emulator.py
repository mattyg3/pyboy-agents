from pyboy import PyBoy#, WindowEvent
from perception import PokemonPerceptionAgent, DialogPerception, DialogFlag
# from planner import SimplePlanner
from skills import SkillExecutor
import time
from typing import Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.runnables.config import RunnableConfig
# from agents.pathing_agent import *
from path_finder import *
from agents.battle_agent import  create_battle_agent_state, BattleAgent
from agents.pathing_agent import PathingAgent

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
    battle_agent_state = create_battle_agent_state()
    battle_agent = BattleAgent(pyboy)
    battle_agent.compile_workflow(battle_agent_state)

    # Pathing Agent
    pathing_agent = PathingAgent(pyboy)

    # Dialog
    dialog_flag = DialogFlag(pyboy)
    dialog_reader = DialogPerception(pyboy)

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

            if frame > 10:
                break

            
            battle_flag = BattleFlag(pyboy)
            battle_info = battle_flag.read_memory_state()       
            if dialog_flag.read_memory_state():
                while dialog_flag.read_memory_state():
                    skills.execute({"type": "PRESS_A"})
                    print("PRESS_A: advance dialog")
                    for _ in range(200):  # wait 200 frames
                        pyboy.tick()
                    dialog_reader.read_dialog()
                    
                dialog_reader.log_dialog()
                

            elif frame==0:
                # CUSTOM_DEST="Enter 'REDS_HOUSE_1F'" 
                # CUSTOM_DEST="Enter 'BLUES_HOUSE'" 
                # CUSTOM_DEST="Move to 'NORTH'" #leave pallettown to route1
                # pathing_agent.go_to_destination_xy(CUSTOM_DEST)
                
                # CUSTOM_DEST="Move to 'NORTH'" #go through route1
                # pathing_agent.go_to_destination_xy(CUSTOM_DEST)

                CUSTOM_DEST="Enter  'OAKS_LAB'" 
                pathing_agent.go_to_destination_xy(CUSTOM_DEST)

                CUSTOM_DEST="Talk to  'OAK'" 
                pathing_agent.go_to_destination_xy(CUSTOM_DEST)
                # percept_state = perception.get_game_state()
            elif battle_info["battle_type"] != 0:
                battle_agent_state = create_battle_agent_state()
                config = RunnableConfig(recursion_limit=500) #max number of graph nodes to process
                battle_agent_state = battle_agent.app.invoke(battle_agent_state, config)
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