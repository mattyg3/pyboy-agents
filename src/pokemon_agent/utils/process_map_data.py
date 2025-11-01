# # ====== create map_headers.json ======
# import re
# import pandas as pd

# # Path to your file
# file_path = "src/pokemon_agent/utils/ref_data/pokered_data/map_constants.asm"

# # Regex to match map_const lines
# pattern = re.compile(r'map_const\s+(\w+),\s+(\d+),\s+(\d+)\s*;\s*(\$\w+)')

# data = []

# with open(file_path, "r") as f:
#     for line in f:
#         match = pattern.search(line)
#         if match:
#             name = match.group(1).replace('_', '').upper()
#             width = int(match.group(2))
#             height = int(match.group(3))
#             map_id = int(match.group(4).replace('$', ''), 16)
#             data.append({
#                 "ID": map_id,
#                 "name": name,
#                 "width": width,
#                 "height": height
#             })

# df = pd.DataFrame(data)
# print(df)
# print(df.dtypes)

# import re
# import json
# from pathlib import Path

# # Directory containing .asm files
# ASM_DIR = Path("src/pokemon_agent/utils/ref_data/pokered_data/maps/headers")
# OUTPUT_JSON = Path("src/pokemon_agent/utils/ref_data/maps/map_headers.json")

# # Regex patterns
# header_pattern = re.compile(
#     r"map_header\s+(\w+),\s*(\w+),\s*(\w+),\s*(.*)"
# )
# connection_pattern = re.compile(
#     r"connection\s+(\w+),\s*(\w+),\s*(\w+),\s*(\d+)"
# )

# maps = []

# # Loop through all .asm files
# for asm_file in ASM_DIR.glob("*.asm"):
#     with asm_file.open("r", encoding="utf-8") as f:
#         content = f.read()

#     # Extract map_header
#     header_match = header_pattern.search(content)
#     if not header_match:
#         continue  # skip files without a map_header


#     # Fix environment based on collision table
#     env = None
#     if header_match.group(3) == "REDS_HOUSE_1" or header_match.group(3) == "REDS_HOUSE_2":
#         env = "REDS_HOUSE"
#     elif header_match.group(3) == "MART":
#         env = "POKECENTER"
#     elif header_match.group(3) == "DOJO":
#         env = "GYM"
#     elif header_match.group(3) == "FOREST_GATE" or header_match.group(3) == "MUSEUM":
#         env = "GATE"
#     else:
#         env = header_match.group(3)

#     # Look up map constants
#     upper_name = header_match.group(1).upper()
#     try:
#         map_id = df[df['name'] == upper_name]['ID'].iloc[0]
#     except:
#         map_id = None
#     try:
#         map_width = df[df['name'] == upper_name]['width'].iloc[0]
#     except:
#         map_width = None
#     try:
#         map_height = df[df['name'] == upper_name]['height'].iloc[0]
#     except:
#         map_height = None

#     map_data = {
#         "file": asm_file.name,
#         "name": upper_name,
#         "map_id": map_id,
#         "map_width": map_width,
#         "map_height": map_height,
#         "label": header_match.group(2),
#         # "environment": header_match.group(3),
#         "environment": env,
#         "connections_flags": header_match.group(4),
#         "connections": []
#     }

#     # Extract connections
#     for conn_match in connection_pattern.finditer(content):
#         map_data["connections"].append({
#             "direction": conn_match.group(1),
#             "target_name": conn_match.group(2),
#             "target_label": conn_match.group(3),
#             "offset": int(conn_match.group(4))
#         })

#     maps.append(map_data)

# # Save to JSON
# with OUTPUT_JSON.open("w", encoding="utf-8") as f:
#     json.dump(maps, f, indent=4, default=int)

# print(f"Parsed {len(maps)} maps and saved to {OUTPUT_JSON}")



# # ====== create collision_tiles.json ======
# import re
# import json
# from pathlib import Path

# # Path to your collision file
# collision_file = Path("src/pokemon_agent/utils/ref_data/pokered_data/tilesets/collision_tile_ids.asm")

# collision_data = {}
# current_labels = []

# with collision_file.open("r", encoding="utf-8") as f:
#     for line in f:
#         # Remove comments and whitespace
#         line = line.split(";")[0].strip()
#         if not line or line.startswith("MACRO"):
#             continue


#         # Match labels like Underground_Coll:: or multiple stacked labels
#         if line.endswith("::"):
#             labels = [l.strip() for l in line.split("::") if l.strip()]
#             current_labels = labels
#             # Shared list for all stacked labels
#             shared_list = []
#             for label in labels:
#                 collision_data[label] = shared_list
#             continue

