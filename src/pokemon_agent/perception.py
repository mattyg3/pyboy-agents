
import numpy as np
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import json
# Import Reference Data
with open('src/pokemon_agent/utils/ref_data/POKEMON_NAMES.json', 'r') as f:
    POKEMON_NAMES = json.load(f)

with open('src/pokemon_agent/utils/ref_data/POKEMON_TYPES.json', 'r') as f:
    POKEMON_TYPES = json.load(f)

with open('src/pokemon_agent/utils/ref_data/ram_addresses.json', 'r') as f:
    RAM_POINTERS = json.load(f)


def read_word(memory, addr):
    """Read 2 bytes little-endian"""
    low = memory[addr]
    high = memory[addr + 1]
    return (high << 8) | low
# def read_word4(memory, addr):
#     """Read 4 bytes little-endian"""
#     low = memory[addr]
#     high = memory[addr + 3]
#     return (high << 8) | low

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
        player_species = POKEMON_NAMES.get(str(mem[self.get_mem_pointer("poke_species")]))   
        # player_type1 = mem[self.get_mem_pointer("poke_type1")]
        # player_type2 = mem[self.get_mem_pointer("poke_type2")] 
        try:
            player_type1 = POKEMON_TYPES.get(player_species.upper(), None)[0]
            player_type2 = POKEMON_TYPES.get(player_species.upper(), None)[1]
        except:
            player_type1 = None
            player_type2 = None
        player_hp = read_word(mem, self.get_mem_pointer("poke_current_hp"))/256
        player_hp_max = read_word(mem, self.get_mem_pointer("poke_max_hp"))/256
        player_level = mem[self.get_mem_pointer("poke_level")] 

        # Enemy Pokémon stats
        enemy_species = POKEMON_NAMES.get(str(mem[self.get_mem_pointer("enemy_species")]))
        # enemy_type1 = mem[self.get_mem_pointer("enemy_type1")] 
        # enemy_type2 = mem[self.get_mem_pointer("enemy_type2")]
        try:
            enemy_type1 = POKEMON_TYPES.get(enemy_species.upper(), None)[0]
            enemy_type2 = POKEMON_TYPES.get(enemy_species.upper(), None)[1]
        except:
            enemy_type1 = None
            enemy_type2 = None
        enemy_hp = read_word(mem, self.get_mem_pointer("enemy_current_hp"))/256
        enemy_hp_max = read_word(mem, self.get_mem_pointer("enemy_max_hp"))/256
        enemy_name = POKEMON_NAMES.get(enemy_species, "Unknown")
        enemy_level = mem[self.get_mem_pointer("enemy_level")]


        return {
            "player": {
                "position": {"x": x, "y": y, "map_id": map_id},
                "pokemon": {
                    "species": player_species,
                    "type1": player_type1,
                    "type2": player_type2,
                    "level": player_level,
                    "hp": player_hp,
                    "hp_max": player_hp_max,
                    "hp_ratio": round(player_hp / max(player_hp_max, 1), 2)
                },
            },
            "opponent": {
                "name": enemy_name,
                "species": enemy_species,
                "type1": enemy_type1,
                "type2": enemy_type2,
                "level": enemy_level,
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
        # if mode == 'battle':
        #     self.print_memory_region(self.pyboy, 0xD013)

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

