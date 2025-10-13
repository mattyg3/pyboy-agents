
import numpy as np
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import json
from utils.utility_funcs import type_multiplier

# Import Reference Data
with open('src/pokemon_agent/utils/ref_data/POKEDEX.json', 'r') as f:
    POKEDEX = json.load(f)

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
    
    def get_mem_pointer(self, address_book, pointer_name):
        return int(next(entry["address"] for entry in RAM_POINTERS[address_book] if entry["name"] == pointer_name), 16)
    


    def read_memory_state(self):
        mem = self.pyboy.memory
        x = mem[self.get_mem_pointer("system_addresses", "player_x")]
        y = mem[self.get_mem_pointer("system_addresses", "player_y")]
        map_id = mem[self.get_mem_pointer("system_addresses", "current_map_id")]

        # Battle 
        turn = mem[self.get_mem_pointer("system_addresses", "battle_turn")]

        # Player Pokémon stats
        try:
            self.player_dict = next((d for d in POKEDEX if d['internal_id'] == str(mem[self.get_mem_pointer("player_addresses", "battle_species")])), None)
            player_species = self.player_dict.get("pokemon_name")   
            player_type1 = self.player_dict.get("types")[0]
            player_type2 = self.player_dict.get("types")[1]
            player_move_1 = mem[self.get_mem_pointer("player_addresses", "move_1")] 
            player_move_1_PP = mem[self.get_mem_pointer("player_addresses", "move_1_PP")] 
            player_move_2 = mem[self.get_mem_pointer("player_addresses", "move_2")] 
            player_move_2_PP = mem[self.get_mem_pointer("player_addresses", "move_2_PP")] 
            player_move_3 = mem[self.get_mem_pointer("player_addresses", "move_3")] 
            player_move_3_PP = mem[self.get_mem_pointer("player_addresses", "move_3_PP")] 
            player_move_4 = mem[self.get_mem_pointer("player_addresses", "move_4")] 
            player_move_4_PP = mem[self.get_mem_pointer("player_addresses", "move_4_PP")] 
            player_attack = mem[self.get_mem_pointer("player_addresses", "battle_attack_stat")] 
            player_defense = mem[self.get_mem_pointer("player_addresses", "battle_defense_stat")]
            player_speed = mem[self.get_mem_pointer("player_addresses", "battle_speed_stat")]
            player_special = mem[self.get_mem_pointer("player_addresses", "battle_special_stat")]
        except:
            self.player_dict={}
            player_species = None
            player_type1 = None
            player_type2 = None
            player_move_1 = None
            player_move_1_PP = None
            player_move_2 = None
            player_move_2_PP = None
            player_move_3 = None
            player_move_3_PP = None
            player_move_4 = None
            player_move_4_PP = None
            player_attack = None
            player_defense = None
            player_speed = None
            player_special = None
        player_hp = read_word(mem, self.get_mem_pointer("player_addresses", "battle_current_hp"))/256
        player_hp_max = read_word(mem, self.get_mem_pointer("player_addresses", "battle_max_hp"))/256
        player_level = mem[self.get_mem_pointer("player_addresses", "battle_level")] 

        # Enemy Pokémon stats
        try:
            self.enemy_dict = next((d for d in POKEDEX if d['internal_id'] == str(mem[self.get_mem_pointer("enemy_addresses", "battle_species")])), None)
            enemy_species = self.enemy_dict.get("pokemon_name")  
            enemy_type1 = self.enemy_dict.get("types")[0]
            enemy_type2 = self.enemy_dict.get("types")[1]
        except:
            self.enemy_dict = {}
            enemy_species = None
            enemy_type1 = None
            enemy_type2 = None
        enemy_hp = read_word(mem, self.get_mem_pointer("enemy_addresses", "battle_current_hp"))/256
        enemy_hp_max = read_word(mem, self.get_mem_pointer("enemy_addresses", "battle_max_hp"))/256
        enemy_level = mem[self.get_mem_pointer("enemy_addresses", "battle_level")]


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
                    "hp_ratio": round(player_hp / max(player_hp_max, 1), 2),
                    "stats": {
                        "attack":player_attack,
                        "defense":player_defense,
                        "speed":player_speed,
                        "special":player_special,
                    },
                    "moves": {
                        "move_1": {
                            "move":player_move_1,
                            "PP":player_move_1_PP,
                        },
                        "move_2": {
                            "move":player_move_2,
                            "PP":player_move_2_PP,
                        },
                        "move_3": {
                            "move":player_move_3,
                            "PP":player_move_3_PP,
                        },
                        "move_4": {
                            "move":player_move_4,
                            "PP":player_move_4_PP,
                        }
                    }
                },
            },
            "opponent": {
                "species": enemy_species,
                "type1": enemy_type1,
                "type2": enemy_type2,
                "level": enemy_level,
                "hp": enemy_hp,
                "hp_max": enemy_hp_max,
                "hp_ratio": round(enemy_hp / max(enemy_hp_max, 1), 2)
            }
        }
    
    # def get_battle_state(self, mem_state):
    #     turn_count = 

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

        # if mode == 'battle':
        #     state = {
        #         "scene": mode,
        #         "text_box": text,

        #         }
        # else:
        #     state = {
        #         "scene": mode,
        #         "text_box": text,
        #         "player": mem_state["player"],
        #         "opponent": mem_state["opponent"],
        #     }
        return state

    # def evaluate_advantage(self, player, enemy):
    #     # Compute expected damage multipliers for both sides
    #     player_best = max(
    #         [type_multiplier(self.player_dict.get("PLACEHOLDER", "Normal"), self.enemy_dict.get("types"), self.player_dict.get("types"))
    #          for m in player.moves],
    #         default=1
    #     )
    #     enemy_best = max(
    #         [type_multiplier(self.enemy_dict.get("PLACEHOLDER", "Normal"), self.player_dict.get("types"), self.enemy_dict.get("types"))
    #          for m in enemy.moves],
    #         default=1
    #     )

    #     if player_best > enemy_best:
    #         return "player"
    #     elif enemy_best > player_best:
    #         return "enemy"
    #     else:
    #         return "even"
        

    # def step(self):
    #     self.pyboy.tick()
    #     return self.get_game_state()

# if __name__ == "__main__":
#     agent = PokemonPerceptionAgent("PokemonRed.gb")

#     while not agent.pyboy.tick():
#         state = agent.get_game_state()
#         if state["text_box"] != agent.text_prev:
#             print(state)
#             agent.text_prev = state["text_box"]

