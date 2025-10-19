from pyboy import PyBoy#, WindowEvent
from perception import PokemonPerceptionAgent
from planner import SimplePlanner
from skills import SkillExecutor
import time

ROM_PATH = 'ROMS/pokemon_red.gb'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_midfight.sav'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'
# SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'

def main():
    # Use headless for fastest "null", or use "SDL2" if you want a window or "OpenGL"
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    # Optionally set unlimited speed
    # pyboy.set_emulation_speed(0)


    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    
    with open('src/pokemon_agent/saves/dialog_log.txt', 'w') as file:
        file.write('====== Saved Dialog ======\n')

    perception = PokemonPerceptionAgent(pyboy)
    planner = SimplePlanner() #LLM Step eventually
    skills = SkillExecutor(pyboy)

    frame = 0
    try:
        # if frame % 10 == 0:
        
        while pyboy.tick(120):  # returns False when ROM done / exit 60
            # if frame < 2500:
            #     state = {}
            # else:
            #     state = perception.get_game_state()
            # if frame < 3800:
            #     plan = planner.gamestart_plan(frame)
            # else:
            #     plan = planner.plan(state, frame)
            if frame < 500:
                state = perception.get_game_state()
                plan = planner.fightstart_plan(frame)
            elif frame < 400:
                state = perception.get_game_state()
                plan = planner.findwildpokemon_plan(frame)
            else:
                state = perception.get_game_state()
                plan = planner.plan(state, frame)
            status = skills.execute(plan, state)

            # if frame % 100 == 0:
                # print(f"[frame {frame}] scene={state.get('scene')} plan={plan.get('type')} status={status}")
            print(f"\n\n[frame {frame}]     \nstatus={status}     \nSTATE: {state}\n")
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
    main()