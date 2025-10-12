import json
import os
# Pokemon Names
names_file = "src/pokemon_agent/utils/ref_data/pokered_data/pokemon/names.asm"

POKEMON_NAMES = {}
with open(names_file, "r") as f:
    index = 1
    for line in f:
        line = line.strip()
        # print(line)
        if line.startswith("dname"):
            # Remove dname and quotes
            name = line.split('"')[1] #.replace(".", "")
            POKEMON_NAMES[index] = name.title()#.upper()
            index += 1

with open("src/pokemon_agent/utils/ref_data/POKEMON_NAMES.json", "w") as f:
    json.dump(POKEMON_NAMES, f, indent=4, ensure_ascii=False)
print(POKEMON_NAMES)




# Pokemon Types
pokemon_folder = "src/pokemon_agent/utils/ref_data/pokered_data/pokemon/base_stats/"
POKEMON_TYPES = {}
for filename in os.listdir(pokemon_folder):
    if filename.endswith(".asm"):
        filepath = os.path.join(pokemon_folder, filename)
        with open(filepath, "r") as f:
            lines = f.readlines()
        db_lines = [line.strip() for line in lines if line.strip().startswith("db")]
        types_line = db_lines[2]
        tokens = types_line.split()[1:3]  # only get types
        types = [t.strip(",").upper() for t in tokens]
        POKEMON_TYPES[filename.split('.')[0].upper()] = types

with open("src/pokemon_agent/utils/ref_data/POKEMON_TYPES.json", "w") as f:
    json.dump(POKEMON_TYPES, f, indent=4, ensure_ascii=False)
print(POKEMON_TYPES)


