import cv2
import pytesseract
from collections import deque
import re
import numpy as np
import pickle

# ---------- CONFIG ----------
# UPSCALE = 2
# TEXT_WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" #!?.',:; 
HISTORY_SIZE = 20
REGIONS = {
    "dialog":  (104, 144, 2, 160),
    "menu":    (90, 144, 35, 160),
}
def load_templates_pkl(filename="src/pokemon_agent/utils/ref_data/font_templates.pkl"):
    with open(filename, "rb") as f:
        templates = pickle.load(f)
    print(f"✅ Loaded {len(templates)} templates from {filename}")
    return templates

TEMPLATES = load_templates_pkl()
# ----------------------------
class OverworldStateTracker:
    def __init__(self):
        self.dialog_text = None
        self.dialog_history = ''
        self.region = REGIONS["dialog"]
        self.upscale = 4

    def update_from_ocr(self, text_data):
        self.dialog_text = text_data.upper()
        self.dialog_history = f"{self.dialog_history}\n{self.dialog_text}" 
        
    def summary(self):
        return {
            "new_text": self.dialog_text,
            "dialog_history": self.dialog_history,

        }


class BattleStateTracker:
    def __init__(self):
        self.menu_state = None
        self.region = REGIONS["dialog"]
        self.upscale = 2

    def update_from_ocr(self, text_data):
        menu = text_data.upper()
        if any(x in menu for x in ["FIGHT", "ITEM", "RUN", "POKEMON"]):
            self.menu_state = "battle_menu"
        elif menu == "":
            self.menu_state = None

    def summary(self):
        return {
            "menu_state": self.menu_state,
        }


class OCR_Processing:
    def __init__(self, pyboy, frame, tracking):
        self.pyboy = pyboy
        self.frame=frame
        # self.history = ""#deque(maxlen=HISTORY_SIZE)
        self.last_texts = {k: "" for k in REGIONS.keys()}
        self.state = tracking #tracking class
        

    def get_region(self):
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        y1, y2, x1, x2 = self.state.region
        # extracted = []
        # for (y1, y2, x1, x2) in self.regions:
        #     # extracted.append(frame[y:y+h, x:x+w])
        #     extracted.append(gray[y1:y2, x1:x2])
        return gray[y1:y2, x1:x2]
        # return extracted

    # def preprocess(self, img):
    #     upscaled = cv2.resize(img, None, fx=self.state.upscale, fy=self.state.upscale, interpolation=cv2.INTER_NEAREST)
    #     _, thresh = cv2.threshold(upscaled, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    #     return thresh

    def preprocess(self, img):
        # img: BGR or grayscale numpy array (dialog region)
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # 1) sharpen slightly (optional)
        kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]], dtype=np.float32)
        gray = cv2.filter2D(gray, -1, kernel)

        # # 2) histogram equalization (CLAHE)
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        # gray = clahe.apply(gray)

        # # 3) upscale by nearest (preserve pixels)
        # up = cv2.resize(gray, None, fx=self.state.upscale, fy=self.state.upscale, interpolation=cv2.INTER_NEAREST)

        # # 4) adaptive threshold (handles subtle shading)
        # th = cv2.adaptiveThreshold(up, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #                         cv2.THRESH_BINARY, 11, 2)

        # # 5) optionally clear small noise and close glyph gaps
        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        # th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=1)
        # th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)

        return gray
    
    def match_text_region(self, region, TEMPLATES, threshold=0.99, space_threshold=1.5, line_threshold=10):
        """
        Match text from a given region using template matching.
        - region: grayscale image of the text area
        - templates: dict of character -> glyph
        - threshold: match quality threshold
        - space_threshold: horizontal spacing multiplier for spaces
        - line_threshold: vertical distance threshold for separating lines
        """
        # Binarize and invert
        # region = self.state.region.astype(np.uint8)
        region = cv2.threshold(region, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        matches = []
        for ch, tmpl in TEMPLATES.items():
            try:
                res = cv2.matchTemplate(region, tmpl, cv2.TM_CCOEFF_NORMED)
            except cv2.error:
                print("Template size:", tmpl.shape)
                print("Image size:", region.shape)
                continue

            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):  # (x, y)
                matches.append((pt[0], pt[1], ch, res[pt[1], pt[0]]))

        if not matches:
            return ""

        # Sort primarily by Y (line), then X (within line)
        matches.sort(key=lambda x: (x[1], x[0]))

        # Group into lines based on Y distance
        lines = []
        current_line = [matches[0]]
        for i in range(1, len(matches)):
            if abs(matches[i][1] - current_line[-1][1]) < line_threshold:
                current_line.append(matches[i])
            else:
                lines.append(current_line)
                current_line = [matches[i]]
        lines.append(current_line)

        # Sort each line by X position
        lines = [sorted(line, key=lambda x: x[0]) for line in lines]

        # Assemble text lines
        text_lines = []
        for line in lines:
            text = ""
            last_x = None
            for x, y, ch, score in line:
                tmpl_width = TEMPLATES[ch].shape[1]
                if last_x is not None and x - last_x > tmpl_width * space_threshold:
                    text += " "
                text += ch
                last_x = x
            text_lines.append(text.strip())

        return "\n".join(text_lines)


    # def ocr_text(self, img):
    #     config = f'--psm 6 --oem 3 -c tessedit_char_whitelist={TEXT_WHITELIST}'
    #     text = pytesseract.image_to_string(img, config=config)
    #     return text.replace("\n", " ").strip()

    # def ocr_from_regions(self, frame, templates):
    #     """
    #     Perform OCR over multiple regions using template matching.
    #     """
    #     results = []
    #     crops = get_region() 
    #     for crop in crops:
    #         text = match_text_region(crop, templates)
    #         results.append(text)
    #     return results

    def read_regions(self):
        img = self.get_region()
        proc = self.preprocess(img)
        text = self.match_text_region(proc, TEMPLATES)
        return text

    # def detect_changes(self, text):
    #     if text and text != self.last_texts:
    #         new_texts = text
    #         self.last_texts = text
    #         # if text not in self.history:
    #         #     self.history.append(f"{text}")
    #     else:
    #         new_texts = None
    #     return new_texts

    def read_frame(self):
        text = self.read_regions()
        self.state.update_from_ocr(text)
        # new_texts = self.detect_changes(text)
        # if new_texts:
        #     self.state.update_from_ocr(text)

        return self.state.summary()

