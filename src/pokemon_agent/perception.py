# perception.py
# Perception: reads PyBoy screen and (optionally) RAM to return a compact structured state.
# NOTE: This is intentionally conservative: uses pixel heuristics and PyBoy.get_memory_value for demonstration.
# You should adapt RAM addresses for your ROM.
# perception.py
import numpy as np
import cv2
from PIL import Image

class Perception:
    def __init__(self, pyboy):
        self.pyboy = pyboy

    def _get_frame_rgb(self):
        # pyboy.screen.image is a PIL Image view of the screen
        img = self.pyboy.screen.image  # PIL Image
        # Make a copy or convert to np array
        return np.array(img)

    def _simple_text_detection(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        v = hsv[:, :, 2]
        _, th = cv2.threshold(v, 200, 255, cv2.THRESH_BINARY)
        h, w = th.shape
        bottom = th[int(h * 0.6):, :]
        pct = (bottom > 0).mean()
        return pct > 0.02

    def parse_state(self):
        frame = self._get_frame_rgb()
        has_text = self._simple_text_detection(frame)

        # Heuristic: check a memory address to detect battle or overworld
        # Example: using direct memory mapping (you must find correct addresses for your ROM)
        try:
            battle_flag = self.pyboy.memory[0xD163]  # placeholder; adjust as needed
        except Exception:
            battle_flag = None

        if has_text:
            scene = "text/menu"
        else:
            if battle_flag is not None and battle_flag > 0:
                scene = "battle"
            else:
                scene = "overworld"

        # Example of reading party HP slots (just demonstration)
        party = []
        for i in range(6):
            try:
                hp = self.pyboy.memory[0xD000 + i]
            except Exception:
                hp = None
            if hp is None:
                break
            party.append({"slot": i, "hp": int(hp)})

        state = {
            "scene": scene,
            "has_text": has_text,
            "party": party,
        }
        return state
