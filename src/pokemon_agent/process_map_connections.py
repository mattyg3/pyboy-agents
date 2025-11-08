# ====== add map connection coords to map_headers.json ======
import json
from pathlib import Path
from path_finder import *
from utils.utility_funcs import find_map_by_id
from tqdm import tqdm


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

OUTPUT_JSON = Path("src/pokemon_agent/utils/ref_data/maps/map_headers_upgraded3.json")

from collections import deque

def compute_world_offsets(maps, start_map="PALLETTOWN"):
    """
    Given list of maps (each with `name`, `map_width`, `map_height`, and `connections` list),
    compute absolute (x,y) offsets for all maps in a shared world coordinate system.

    Returns dict: { map_name: (world_x, world_y) }
    where (world_x, world_y) = top-left corner in global coordinates.
    """

    # Build lookup by name
    maps_by_name = {m["name"]: m for m in maps}
    world_offsets = {}
    queue = deque()

    # Start at chosen origin map
    world_offsets[start_map] = (0, 0)
    queue.append(start_map)

    while queue:
        current = queue.popleft()
        cx, cy = world_offsets[current]
        cmap = maps_by_name[current]

        for conn in cmap.get("connections", []):
            target = conn["target_name"].upper()
            if target not in maps_by_name:
                continue  # skip unknown map names
            if target in world_offsets:
                continue  # already placed

            direction = conn["direction"].lower()
            offset = conn["offset"]

            tmap = maps_by_name[target]
            tw, th = tmap["map_width"], tmap["map_height"]
            cw, ch = cmap["map_width"], cmap["map_height"]

            # Compute target top-left based on connection direction
            if direction == "north":
                # Target is above current map
                tx = cx + offset
                ty = cy - th
            elif direction == "south":
                tx = cx - offset
                ty = cy + ch
            elif direction == "west":
                tx = cx - tw
                ty = cy + offset
            elif direction == "east":
                tx = cx + cw
                ty = cy - offset
            else:
                raise ValueError(f"Unknown direction {direction}")

            world_offsets[target] = (tx, ty)
            queue.append(target)

    return world_offsets

import numpy as np

def combine_world_maps(maps, world_offsets):
    """
    Combine all maps into a single large 2D matrix of walkable tiles.

    Parameters:
      maps: list of dicts, each with:
            - name
            - map_width
            - map_height
            - tiles: 2D list or np.array (True=walkable, False=blocked)
      world_offsets: dict { map_name: (world_x, world_y) }
                     from compute_world_offsets()

    Returns:
      world_matrix: 2D np.array (bool)
      world_origin: (min_x, min_y) for translating back to world coords
    """
    # Find bounds of combined world
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")

    for m in maps:
        if m["name"] not in world_offsets:
            continue
        ox, oy = world_offsets[m["name"]]
        w, h = m["map_width"], m["map_height"]
        min_x = min(min_x, ox)
        min_y = min(min_y, oy)
        max_x = max(max_x, ox + w)
        max_y = max(max_y, oy + h)

    world_w = max_x - min_x
    world_h = max_y - min_y

    # Create empty world matrix
    world = np.zeros((world_h, world_w), dtype=bool)

    # Paste each map into world matrix
    for m in maps:
        name = m["name"]
        if name not in world_offsets:
            continue
        ox, oy = world_offsets[name]
        local_x = ox - min_x
        local_y = oy - min_y

        tiles = np.array(m["tiles"], dtype=bool)
        h, w = tiles.shape
        world[local_y:local_y+h, local_x:local_x+w] = np.logical_or(
            world[local_y:local_y+h, local_x:local_x+w],
            tiles
        )

    return world, (min_x, min_y)

import numpy as np

