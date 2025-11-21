# ====== create map_headers.json ======
import re
import pandas as pd
import json
from pathlib import Path


def create_map_headers():
    # Path to your file
    file_path = "src/pokemon_agent/utils/ref_data/pokered_data/map_constants.asm"

    # Regex to match map_const lines
    pattern = re.compile(r'map_const\s+(\w+),\s+(\d+),\s+(\d+)\s*;\s*(\$\w+)')

    data = []

    with open(file_path, "r") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                name = match.group(1).replace('_', '').upper()
                width = int(match.group(2))
                height = int(match.group(3))
                map_id = int(match.group(4).replace('$', ''), 16)
                data.append({
                    "ID": map_id,
                    "name": name,
                    "width": width,
                    "height": height
                })

    df = pd.DataFrame(data)
    print(df)
    print(df.dtypes)



    # Directory containing .asm files
    ASM_DIR = Path("src/pokemon_agent/utils/ref_data/pokered_data/maps/headers")
    OUTPUT_JSON = Path("src/pokemon_agent/utils/ref_data/maps/map_headers.json")

    # Regex patterns
    header_pattern = re.compile(
        r"map_header\s+(\w+),\s*(\w+),\s*(\w+),\s*(.*)"
    )
    # connection_pattern = re.compile(
    #     r"connection\s+(\w+),\s*(\w+),\s*(\w+),\s*(\d+)"
    # )
    connection_pattern = re.compile(
        r"connection\s+(\w+),\s*(\w+),\s*(\w+),\s*([$\-\w\d]+)(?:\s*;.*)?"
    )

    maps = []

    # Loop through all .asm files
    for asm_file in ASM_DIR.glob("*.asm"):
        with asm_file.open("r", encoding="utf-8") as f:
            content = f.read()

        # Extract map_header
        header_match = header_pattern.search(content)
        if not header_match:
            continue  # skip files without a map_header


        # Fix environment based on collision table
        env = None
        if header_match.group(3) == "REDS_HOUSE_1" or header_match.group(3) == "REDS_HOUSE_2":
            env = "REDS_HOUSE"
        elif header_match.group(3) == "MART":
            env = "POKECENTER"
        elif header_match.group(3) == "DOJO":
            env = "GYM"
        elif header_match.group(3) == "FOREST_GATE" or header_match.group(3) == "MUSEUM":
            env = "GATE"
        else:
            env = header_match.group(3)

        # Look up map constants
        upper_name = header_match.group(1).upper()
        try:
            map_id = df[df['name'] == upper_name]['ID'].iloc[0]
        except:
            map_id = None
        try:
            map_width = df[df['name'] == upper_name]['width'].iloc[0]
        except:
            map_width = None
        try:
            map_height = df[df['name'] == upper_name]['height'].iloc[0]
        except:
            map_height = None

        map_data = {
            "file": asm_file.name,
            "name": upper_name,
            "map_id": map_id,
            "map_width": map_width,
            "map_height": map_height,
            "label": header_match.group(2),
            # "environment": header_match.group(3),
            "environment": env,
            "connections_flags": header_match.group(4),
            "connections": []
        }

        # Extract connections
        for conn_match in connection_pattern.finditer(content):
            map_data["connections"].append({
                "direction": conn_match.group(1),
                "target_name": conn_match.group(2),
                "target_label": conn_match.group(3),
                "offset": int(conn_match.group(4))
            })

        maps.append(map_data)

    # Save to JSON
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(maps, f, indent=4, default=int)

    print(f"Parsed {len(maps)} maps and saved to {OUTPUT_JSON}")



# ====== create collision_tiles.json ======
import re
import json
from pathlib import Path

