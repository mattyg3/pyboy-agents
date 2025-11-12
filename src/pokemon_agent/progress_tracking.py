
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

class ProgressTracker:
    def __init__(self, pyboy):
        self.pyboy = pyboy
    
    def read_progress(self):
        mem = self.pyboy.memory

        oaks_parcel = mem[oaks_parcel_RAM]
        town_map = mem[town_map_RAM]
        fought_brock = mem[fought_brock_RAM]

        current_progress = {
            'oaks_parcel':oaks_parcel,
            'town_map':town_map,
            'fought_brock':fought_brock,
            }
        return current_progress
    
    def check_progress(self):
        current_progress = self.read_progress()
        if current_progress["oaks_parcel"] == 0:
            next_game_checkpoint = "Player must retrieve Oak's parcel from Viridian City Mart and then return it to Oak in his lab"
        elif current_progress["town_map"] == 0:
            next_game_checkpoint = "Get The Town Map in Pallet Town"
        elif current_progress["fought_brock"] == 0:
            next_game_checkpoint = "Defeat Brock at Pewter City Gym"
        else:
            next_game_checkpoint = "NEED TO DEFINE NEXT GOAL!!!"

        return next_game_checkpoint

