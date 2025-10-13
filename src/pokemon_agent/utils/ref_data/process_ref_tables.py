import re
from pathlib import Path
import os
import json

# # ====== POKEDEX ====== 
# POKEDEX = []
# def parse_pokemon_file(path, name_dict):
#     text = Path(path).read_text()

#     data = {}

#     # Pokemon Name
#     data['pokemon_name'] = path.split('/')[-1].split('.')[0].upper()

#     # Internal ID
#     data['internal_id'] = name_dict.get(data['pokemon_name'])

#     # Pokédex ID
#     if match := re.search(r'db\s+(DEX_[A-Z_]+)', text):
#         data['pokedex_id'] = match.group(1)

#     # Base stats
#     if match := re.search(r'db\s+([\d\s,]+)\s*;\s*hp', text):
#         stats = [int(x) for x in match.group(1).split(',')]
#         data['stats'] = dict(zip(['hp','atk','def','spd','spc'], stats))

#     # Types
#     if match := re.search(r'db\s+([A-Z_]+),\s*([A-Z_]+)\s*;\s*type', text):
#         data['types'] = [match.group(1).replace('_TYPE',''), match.group(2).replace('_TYPE','')]

#     # Catch rate & base exp
#     if match := re.search(r'db\s+(\d+)\s*;\s*catch rate', text):
#         data['catch_rate'] = int(match.group(1))
#     if match := re.search(r'db\s+(\d+)\s*;\s*base exp', text):
#         data['base_exp'] = int(match.group(1))

#     # # Sprite includes
#     # if match := re.search(r'INCBIN\s+"([^"]+)"', text):
#     #     data['sprite_front'] = match.group(1)

#     # # Sprite labels
#     # if match := re.search(r'dw\s+([A-Za-z0-9_]+),\s*([A-Za-z0-9_]+)', text):
#     #     data['sprite_labels'] = [match.group(1), match.group(2)]

#     # Level 1 moves
#     if match := re.search(r'db\s+([A-Z0-9_,\s]+);\s*level 1 learnset', text):
#         moves = [m.strip() for m in match.group(1).split(',') if m.strip() != 'NO_MOVE']
#         data['level_1_moves'] = moves

#     # Growth rate
#     if match := re.search(r'db\s+(GROWTH_[A-Z_]+)', text):
#         data['growth_rate'] = match.group(1).replace('GROWTH_', '')

#     # TM/HM list
#     if match := re.search(r'tmhm\s+([A-Z0-9_,\s\\]+)\n', text):
#         tms = re.split(r'[,\s\\]+', match.group(1))
#         data['tmhm'] = [t for t in tms if t]

#     return data

# names_file = "src/pokemon_agent/utils/ref_data/POKEMON_NAMES.json"
# with open(names_file, "r", encoding='utf-8') as f:
#     POKEMON_NAMES= json.load(f)
# POKEMON_NAMES['3'] = 'NIDORANA' #remove accent letters
# POKEMON_NAMES['15'] = 'NIDORANO' #remove accent letters
# inverted_POKEMON_NAMES = {value: key for key, value in POKEMON_NAMES.items()}

# pokemon_folder = "src/pokemon_agent/utils/ref_data/pokered_data/pokemon/base_stats/"
# for filename in os.listdir(pokemon_folder):
#     if filename.endswith(".asm"):
#         filepath = os.path.join(pokemon_folder, filename)
#         POKEDEX.append(parse_pokemon_file(filepath, inverted_POKEMON_NAMES))

# with open("src/pokemon_agent/utils/ref_data/POKEDEX.json", "w", encoding='utf-8') as f:
#     json.dump(POKEDEX, f, indent=4, ensure_ascii=False)



# ====== Move Sets ======

def parse_move_names(path):
    text = Path(path).read_text()

    # Find all li "..." entries
    moves = re.findall(r'li\s+"([^"]+)"', text)

    # Create dictionary with IDs starting at 1
    move_dict = {i + 1: name for i, name in enumerate(moves)}

    return move_dict

MOVES_NAMES = parse_move_names("src/pokemon_agent/utils/ref_data/pokered_data/moves/names.asm")
with open("src/pokemon_agent/utils/ref_data/MOVES_NAMES.json", "w", encoding='utf-8') as f:
    json.dump(MOVES_NAMES, f, indent=4, ensure_ascii=False)

inverted_MOVES_NAMES = {value: key for key, value in MOVES_NAMES.items()}

def parse_move_data(path):
    text = Path(path).read_text()

    # Regex: match each move line
    pattern = re.compile(
        r'move\s+([A-Z0-9_]+),\s*([A-Z0-9_]+),\s*([0-9]+),\s*([A-Z_]+),\s*([0-9]+),\s*([0-9]+)'
    )

    moves = []
    for match in pattern.findall(text):
        name, effect, power, type_, accuracy, pp = match
        moves.append({
            "name": name,
            "move_id": inverted_MOVES_NAMES.get(name),
            "effect": effect,
            "power": int(power),
            "type": type_,
            "accuracy": int(accuracy),
            "pp": int(pp)
        })

    return moves
MOVES_DATA = parse_move_data("src/pokemon_agent/utils/ref_data/pokered_data/moves/moves.asm")
with open("src/pokemon_agent/utils/ref_data/MOVES_INDEX.json", "w", encoding='utf-8') as f:
    json.dump(MOVES_DATA, f, indent=4, ensure_ascii=False)



# # Pokemon Names
# names_file = "src/pokemon_agent/utils/ref_data/pokered_data/pokemon/names.asm"

# POKEMON_NAMES = {}
# with open(names_file, "r") as f:
#     index = 1
#     for line in f:
#         line = line.strip()
#         # print(line)
#         if line.startswith("dname"):
#             # Remove dname and quotes
#             POKEMON_NAMES[index] = line.split('"')[1].upper()
#             index += 1

# with open("src/pokemon_agent/utils/ref_data/POKEMON_NAMES.json", "w", encoding='utf-8') as f:
#     json.dump(POKEMON_NAMES, f, indent=4, ensure_ascii=False)
# print(POKEMON_NAMES)




# # Pokemon Types
# pokemon_folder = "src/pokemon_agent/utils/ref_data/pokered_data/pokemon/base_stats/"
# POKEMON_TYPES = {}
# for filename in os.listdir(pokemon_folder):
#     if filename.endswith(".asm"):
#         filepath = os.path.join(pokemon_folder, filename)
#         with open(filepath, "r") as f:
#             lines = f.readlines()
#         db_lines = [line.strip() for line in lines if line.strip().startswith("db")]
#         types_line = db_lines[2]
#         tokens = types_line.split()[1:3]  # only get types
#         types = [t.strip(",").upper() for t in tokens]
#         POKEMON_TYPES[filename.split('.')[0].upper()] = types

# with open("src/pokemon_agent/utils/ref_data/POKEMON_TYPES.json", "w") as f:
#     json.dump(POKEMON_TYPES, f, indent=4, ensure_ascii=False)
# print(POKEMON_TYPES)


