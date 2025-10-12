# perception.py
# Perception: reads PyBoy screen and (optionally) RAM to return a compact structured state.
# NOTE: This is intentionally conservative: uses pixel heuristics and PyBoy.get_memory_value for demonstration.
# You should adapt RAM addresses for your ROM.
# perception.py
# import numpy as np
# import cv2
# from PIL import Image

# class Perception:
#     def __init__(self, pyboy):
#         self.pyboy = pyboy

#     def _get_frame_rgb(self):
#         # pyboy.screen.image is a PIL Image view of the screen
#         img = self.pyboy.screen.image  # PIL Image
#         # Make a copy or convert to np array
#         return np.array(img)

#     def _simple_text_detection(self, frame):
#         hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
#         v = hsv[:, :, 2]
#         _, th = cv2.threshold(v, 200, 255, cv2.THRESH_BINARY)
#         h, w = th.shape
#         bottom = th[int(h * 0.6):, :]
#         pct = (bottom > 0).mean()
#         return pct > 0.02

#     def parse_state(self):
#         frame = self._get_frame_rgb()
#         has_text = self._simple_text_detection(frame)

#         # Heuristic: check a memory address to detect battle or overworld
#         # Example: using direct memory mapping (you must find correct addresses for your ROM)
#         try:
#             battle_flag = self.pyboy.memory[0xD163]  # placeholder; adjust as needed
#         except Exception:
#             battle_flag = None

#         if has_text:
#             scene = "text/menu"
#         else:
#             if battle_flag is not None and battle_flag > 0:
#                 scene = "battle"
#             else:
#                 scene = "overworld"

#         # Example of reading party HP slots (just demonstration)
#         party = []
#         for i in range(6):
#             try:
#                 hp = self.pyboy.memory[0xD000 + i]
#             except Exception:
#                 hp = None
#             if hp is None:
#                 break
#             party.append({"slot": i, "hp": int(hp)})

#         state = {
#             "scene": scene,
#             "has_text": has_text,
#             "party": party,
#         }
#         return state
    



import numpy as np
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import json
# Import Reference Data
with open('src/pokemon_agent/utils/ref_data/pokemon_ids.json', 'r') as f:
    POKEMON_NAMES = json.load(f)
    # POKEMON_NAMES = {hex(int(k, 16)): v for k, v in POKEMON_NAMES.items()}
    # print(POKEMON_NAMES)

with open('src/pokemon_agent/utils/ref_data/ram_addresses.json', 'r') as f:
    RAM_POINTERS = json.load(f)

# # Mapping of Pokémon IDs to names (small sample)
# POKEMON_NAMES = {
#     0x01: "Bulbasaur",
#     0x02: "Ivysaur",
#     0x03: "Venusaur",
#     0x04: "Charmander",
#     0x05: "Charmeleon",
#     0x06: "Charizard",
#     0x16: "Pidgey",
#     0x19: "Rattata",
#     # (you can extend this easily)
# }

def read_word(memory, addr):
    """Read 2 bytes little-endian"""
    low = memory[addr]
    high = memory[addr + 1]
    return (high << 8) | low

class PokemonPerceptionAgent:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.screen = self.pyboy.screen
        self.text_prev = ""
        print("PerceptionAgent with memory reading initialized.")

    def capture_frame(self):
        return self.screen.ndarray

    def read_text(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape
        text_region = gray[int(h*0.7):, :]
        text_region = cv2.threshold(text_region, 100, 255, cv2.THRESH_BINARY)[1]
        text = pytesseract.image_to_string(text_region, config='--psm 6').strip()
        return text
    
    def get_mem_pointer(self, pointer_name):
        return int(next(entry["address"] for entry in RAM_POINTERS["ram_addresses"] if entry["name"] == pointer_name), 16)

    def read_memory_state(self):
        mem = self.pyboy.memory
        x = mem[self.get_mem_pointer("player_x")]
        y = mem[self.get_mem_pointer("player_y")]
        map_id = mem[self.get_mem_pointer("current_map_id")]

        # Player Pokémon stats
        player_species = mem[self.get_mem_pointer("poke_species")] 
        #D013
        player_species = mem[0xCFD9]#read_word(mem, 0xD013)#mem[0xD013]
        player_type1 = mem[self.get_mem_pointer("poke_type1")] #read_word(mem, self.get_mem_pointer("p1_type1")) # 
        player_type2 = mem[self.get_mem_pointer("poke_type2")] #read_word(mem, self.get_mem_pointer("p1_type2")) # mem[self.get_mem_pointer("p1_type2")]
        player_hp = read_word(mem, self.get_mem_pointer("poke_current_hp"))
        player_hp_max = read_word(mem, self.get_mem_pointer("poke_max_hp"))
        # print(f"wPartyMon1Nick: {read_word(mem, 0xd2b5)}")

        # Enemy Pokémon stats
        enemy_species = mem[self.get_mem_pointer("enemy_species")]
        enemy_type1 = mem[self.get_mem_pointer("enemy_type1")] 
        enemy_type2 = mem[self.get_mem_pointer("enemy_type2")]
        enemy_hp = read_word(mem, self.get_mem_pointer("enemy_current_hp"))
        enemy_hp_max = read_word(mem, self.get_mem_pointer("enemy_max_hp"))
        enemy_name = POKEMON_NAMES.get(enemy_species, "Unknown")

        return {
            "player": {
                "position": {"x": x, "y": y, "map_id": map_id},
                "pokemon": {
                    "species": player_species,
                    "type1": player_type1,
                    "type2": player_type2,
                    "hp": player_hp,
                    "hp_max": player_hp_max,
                    "hp_ratio": round(player_hp / max(player_hp_max, 1), 2)
                },
            },
            "opponent": {
                "species": enemy_species,
                "type1": enemy_type1,
                "type2": enemy_type2,
                "name": enemy_name,
                "hp": enemy_hp,
                "hp_max": enemy_hp_max,
                "hp_ratio": round(enemy_hp / max(enemy_hp_max, 1), 2)
            }
        }

    def detect_mode(self, mem_state, text):
        if mem_state["opponent"]["hp_max"] > 0:
            return "battle"
        if "menu" in text.lower():
            return "menu"
        return "overworld"

    def get_game_state(self):
        frame = self.capture_frame()
        text = self.read_text(frame)
        mem_state = self.read_memory_state()
        mode = self.detect_mode(mem_state, text)

        state = {
            "scene": mode,
            "text_box": text,
            "player": mem_state["player"],
            "opponent": mem_state["opponent"],
        }

        return state

    def step(self):
        self.pyboy.tick()
        return self.get_game_state()

# if __name__ == "__main__":
#     agent = PokemonPerceptionAgent("PokemonRed.gb")

#     while not agent.pyboy.tick():
#         state = agent.get_game_state()
#         if state["text_box"] != agent.text_prev:
#             print(state)
#             agent.text_prev = state["text_box"]