def create_collision_tiles():

    # Path to your collision file
    collision_file = Path("src/pokemon_agent/utils/ref_data/pokered_data/tilesets/collision_tile_ids.asm")

    collision_data = {}
    current_labels = []

    with collision_file.open("r", encoding="utf-8") as f:
        for line in f:
            # Remove comments and whitespace
            line = line.split(";")[0].strip()
            if not line or line.startswith("MACRO"):
                continue


            # Match labels like Underground_Coll:: or multiple stacked labels
            if line.endswith("::"):
                labels = [l.strip() for l in line.split("::") if l.strip()]
                current_labels = labels
                # Shared list for all stacked labels
                shared_list = []
                for label in labels:
                    collision_data[label] = shared_list
                continue

            # Match coll_tiles lines
            match = re.match(r'coll_tiles\s*(.*)', line)
            if match and current_labels:
                tiles_str = match.group(1).strip()
                if tiles_str:
                    # Split by commas and remove whitespace
                    tiles = [t.strip() for t in tiles_str.split(",") if t.strip()]
                    # Only keep valid hex tiles ($XX)
                    tiles = [int(t.replace("$", "0x"), 16) for t in tiles if t.startswith("$")]
                    # tiles = [t.replace("$", "0x") for t in tiles if t.startswith("$")]
                    collision_data[current_labels[0]].extend(tiles)


    collision_data.pop("RedsHouse1_Coll")
    collision_data["RedsHouse_Coll"] = collision_data.pop("RedsHouse2_Coll")
    collision_data.pop("Mart_Coll")
    collision_data.pop("Dojo_Coll")
    collision_data.pop("ForestGate_Coll")
    collision_data.pop("Museum_Coll")

    upper_collision_data = {k.upper(): v for k, v in collision_data.items()}

    # Save as JSON
    output_file = Path("src/pokemon_agent/utils/ref_data/maps/collision_tiles.json")
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(upper_collision_data, f, indent=4)

    print(f"Saved {len(upper_collision_data)} collision tile sets to {output_file}")


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


# # Example usage:
# all_maps = parse_asm_directory(ASM_DIR)
# with OUTPUT_JSON.open( "w", encoding="utf-8") as f:
#     json.dump(all_maps, f, indent=4, default=int)



# ====== add map connection coords to map_headers.json ======
import json
from pathlib import Path
from pokemon_agent.path_finder import *
from pokemon_agent.utils.utility_funcs import find_map_by_id
from tqdm import tqdm


