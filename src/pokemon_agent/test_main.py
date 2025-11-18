# import json
# with open('src/pokemon_agent/utils/ref_data/MOVES_INDEX.json', 'r') as f:
#     MOVES_INDEX = json.load(f)

# player_move1_dict = next((d for d in MOVES_INDEX if d['move_id'] == 10), None)
# print(player_move1_dict)






from pyboy import PyBoy
import cv2
ROM_PATH = 'ROMS/pokemon_red.gb'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_midfight.sav'
from agents.goals_agent import *
def main():
    print("NONE")
    
    
    # # Use headless for fastest "null", or use "SDL2" if you want a window or "OpenGL"
    # pyboy = PyBoy(ROM_PATH, window="SDL2")
    # # Optionally set unlimited speed
    # # pyboy.set_emulation_speed(0)
    # # Load Save State
    # with open(LOAD_STATE_PATH, "rb") as f:
    #         pyboy.load_state(f)

    # frame = 0

    # while pyboy.tick():
    #     frame = pyboy.screen.ndarray
    #     pyboy.button_press("a")
    #     for _ in range(1):
    #         pyboy.tick(5)
    #     pyboy.button_release("a")
    #     # Allow at least one more tick so the command registers
    #     pyboy.tick()
    #     cv2.imwrite("dev_files/frame_test2.png", frame)
    #     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #     y1, y2, x1, x2 = (104, 137, 6, 154) #152
    #     img= gray[y1:y2, x1:x2]
    #     cv2.imwrite("dev_files/dialog_region2.png", img)

    #     y1, y2, x1, x2 = (90, 144, 35, 160)
    #     img= gray[y1:y2, x1:x2]
    #     cv2.imwrite("dev_files/menu_region2.png", img)
    # pyboy.stop()
        


if __name__ == "__main__":
    main()



# import cv2
# import pytesseract
# from pytesseract import Output

# # `img` should be the cropped dialog region (BGR or grayscale)
# img = cv2.imread("dev_files/dialog_region.png")
# # run Tesseract with data output
# data = pytesseract.image_to_data(img, output_type=Output.DICT, config="--psm 6")
# for i, text in enumerate(data['text']):
#     if text.strip():
#         print(f"word:{text!r} conf:{data['conf'][i]}")