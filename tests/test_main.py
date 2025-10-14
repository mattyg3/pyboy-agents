# import json
# with open('src/pokemon_agent/utils/ref_data/MOVES_INDEX.json', 'r') as f:
#     MOVES_INDEX = json.load(f)

# player_move1_dict = next((d for d in MOVES_INDEX if d['move_id'] == 10), None)
# print(player_move1_dict)

from pyboy import PyBoy
import cv2
ROM_PATH = 'ROMS/pokemon_red.gb'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_midfight.sav'

def main():
    # Use headless for fastest "null", or use "SDL2" if you want a window or "OpenGL"
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    # Optionally set unlimited speed
    # pyboy.set_emulation_speed(0)
    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    frame = 0

    while pyboy.tick():
        frame = pyboy.screen.ndarray
        pyboy.button_press("a")
        for _ in range(1):
            pyboy.tick(5)
        pyboy.button_release("a")
        # Allow at least one more tick so the command registers
        pyboy.tick()
        cv2.imwrite("dev_files/frame_test.png", frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        y1, y2, x1, x2 = (104, 144, 2, 160) #152
        img= gray[y1:y2, x1:x2]
        cv2.imwrite("dev_files/dialog_region.png", img)
        y1, y2, x1, x2 = (90, 144, 35, 160)
        img= gray[y1:y2, x1:x2]
        cv2.imwrite("dev_files/menu_region.png", img)
    pyboy.stop()
        


if __name__ == "__main__":
    main()