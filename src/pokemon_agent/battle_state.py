import cv2
import pytesseract
from collections import deque
import re

# ---------- CONFIG ----------
UPSCALE = 2
TEXT_WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?.',:; "
HISTORY_SIZE = 20
REGIONS = {
    # "dialog":  (104, 144, 2, 160),
    "menu":    (90, 144, 35, 160),
    # "player_hp": (64, 72, 100, 152),
    # "enemy_hp":  (16, 24, 96, 152),
}
# ----------------------------

class BattleStateTracker:
    def __init__(self):
        # self.in_battle = False
        # self.turn = None
        # self.player_hp = None
        # self.enemy_hp = None
        self.menu_state = None
        # self.last_event = None

    def update_from_ocr(self, text_data):
        # dialog = text_data.get("dialog", "").upper()
        menu = text_data.get("menu", "").upper()
        # event = None

        # # --- Detect battle start/end ---
        # if "WILD" in dialog or "ENEMY" in dialog:
        #     if not self.in_battle:
        #         self.in_battle = True
        #         event = "Battle started!"
        # elif "GAINED" in dialog or "DEFEATED" in dialog:
        #     if self.in_battle:
        #         self.in_battle = False
        #         event = "Battle ended!"

        # # --- Detect turns ---
        # if "USED" in dialog and "ENEMY" in dialog:
        #     self.turn = "enemy"
        #     event = f"Enemy action: {dialog}"
        # elif "USED" in dialog:
        #     self.turn = "player"
        #     event = f"Player action: {dialog}"


        # --- Detect menu options ---
        if any(x in menu for x in ["FIGHT", "ITEM", "RUN", "POKEMON"]):
            self.menu_state = "battle_menu"
        elif menu == "":
            self.menu_state = None


        # # Record event
        # if event:
        #     self.last_event = event


    def summary(self):
        return {
            # "in_battle": self.in_battle,
            # "turn": self.turn,
            "menu_state": self.menu_state,
            # "last_event": self.last_event,
        }


class BattleTracker:
    def __init__(self, pyboy, frame):
        self.pyboy = pyboy
        self.frame=frame
        self.history = deque(maxlen=HISTORY_SIZE)
        self.last_texts = {k: "" for k in REGIONS.keys()}
        self.state = BattleStateTracker()

    def get_region(self, region_name):
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        y1, y2, x1, x2 = REGIONS[region_name]
        return gray[y1:y2, x1:x2]

    def preprocess(self, img):
        upscaled = cv2.resize(img, None, fx=UPSCALE, fy=UPSCALE, interpolation=cv2.INTER_NEAREST)
        _, thresh = cv2.threshold(upscaled, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return thresh

    def ocr_text(self, img):
        config = f'--psm 6 --oem 3 -c tessedit_char_whitelist={TEXT_WHITELIST}'
        text = pytesseract.image_to_string(img, config=config)
        return text.replace("\n", " ").strip()

    def read_regions(self):
        region_texts = {}
        for name in REGIONS:
            img = self.get_region(name)
            proc = self.preprocess(img)
            text = self.ocr_text(proc)
            region_texts[name] = text
        return region_texts

    def detect_changes(self, region_texts):
        new_texts = {}
        for name, text in region_texts.items():
            if text and text != self.last_texts[name]:
                new_texts[name] = text
                self.last_texts[name] = text
                if text not in self.history:
                    self.history.append(f"{name}: {text}")
        return new_texts

    def read_frame(self):
        region_texts = self.read_regions()
        new_texts = self.detect_changes(region_texts)

        if new_texts:
            self.state.update_from_ocr(region_texts)

        return self.state.summary()

