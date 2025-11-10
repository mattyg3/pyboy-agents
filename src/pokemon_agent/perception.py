
import numpy as np
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import json
from utils.utility_funcs import type_multiplier
from OCR import OCR_Processing, BattleStateTracker, OverworldStateTracker
from utils.utility_funcs import TextCleaner

# Import Reference Data
with open('src/pokemon_agent/utils/ref_data/POKEDEX.json', 'r') as f:
    POKEDEX = json.load(f)

with open('src/pokemon_agent/utils/ref_data/MOVES_INDEX.json', 'r') as f:
    MOVES_INDEX = json.load(f)

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

class BattleFlag:
    def __init__(self, pyboy):
        self.pyboy = pyboy

    def get_mem_pointer(self, address_book, pointer_name):
        return int(next(entry["address"] for entry in RAM_POINTERS[address_book] if entry["name"] == pointer_name), 16)

    def read_memory_state(self):
        mem = self.pyboy.memory
        battle_flag = mem[self.get_mem_pointer("system_addresses", "battle_type")]
        turn = mem[self.get_mem_pointer("system_addresses", "battle_turn")]

        return {"battle_type": battle_flag, "battle_turn": turn}
    
class DialogFlag:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.screen = self.pyboy.screen

    def get_mem_pointer(self, address_book, pointer_name):
        return int(next(entry["address"] for entry in RAM_POINTERS[address_book] if entry["name"] == pointer_name), 16)
    
    def capture_frame(self):
        return self.screen.ndarray
    
    def read_memory_state(self):
        mem = self.pyboy.memory
        frame = self.capture_frame()
        overworld_tracker = OverworldStateTracker()
        ocr_state = OCR_Processing(self.pyboy, frame, overworld_tracker)
        ocr_results = ocr_state.read_frame()
        if ocr_results.get("new_text"):
            return True
        
    