def find_connection_coords(maps, world_offsets, world_matrix, world_origin):
    """
    Detect (x, y) coordinates of connections between adjacent maps.

    Parameters:
      maps: list of map dicts, each with "name", "map_width", "map_height", "tiles"
      world_offsets: dict { map_name: (world_x, world_y) }
      world_matrix: 2D numpy array of combined world walkability (True=walkable)
      world_origin: (min_x, min_y) tuple from combine_world_maps()

    Returns:
      List of dicts:
        {
          "map_a": str,
          "map_b": str,
          "coords_a": [(ax, ay), ...],
          "coords_b": [(bx, by), ...],
          "direction": "north"/"south"/"east"/"west"
        }
    """
    results = []
    maps_by_name = {m["name"]: m for m in maps}
    world_h, world_w = world_matrix.shape

    # Helper: check in world bounds
    def in_bounds(x, y):
        return 0 <= y < world_h and 0 <= x < world_w

    # Loop through every map and its connections
    for m in maps:
        name = m["name"]
        if name not in world_offsets:
            continue
        ox, oy = world_offsets[name]
        cx = ox - world_origin[0]
        cy = oy - world_origin[1]

        for conn in m.get("connections", []):
            target = conn["target_name"].upper()
            if target not in world_offsets:
                continue
            direction = conn["direction"].lower()

            # Calculate overlapping border between the two maps
            tmap = maps_by_name[target]
            tx, ty = world_offsets[target]
            tx -= world_origin[0]
            ty -= world_origin[1]

            h, w = m["map_height"], m["map_width"]
            th, tw = tmap["map_height"], tmap["map_width"]

            border_a, border_b = [], []

            # Compare edge tiles depending on direction
            if direction == "north":
                # Top map touches above
                y_a = cy  # top of current
                y_b = ty + th - 1  # bottom of target
                for x in range(w):
                    wx_a = cx + x
                    wx_b = wx_a - (ox - tx)
                    if in_bounds(wx_a, y_a) and in_bounds(wx_b, y_b):
                        if world_matrix[y_a][wx_a] and world_matrix[y_b][wx_b]:
                            border_a.append((wx_a + world_origin[0], y_a + world_origin[1]))
                            border_b.append((wx_b + world_origin[0], y_b + world_origin[1]))

            elif direction == "south":
                y_a = cy + h - 1  # bottom of current
                y_b = ty  # top of target
                for x in range(w):
                    wx_a = cx + x
                    wx_b = wx_a - (ox - tx)
                    if in_bounds(wx_a, y_a) and in_bounds(wx_b, y_b):
                        if world_matrix[y_a][wx_a] and world_matrix[y_b][wx_b]:
                            border_a.append((wx_a + world_origin[0], y_a + world_origin[1]))
                            border_b.append((wx_b + world_origin[0], y_b + world_origin[1]))

            elif direction == "west":
                x_a = cx
                x_b = tx + tw - 1
                for y in range(h):
                    wy_a = cy + y
                    wy_b = wy_a - (oy - ty)
                    if in_bounds(x_a, wy_a) and in_bounds(x_b, wy_b):
                        if world_matrix[wy_a][x_a] and world_matrix[wy_b][x_b]:
                            border_a.append((x_a + world_origin[0], wy_a + world_origin[1]))
                            border_b.append((x_b + world_origin[0], wy_b + world_origin[1]))

            elif direction == "east":
                x_a = cx + w - 1
                x_b = tx
                for y in range(h):
                    wy_a = cy + y
                    wy_b = wy_a - (oy - ty)
                    if in_bounds(x_a, wy_a) and in_bounds(x_b, wy_b):
                        if world_matrix[wy_a][x_a] and world_matrix[wy_b][x_b]:
                            border_a.append((x_a + world_origin[0], wy_a + world_origin[1]))
                            border_b.append((x_b + world_origin[0], wy_b + world_origin[1]))

            if border_a:
                results.append({
                    "map_a": name,
                    "map_b": target,
                    "direction": direction,
                    "coords_a": border_a,
                    "coords_b": border_b,
                })

    return results


maps = []
for map in map_headers:
    if map['connections_flags'] != '0':
        width = find_map_by_id(MAP_HEADERS, map['map_id']).get("map_width")
        height = find_map_by_id(MAP_HEADERS, map['map_id']).get("map_height")
        map_env = find_map_by_id(MAP_HEADERS, map['map_id']).get("environment")
        map_filename = find_map_by_id(MAP_HEADERS, map['map_id']).get("file")
        map_name = find_map_by_id(MAP_HEADERS, map['map_id']).get("name")
        map_path = Path("src/pokemon_agent/utils/ref_data/maps/map_files") / f"{map_filename.replace(".asm",".blk")}" #/PalletTown.blk
        blockset_path = Path("src/pokemon_agent/utils/ref_data/maps/blocksets") / f"{map_env.lower()}.bst" #/overworld.bst
        WALKABLE_TILE_IDS = COLLISION.get(f"{map_env.replace("_","").upper()}_COLL")

        print(f"MAP: {map_filename}")

        blocks = load_blockset(blockset_path)
        map_blocks = load_map_blk(map_path, width, height)
        walk_matrix = generate_walkability_tile_matrix(blocks, map_blocks, WALKABLE_TILE_IDS)

        curr_map = {
            "name": map_name,
            "map_width": len(walk_matrix[0]),
            "map_height": len(walk_matrix),
            "tiles": walk_matrix,
            "connections": map["connections"],
        }
        maps.append(curr_map)
# print(maps)
offsets = compute_world_offsets(maps)

# for name, (x, y) in offsets.items():
#     print(f"{name:15} -> world offset: ({x}, {y})")
# print(offsets)

world_matrix, world_origin = combine_world_maps(maps, offsets)

# print("World origin:", world_origin)
# print("World matrix:")
# for row in world_matrix:
#     print("".join("." if cell else "#" for cell in row))
connections = find_connection_coords(maps, offsets, world_matrix, world_origin)

for c in connections:
    print(f"{c['map_a']} → {c['map_b']} ({c['direction']}): {len(c['coords_a'])} tiles")
    for a, b in zip(c["coords_a"], c["coords_b"]):
        print(f"  {a} ↔ {b}")