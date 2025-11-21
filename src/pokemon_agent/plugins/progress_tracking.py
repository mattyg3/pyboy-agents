import fnmatch

# Tracking RAM Pointers (in order of events?)
oaks_parcel_RAM = 0xD60D
town_map_RAM = 0xD5F3
fought_brock_RAM = 0xD755
fought_misty_RAM = 0xD75E
fought_lt_surge_RAM = 0xD773
fought_erika_RAM = 0xD77C
fought_koga_RAM = 0xD792
fought_sabrina_RAM = 0xD7B3
fought_blaine_RAM = 0xD79A
fought_giovanni_RAM = 0xD751
###

file_path='src/pokemon_agent/saves/dialog_log.txt'
try:
    with open(file_path, 'r') as f:
        DIALOG_LOG = f.read()
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")


class ProgressTracker:
    def __init__(self, pyboy): #, has_pokedex=False
        self.pyboy = pyboy
        # self.has_pokedex=has_pokedex
        self.dialog_log=''

    def load_dialog(self, file_path='src/pokemon_agent/saves/dialog_log.txt'):
        try:
            with open(file_path, 'r') as f:
                self.dialog_log = f.read()
            # print("LOADED DIALOG FILE")
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

        

    
    def read_progress(self):
        mem = self.pyboy.memory

        oaks_parcel = mem[oaks_parcel_RAM]
        town_map = mem[town_map_RAM]
        fought_brock = mem[fought_brock_RAM]
        self.load_dialog()
        # print(self.dialog_log)
        # print(type(self.dialog_log))
        # if 'GOT POKÈDEX FROM OAK' in self.dialog_log: 
        # if 'DEX FROM OAK' in self.dialog_log:
        # if fnmatch.fnmatch(self.dialog_log, '*GOT POK*DEX FROM OAK*'):
        #     # print("SET HAS_POKEDEX = TRUE")
        #     self.has_pokedex=True
        current_progress = {
            'oaks_parcel':oaks_parcel,
            'town_map':town_map,
            'fought_brock':fought_brock,
            }
        return current_progress
    
    def check_progress(self):
        current_progress = self.read_progress()
        # print(f'pokedex_flag: {self.has_pokedex}')
        if current_progress["oaks_parcel"] == 0:
            next_game_checkpoint = "Player must retrieve Oak's parcel from VIRIDIAN_MART"
            
        # elif current_progress["town_map"] == 0 and self.has_pokedex == True:
        elif current_progress["town_map"] == 0 and fnmatch.fnmatch(self.dialog_log, '*GOT POK*DEX FROM OAK*'):
            next_game_checkpoint = "Retrieve the Town Map from NPC in BLUES_HOUSE"
        elif current_progress["town_map"] == 0:
            next_game_checkpoint = "Return parcel to Oak in OAKS_LAB, Then Retrieve the Town Map from NPC in BLUES_HOUSE"

        
        elif current_progress["fought_brock"] == 0 and fnmatch.fnmatch(self.dialog_log, '*GOT A TOWN MAP*'):
            # print(current_progress["town_map"])
            next_game_checkpoint = "Travel to PEWTER_CITY and Defeat Brock at PEWTER_GYM"
        elif current_progress["fought_brock"] == 0:
            next_game_checkpoint = "Retrieve the Town Map from NPC in BLUES_HOUSE"
        
        
        
        
        
        else:
            next_game_checkpoint = "NEED TO DEFINE NEXT GOAL!!!"

        print(f"LONGTERM_GOAL: {next_game_checkpoint}")

        return next_game_checkpoint, self.dialog_log