#         # Match coll_tiles lines
#         match = re.match(r'coll_tiles\s*(.*)', line)
#         if match and current_labels:
#             tiles_str = match.group(1).strip()
#             if tiles_str:
#                 # Split by commas and remove whitespace
#                 tiles = [t.strip() for t in tiles_str.split(",") if t.strip()]
#                 # Only keep valid hex tiles ($XX)
#                 tiles = [int(t.replace("$", "0x"), 16) for t in tiles if t.startswith("$")]
#                 # tiles = [t.replace("$", "0x") for t in tiles if t.startswith("$")]
#                 collision_data[current_labels[0]].extend(tiles)


# collision_data.pop("RedsHouse1_Coll")
# collision_data["RedsHouse_Coll"] = collision_data.pop("RedsHouse2_Coll")
# collision_data.pop("Mart_Coll")
# collision_data.pop("Dojo_Coll")
# collision_data.pop("ForestGate_Coll")
# collision_data.pop("Museum_Coll")

# upper_collision_data = {k.upper(): v for k, v in collision_data.items()}

# # Save as JSON
# output_file = Path("src/pokemon_agent/utils/ref_data/maps/collision_tiles.json")
# with output_file.open("w", encoding="utf-8") as f:
#     json.dump(upper_collision_data, f, indent=4)

# print(f"Saved {len(upper_collision_data)} collision tile sets to {output_file}")


# ====== create map_objects.json ======
import re
import json
from pathlib import Path
# Directory containing .asm files
ASM_DIR = Path("src/pokemon_agent/utils/ref_data/pokered_data/maps/objects")
OUTPUT_JSON = Path("src/pokemon_agent/utils/ref_data/maps/map_objects.json")

def parse_asm_objects(file_text: str):
    data = {
        "constants": [],
        "border_block": None,
        "warp_events": [],
        "bg_events": [],
        "object_events": [],
        "warps_to": None,
    }

    # ---- 1️⃣ constants ----
    data["constants"] = re.findall(r"const_export\s+(\w+)", file_text)

    # ---- 2️⃣ border block ----
    m = re.search(r"db\s+\$(\w+)\s*;\s*border block", file_text)
    if m:
        data["border_block"] = f"${m.group(1)}"

    # ---- 3️⃣ warp events ----
    for m in re.finditer(r"warp_event\s+(\d+),\s*(\d+),\s*(\w+),\s*(\d+)", file_text):
        x, y, dest, warp_id = m.groups()
        data["warp_events"].append({
            "x": int(x),
            "y": int(y),
            "dest_map": dest,
            "warp_id": int(warp_id),
        })

    # ---- 4️⃣ bg events ----
    for m in re.finditer(r"bg_event\s+(\d+),\s*(\d+),\s*(\w+)", file_text):
        x, y, text = m.groups()
        data["bg_events"].append({
            "x": int(x),
            "y": int(y),
            "text": text,
        })

    # ---- 5️⃣ object events ----
    # Handle both 6-field and 8-field forms
    obj_pattern = re.compile(
        r"object_event\s+(\d+),\s*(\d+),\s*(\w+),\s*(\w+),\s*(\w+),\s*(\w+)(?:,\s*(\w+),\s*(\w+))?"
    )
    for m in obj_pattern.finditer(file_text):
        x, y, sprite, move, facing, text, extra1, extra2 = m.groups(default=None)
        data["object_events"].append({
            "x": int(x),
            "y": int(y),
            "sprite": sprite,
            "movement": move,
            "facing": facing,
            "text": text,
            "extra1": extra1,
            "extra2": extra2,
        })

    # ---- 6️⃣ warps_to ----
    m = re.search(r"def_warps_to\s+(\w+)", file_text)
    if m:
        data["warps_to"] = m.group(1)

    return data


# # === Example: parse one file ===
# file_path = Path("PalletTown.asm")
# parsed = parse_asm_objects(file_path.read_text())

# print(json.dumps(parsed, indent=2))

# === Example: optionally collect directory ===
def parse_asm_directory(dir_path: Path):
    results = {}
    for path in dir_path.glob("*.asm"):
        results[path.stem] = parse_asm_objects(path.read_text())
    return results


# Example usage:
all_maps = parse_asm_directory(ASM_DIR)
with OUTPUT_JSON.open( "w", encoding="utf-8") as f:
    json.dump(all_maps, f, indent=4, default=int)