class PokemonPerceptionAgent:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.screen = self.pyboy.screen
        self.text_prev = ""
        self.prev_state = {"battle":{"turn":None}, "opponent":{"species":None}}
        self.enemy_move_list = []
        self.dialog_history = []
        # self.frame_count = 0
        self.text_count = 0
        self.dialog_reset_counter = 0
        print("PerceptionAgent with memory reading initialized.")

    

    # def read_text(self, frame):
    #     gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    #     h, w = gray.shape
    #     text_region = gray[int(h*0.7):, :]
    #     text_region = cv2.threshold(text_region, 100, 255, cv2.THRESH_BINARY)[1]
    #     text = pytesseract.image_to_string(text_region, config='--psm 6').strip()
    #     return text
    
    def get_mem_pointer(self, address_book, pointer_name):
        return int(next(entry["address"] for entry in RAM_POINTERS[address_book] if entry["name"] == pointer_name), 16)
    


    def read_memory_state(self):
        mem = self.pyboy.memory
        x = mem[self.get_mem_pointer("system_addresses", "player_x")]
        y = mem[self.get_mem_pointer("system_addresses", "player_y")]
        map_id = mem[self.get_mem_pointer("system_addresses", "current_map_id")]

        # Battle 
        self.battle_flag = mem[self.get_mem_pointer("system_addresses", "battle_type")]
        turn = mem[self.get_mem_pointer("system_addresses", "battle_turn")]
        # prev_turn = self.prev_state.get("battle").get("turn")
        prev_enemy_species = self.prev_state.get("opponent").get("species")


        # Player Pokémon stats
        ## Pokemon Info
        try:
            self.player_dict = next((d for d in POKEDEX if d['internal_id'] == str(mem[self.get_mem_pointer("player_addresses", "battle_species")]))) #, None
        except:
            self.player_dict={"pokemon_name":None, "types":[None,None]}

        player_species = self.player_dict.get("pokemon_name")   
        player_type1 = self.player_dict.get("types")[0]
        player_type2 = self.player_dict.get("types")[1]

        player_attack = read_word(mem, self.get_mem_pointer("player_addresses", "battle_attack_stat"))/256
        player_defense = read_word(mem, self.get_mem_pointer("player_addresses", "battle_defense_stat"))/256
        player_speed = read_word(mem, self.get_mem_pointer("player_addresses", "battle_speed_stat"))/256
        player_special = read_word(mem, self.get_mem_pointer("player_addresses", "battle_special_stat"))/256

        player_hp = read_word(mem, self.get_mem_pointer("player_addresses", "battle_current_hp"))/256
        player_hp_max = read_word(mem, self.get_mem_pointer("player_addresses", "battle_max_hp"))/256
        player_level = mem[self.get_mem_pointer("player_addresses", "battle_level")] 

        ## Moves
        try:
            player_move1_dict = next((d for d in MOVES_INDEX if d['move_id'] == int(mem[self.get_mem_pointer("player_addresses", "move_1")]))) #, None
        except:
            player_move1_dict={"name":None, "effect":None, "power":None, "type":None, "accuracy":None, "pp":None}
        player_move_1 = player_move1_dict.get("name")
        player_move_1_effect = player_move1_dict.get("effect")
        player_move_1_power = player_move1_dict.get("power")
        player_move_1_type = player_move1_dict.get("type")
        player_move_1_accuracy = player_move1_dict.get("accuracy")
        player_move_1_PP_max = player_move1_dict.get("pp")
        player_move_1_PP = mem[self.get_mem_pointer("player_addresses", "move_1_PP")] 

        try:
            player_move2_dict = next((d for d in MOVES_INDEX if d['move_id'] == int(mem[self.get_mem_pointer("player_addresses", "move_2")]))) #, None
        except:
            player_move2_dict={"name":None, "effect":None, "power":None, "type":None, "accuracy":None, "pp":None}
        player_move_2 = player_move2_dict.get("name")
        player_move_2_effect = player_move2_dict.get("effect")
        player_move_2_power = player_move2_dict.get("power")
        player_move_2_type = player_move2_dict.get("type")
        player_move_2_accuracy = player_move2_dict.get("accuracy")
        player_move_2_PP_max = player_move2_dict.get("pp")
        player_move_2_PP = mem[self.get_mem_pointer("player_addresses", "move_2_PP")] 
            
        try:
            player_move3_dict = next((d for d in MOVES_INDEX if d['move_id'] == int(mem[self.get_mem_pointer("player_addresses", "move_3")]))) #, None
        except:
            player_move3_dict={"name":None, "effect":None, "power":None, "type":None, "accuracy":None, "pp":None}
        player_move_3 = player_move3_dict.get("name")
        player_move_3_effect = player_move3_dict.get("effect")
        player_move_3_power = player_move3_dict.get("power")
        player_move_3_type = player_move3_dict.get("type")
        player_move_3_accuracy = player_move3_dict.get("accuracy")
        player_move_3_PP_max = player_move3_dict.get("pp")
        player_move_3_PP = mem[self.get_mem_pointer("player_addresses", "move_3_PP")] 

        try:
            player_move4_dict = next((d for d in MOVES_INDEX if d['move_id'] == int(mem[self.get_mem_pointer("player_addresses", "move_4")]))) #, None
        except:
            player_move4_dict={"name":None, "effect":None, "power":None, "type":None, "accuracy":None, "pp":None}
        player_move_4 = player_move4_dict.get("name")
        player_move_4_effect = player_move4_dict.get("effect")
        player_move_4_power = player_move4_dict.get("power")
        player_move_4_type = player_move4_dict.get("type")
        player_move_4_accuracy = player_move4_dict.get("accuracy")
        player_move_4_PP_max = player_move4_dict.get("pp")
        player_move_4_PP = mem[self.get_mem_pointer("player_addresses", "move_4_PP")]  


        # Enemy Pokémon stats
        ## Pokemon Info
        try:
            self.enemy_dict = next((d for d in POKEDEX if d['internal_id'] == str(mem[self.get_mem_pointer("enemy_addresses", "battle_species")])))
        except:
            self.enemy_dict = {"pokemon_name":None, "types":[None,None], "stats": {"atk":None, "def":None, "spd":None, "spc":None}}
  
        enemy_species = self.enemy_dict.get("pokemon_name")  
        enemy_type1 = self.enemy_dict.get("types")[0]
        enemy_type2 = self.enemy_dict.get("types")[1]

        enemy_attack = self.enemy_dict.get("stats").get("atk")  
        enemy_defense = self.enemy_dict.get("stats").get("def")  
        enemy_speed = self.enemy_dict.get("stats").get("spd")  
        enemy_special = self.enemy_dict.get("stats").get("spc")  
        
        enemy_hp = read_word(mem, self.get_mem_pointer("enemy_addresses", "battle_current_hp"))/256
        enemy_hp_max = read_word(mem, self.get_mem_pointer("enemy_addresses", "battle_max_hp"))/256
        enemy_level = mem[self.get_mem_pointer("enemy_addresses", "battle_level")]

        ## Moves - Log Moves in BattleState
        if prev_enemy_species != enemy_species:
            self.enemy_move_list=[] #reset for new enemies
        try:
            enemy_move_dict = next((d for d in MOVES_INDEX if d['move_id'] == int(mem[self.get_mem_pointer("enemy_addresses", "move_id")])))
        except:
            enemy_move_dict={"name":None, "effect":None, "power":None, "type":None, "accuracy":None, "pp":None}

        enemy_move = {
                        "move":enemy_move_dict.get("name"),
                        "PP_max":enemy_move_dict.get("pp"),
                        "effect":enemy_move_dict.get("effect"),
                        "power":enemy_move_dict.get("power"),
                        "type":enemy_move_dict.get("type"),
                        "accuracy":enemy_move_dict.get("accuracy"),
                    }

        move_list = self.enemy_move_list + [enemy_move]
        move_list = list({d['move']: d for d in move_list}.values())
        self.enemy_move_list = [d for d in move_list if d['move'] != None]
        

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
                            "PP_max":player_move_1_PP_max,
                            "effect":player_move_1_effect,
                            "power":player_move_1_power,
                            "type":player_move_1_type,
                            "accuracy":player_move_1_accuracy,
                        },
                        "move_2": {
                            "move":player_move_2,
                            "PP":player_move_2_PP,
                            "PP_max":player_move_2_PP_max,
                            "effect":player_move_2_effect,
                            "power":player_move_2_power,
                            "type":player_move_2_type,
                            "accuracy":player_move_2_accuracy,
                        },
                        "move_3": {
                            "move":player_move_3,
                            "PP":player_move_3_PP,
                            "PP_max":player_move_3_PP_max,
                            "effect":player_move_3_effect,
                            "power":player_move_3_power,
                            "type":player_move_3_type,
                            "accuracy":player_move_3_accuracy,
                        },
                        "move_4": {
                            "move":player_move_4,
                            "PP":player_move_4_PP,
                            "PP_max":player_move_4_PP_max,
                            "effect":player_move_4_effect,
                            "power":player_move_4_power,
                            "type":player_move_4_type,
                            "accuracy":player_move_4_accuracy,
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
                "hp_ratio": round(enemy_hp / max(enemy_hp_max, 1), 2),
                "stats": {
                        "attack":enemy_attack,
                        "defense":enemy_defense,
                        "speed":enemy_speed,
                        "special":enemy_special,
                    },
                "moves": self.enemy_move_list,
            },
            "battle": {
                "battle_type": self.battle_flag,
                "turn": turn,
            }
        }
    
    # def get_battle_state(self, mem_state):
    #     turn_count = 

    # def detect_mode(self, mem_state, text):
    #     if mem_state["opponent"]["hp_max"] > 0:
    #         return "battle"
    #     if "menu" in text.lower():
    #         return "menu"
    #     return "overworld"
    def capture_frame(self):
        return self.screen.ndarray
    
    

    def get_game_state(self):
        # self.frame_count += 1 
        frame = self.capture_frame()
        battle_tracker = BattleStateTracker()
        overworld_tracker = OverworldStateTracker()
        mem_state = self.read_memory_state()

        if self.battle_flag != 0:
            tracker_state = battle_tracker
        else:
            tracker_state = overworld_tracker

        ocr_state = OCR_Processing(self.pyboy, frame, tracker_state)
        ocr_results = ocr_state.read_frame()
        player_turn=False

        if ocr_results.get("menu_state"):
            if not player_turn and len(self.dialog_history) > 0:
                cleaned_dialog = TextCleaner(self.dialog_history)
                with open('src/pokemon_agent/saves/dialog_log.txt', 'a') as file:
                    file.write(f'{cleaned_dialog}\n')
                self.dialog_history=[]
                self.text_count=0

            player_turn = True
            menu_state = ocr_results.get("menu_state")
            dialog_text = None
            # print(f'\nMENU: {ocr_results.get("menu_state")}\n')
        elif ocr_results.get("new_text"):
            menu_state = None
            dialog_text = ocr_results.get("new_text")
            # dialog_text = TextCleaner([dialog_text])
            if dialog_text not in self.dialog_history:
                self.dialog_history.append(dialog_text)
                self.text_count += 1
                self.dialog_reset_counter = 0 
                if self.text_count > 5: #save cleaned text to LOG
                    cleaned_dialog = TextCleaner(self.dialog_history)
                    with open('src/pokemon_agent/saves/dialog_log.txt', 'a') as file:
                        file.write(f'{cleaned_dialog}\n')

                    self.dialog_history=[]
                    self.text_count=0
        elif self.dialog_reset_counter > 10:
            menu_state = None
            dialog_text= None
            if len(self.dialog_history) > 0:
                cleaned_dialog = TextCleaner(self.dialog_history)
                with open('src/pokemon_agent/saves/dialog_log.txt', 'a') as file:
                    file.write(f'{cleaned_dialog}\n')
                self.dialog_history=[]
                self.text_count=0
        else:
            self.dialog_reset_counter += 1
            menu_state = None
            dialog_text= None
    
        self.prev_state = mem_state
        state = {
                "player": mem_state["player"],
                "opponent": mem_state["opponent"],
                "battle": {
                    "battle_type": mem_state.get("battle").get("battle_type"),
                    "turn": mem_state.get("battle").get("turn"),
                    "player_turn": player_turn
                },
                "menu_state": menu_state,
                "dialog_text": dialog_text,
                "dialog_history": TextCleaner(self.dialog_history),
            }
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
        


