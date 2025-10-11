# Minimal runner: uses PyBoy to run an emulator loop, publishes state to planner, runs skill macros.

from pyboy import PyBoy#, WindowEvent
from perception import Perception
from planner import SimplePlanner
from skills import SkillExecutor
import time

ROM_PATH = "C:/Users/surff/Desktop/Pokemon ROMs/Pokemon_ Red Version/Pokemon - Red Version.gb"  


def main():
    # Use headless for fastest "null", or use "SDL2" if you want a window or "OpenGL"
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    # Optionally set unlimited speed
    # pyboy.set_emulation_speed(0)

    # Load Save State
    # START_SAVE = "C:/Users/surff/Desktop/Pokemon ROMs/Pokemon_ Red Version/Pokemon - Red Version_charmander.sav"
    # START_SAVE = "./saves/Pokemon - Red Version_charmander.sav"
    # START_SAVE = "src/pokemon_agent/saves/Pokemon - Red Version_charmander.sav"
    # pyboy.load_battery(START_SAVE)
    # with open(START_SAVE, "rb") as f:
    #     pyboy.cartridge.load_ram(f.read())

    perception = Perception(pyboy)
    planner = SimplePlanner()
    skills = SkillExecutor(pyboy)

    frame = 0
    try:
        while pyboy.tick():  # returns False when ROM done / exit
            state = perception.parse_state()
            plan = planner.plan(state)
            status = skills.execute(plan, state)

            if frame % 100 == 0:
                print(f"[frame {frame}] scene={state.get('scene')} plan={plan.get('type')} status={status}")
            frame += 1

            if frame==1000:
                break

            # optional: small sleep to avoid hogging CPU unnecessarily
            time.sleep(0.001)
    finally:
        # with open("saves/test_saves.sav", "wb") as f:
        #     f.write(pyboy.cartridge.save_ram())
        pyboy.stop()
        print("Stopped emulator.")

if __name__ == "__main__":
    main()