def add_connection_xy_to_map_headers():

    with open('src/pokemon_agent/utils/ref_data/maps/map_headers.json', 'r') as f:
        MAP_HEADERS = json.load(f)
    with open('src/pokemon_agent/utils/ref_data/maps/collision_tiles.json', 'r') as f:
        COLLISION = json.load(f)
    with open('src/pokemon_agent/utils/ref_data/maps/map_objects.json', 'r') as f:
        MAP_OBJECTS = json.load(f)

    # Load to JSON
    INPUT_JSON = Path("src/pokemon_agent/utils/ref_data/maps/map_headers.json")
    with INPUT_JSON.open("r") as f:
        map_headers = json.load(f)

    OUTPUT_JSON = Path("src/pokemon_agent/utils/ref_data/maps/map_headers.json")

    # print(map_headers[6])
    upgraded_maps = []
    for map in map_headers:
        if map['connections_flags'] != '0':
            width = find_map_by_id(MAP_HEADERS, map['map_id']).get("map_width")
            height = find_map_by_id(MAP_HEADERS, map['map_id']).get("map_height")
            map_env = find_map_by_id(MAP_HEADERS, map['map_id']).get("environment")
            map_filename = find_map_by_id(MAP_HEADERS, map['map_id']).get("file")
            map_path = Path("src/pokemon_agent/utils/ref_data/maps/map_files") / f"{map_filename.replace(".asm",".blk")}" #/PalletTown.blk
            blockset_path = Path("src/pokemon_agent/utils/ref_data/maps/blocksets") / f"{map_env.lower()}.bst" #/overworld.bst
            WALKABLE_TILE_IDS = COLLISION.get(f"{map_env.replace("_","").upper()}_COLL")

            print(f"MAP: {map_filename}")

            blocks = load_blockset(blockset_path)
            map_blocks = load_map_blk(map_path, width, height)
            walk_matrix = generate_walkability_tile_matrix(blocks, map_blocks, WALKABLE_TILE_IDS)
            warp_tiles = get_warp_tiles(map_filename)
            valid_start_xy = []
            # try:
            if len(warp_tiles) > 0:
                for warp in warp_tiles:
                    valid_start_xy.append((warp.get("xy_coord")[0], warp.get("xy_coord")[1]+1))
                print("WARPS")
            # except:
            else:
                cropped_height = len(walk_matrix)-10
                cropped_width = len(walk_matrix[0])-10
                for y in range(10, cropped_height):
                    for x in range(10, cropped_width):
                        if y % 5 == 0 and x % 5 == 0: #limit combos
                            value = walk_matrix[y][x]
                            if value == True:
                                valid_start_xy.append((x,y))
                print("BRUTE_FORCE")
                # # Get coordinates of True cells
                # true_coords = [(x, y) for y, row in enumerate(walk_matrix) for x, val in enumerate(row) if val]
                # # Compute average (center of mass)
                # avg_x = sum(x for x, y in true_coords) / len(true_coords)
                # avg_y = sum(y for x, y in true_coords) / len(true_coords)
                # # Find True coordinate closest to the average point
                # warp_start = min(true_coords, key=lambda c: (c[0] - avg_x) ** 2 + (c[1] - avg_y) ** 2)

            # #get possible start tiles walk_matrix[y][x], crop area by 3 blocks in each direction
            # cropped_height = len(walk_matrix)-3
            # cropped_width = len(walk_matrix[0])-3
            # valid_start_xy = []
            # for y in range(3, cropped_height):
            #     for x in range(3, cropped_width):
            #         if y % 5 == 0 and x % 5 == 0: #limit combos
            #             value = walk_matrix[y][x]
            #             if value == True:
            #                 valid_start_xy.append((x,y))

            map_connections = []
            print(map["connections"])
            for connection in map["connections"]:
                if connection["direction"] == "west":
                    x_pot = [0]
                    y_pot = range(map["map_height"]*4)
                elif connection["direction"] == "east":
                    x_pot = [map["map_width"]*4 - 1] #max index (width)
                    y_pot = range(map["map_height"]*4)
                elif connection["direction"] == "north":
                    x_pot = range(map["map_width"]*4)
                    y_pot = [0]
                elif connection["direction"] == "south":
                    x_pot = range(map["map_width"]*4)
                    y_pot = [map["map_height"]*4 - 1] #max index (height)
                else:
                    x_pot = None
                    y_pot = None

                valid_connections=[]
                for start in tqdm(valid_start_xy, desc="Processing"):
                    for x in x_pot:
                        for y in y_pot:
                            path = astar(walk_matrix, start, (x, y))
                            if path:
                                valid_connections.append((x, y))
                
                connection["connection_coords"] = list(set(valid_connections))
                map_connections.append(connection)
            map["connections"] = map_connections
        upgraded_maps.append(map)

    # Save to JSON
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(upgraded_maps, f, indent=4, default=int)

# ====== create map_graph.json ======
from collections import deque, defaultdict
from pokemon_agent.utils.utility_funcs import camel_to_snake

with open('src/pokemon_agent/utils/ref_data/maps/map_headers.json', 'r') as f:
        MAP_HEADERS = json.load(f)

with open('src/pokemon_agent/utils/ref_data/maps/map_objects.json', 'r') as f:
        MAP_OBJECTS = json.load(f)

