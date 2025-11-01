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
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'
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
        # walkable_grid: list[Any]
        walkable_grid: str
        grid_width: int
        grid_height: int
        start_xy: tuple
        destination_wanted: str
        destination: tuple

    def create_agent_state(
            messages=[],
            # walkable_grid=[],
            walkable_grid=None,
            grid_width=None,
            grid_height=None,
            start_xy=None,
            destination_wanted=None,
            destination=None,
    ) -> AgentState:
        return AgentState(
            messages=messages, 
            walkable_grid=walkable_grid, 
            grid_width=grid_width,
            grid_height=grid_height,
            start_xy=start_xy, 
            destination_wanted=destination_wanted,
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
            walkable_grid, map_width, map_height = read_map(pyboy)
            walkable_grid_clean = "\n".join(
                "".join("PLAYER" if cell in ("P", "PLAYER") else str(cell) for cell in row)
                for row in walkable_grid
            )
            map_id, px, py, direction = get_player_position(pyboy)
            CUSTOM_DEST="Exit the building through bottom of map, exit area is middle of the bottom row"
            state = create_agent_state(walkable_grid=walkable_grid_clean, grid_width=map_width, grid_height=map_height, start_xy=(px,py), destination_wanted=CUSTOM_DEST)
            # Initial full pipeline run
            config = RunnableConfig(recursion_limit=50) #max number of graph nodes to process
            state = app.invoke(state, config) 
            dest_goal = (state["destination"].get("destination_x"), state["destination"].get("destination_y"))
            print(f"GOAL: {dest_goal}")
            path_finder(pyboy, goal=dest_goal)
            pyboy.stop()
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
            print(f"\n\n[frame {frame}] \nSTATE: {percept_state}\n") #\nstatus={status}  
                # print(pyboy.memory[0xD014])
            frame += 1

            if frame>2000:
                break

            # optional: small sleep to avoid hogging CPU unnecessarily
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