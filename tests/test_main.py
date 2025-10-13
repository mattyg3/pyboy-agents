import json
with open('src/pokemon_agent/utils/ref_data/MOVES_INDEX.json', 'r') as f:
    MOVES_INDEX = json.load(f)

player_move1_dict = next((d for d in MOVES_INDEX if d['move_id'] == 10), None)
print(player_move1_dict)