class MapGraph:
    def __init__(self):
        # graph[map_name] = list of (neighbor, metadata_dict)
        self.graph = defaultdict(list)

    def add_connection(self, map_a, map_b, meta=None):
        """Add a bidirectional edge between map_a and map_b.

        meta can contain offsets, coordinates, warp positions, etc.
        """
        if meta is None:
            meta = {}

        self.graph[map_a].append((map_b, meta))
        self.graph[map_b].append((map_a, meta))

    def neighbors(self, map_name):
        return self.graph.get(map_name, [])

    def find_path(self, start, goal):
        """Breadth-first search returning full path of maps from start → goal."""
        if start not in self.graph or goal not in self.graph:
            return None

        queue = deque([start])
        visited = {start: None}   # backpointers

        while queue:
            current = queue.popleft()

            if current == goal:
                return self._reconstruct_path(visited, start, goal)

            for neighbor, _meta in self.graph[current]:
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)

        return None  # no path

    def _reconstruct_path(self, visited, start, goal):
        path = [goal]
        while path[-1] != start:
            path.append(visited[path[-1]])
        return list(reversed(path))
    
    def to_dict(self):
        """Convert graph to serializable pure-Python structure."""
        out = {}
        for k, neighbors in self.graph.items():
            out[k] = [{"neighbor": n, "meta": m} for n, m in neighbors]
        return out

    @classmethod
    def from_dict(cls, data):
        g = cls()
        for map_name, neighbor_list in data.items():
            g.graph[map_name] = [(item["neighbor"], item["meta"]) for item in neighbor_list]
        return g

def create_map_graph():

    map_graph = MapGraph()

    # map_filename = find_map_by_filename(MAP_HEADERS, map_id).get("file")
    map_headers = []
    for map in MAP_HEADERS:
        map_data = {}
        if map["connections_flags"] not in ('0', '$0'):
            map_data["map_name"] = map["file"].replace(".asm", "")
            map_data["label"] = map["label"]
            connections = []
            for conn in map["connections"]:
                connections.append(conn["target_label"])

            map_data["connections"] = connections
            map_headers.append(map_data)
    
    # print(map_headers)
    map_objects = []
    for key, value in MAP_OBJECTS.items():
        map_data = {}
        map_data["map_name"] = key
        map_data["label"] = camel_to_snake(key).upper()
        connections = []
        for warp in value["warp_events"]:
            if warp["dest_map"] != 'LAST_MAP':
                connections.append(warp["dest_map"])
        map_data["connections"] = connections
        map_objects.append(map_data)
    # print(map_objects)

    #merge dicts
    map_dict = {}

    for map in map_headers + map_objects:
        label = map["label"]
        map_name = map["map_name"]
        conns = map.get("connections", [])

        if label not in map_dict:
            # Start new entry
            map_dict[label] = {
                "map_name": map_name,
                "connections": list(conns)  # make a copy
            }
        else:
            # Merge connections
            map_dict[label]["connections"].extend(conns)

    # print(map_dict)

    logged_connections=[]
    for k, v in map_dict.items():
        point_a = k
        for conn in v["connections"]:
            point_b = conn
            if (point_a, point_b) or (point_b, point_a) not in logged_connections: # and (point_b, point_a)
                map_graph.add_connection(point_a, point_b)
                # map_graph.add_connection(point_b, point_a)
                logged_connections.append((point_a, point_b))
                # logged_connections.append((point_b, point_a))

    # save map_graph.json
    with open("src/pokemon_agent/utils/ref_data/maps/map_graph.json", "w") as f:
        json.dump(map_graph.to_dict(), f, indent=2)
        










############################################################
#------------------------- MAIN ---------------------------#
############################################################

def main():
    # create_map_headers()
    # add_connection_xy_to_map_headers()

    # create_collision_tiles()
    # parse_asm_objects()

    create_map_graph()
    with open("src/pokemon_agent/utils/ref_data/maps/map_graph.json") as f:
        MAP_GRAPH = json.load(f)
    g = MapGraph.from_dict(MAP_GRAPH)
    print(g.find_path("OAKS_LAB", "PEWTER_CITY"))





if __name__ == "__main__":
    main()