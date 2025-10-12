import json
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
#             name = line.split('"')[1] #.replace(".", "")
#             POKEMON_NAMES[index] = name.title()
#             index += 1

# with open("src/pokemon_agent/utils/ref_data/POKEMON_NAMES.json", "w") as f:
#     json.dump(POKEMON_NAMES, f, indent=4, ensure_ascii=False)
# print(POKEMON_NAMES)




# Pokemon Types
import re
# Path to your asm file
asm_file = "src/pokemon_agent/utils/ref_data/pokered_data/types/names.asm"

with open(asm_file, "r") as f:
    lines = f.readlines()

# Step 1: parse table order
type_order = []
parsing_table = False
for line in lines:
    line = line.strip()
    if line.startswith("TypeNames:"):
        parsing_table = True
        continue
    if parsing_table:
        if line.startswith("dw"):
            # extract the label name after dw
            label = line.split()[-1].replace(".", "")
            type_order.append(label)
        elif line.startswith("."):  # reached label definitions
            break

# Step 2: parse label definitions
type_labels = {}
for line in lines:
    line = line.strip()
    match = re.match(r"\.(\w+):\s+db\s+\"([A-Z]+)@", line)
    if match:
        label, name = match.groups()
        type_labels[label] = name.title()

# Step 3: combine order and labels into a dict
TYPE_NAMES = {i: type_labels[label] for i, label in enumerate(type_order)}

print(TYPE_NAMES)