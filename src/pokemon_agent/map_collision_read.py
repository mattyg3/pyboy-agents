# import sys
from pathlib import Path
# from PIL import Image, ImageDraw
from pyboy import PyBoy
import json
from utils.utility_funcs import find_map_by_id


# =========================================================
# 1. --- Load tiles from 2bpp format ---
# =========================================================
# def load_tileset_2bpp(path):
#     """
#     Load a tileset in 2bpp format (Game Boy graphics format).
#     Each tile = 8x8 pixels, 16 bytes total.
#     Returns a list of 8x8 tiles (each pixel value is 0–3).
#     """
#     data = path.read_bytes()
#     tile_size = 16
#     tiles = []

#     for t in range(0, len(data), tile_size):
#         tile_data = data[t : t + tile_size]
#         tile = []
#         for y in range(8):
#             byte1 = tile_data[y * 2]
#             byte2 = tile_data[y * 2 + 1]
#             row = []
#             for x in range(8):
#                 bit = 7 - x
#                 lo = (byte1 >> bit) & 1
#                 hi = (byte2 >> bit) & 1
#                 val = (hi << 1) | lo
#                 row.append(val)
#             tile.append(row)
#         tiles.append(tile)

#     return tiles


# =========================================================
# 2. --- Load blockset (4x4 tiles per block) ---
# =========================================================
def load_blockset(path):
    """
    Each block = 4x4 tiles (16 bytes)
    Each byte is an index into the tileset.
    """
    data = path.read_bytes()
    blocks = []

    for b in range(0, len(data), 16):
        block_data = data[b : b + 16]
        block = [[block_data[row * 4 + col] for col in range(4)] for row in range(4)]
        blocks.append(block)

    return blocks


# =========================================================
# 3. --- Load map (indices into blockset) ---
# =========================================================
def load_map_blk(path, width, height):
    """
    Each byte is an index into the blockset.
    Map = width × height blocks.
    """
    data = path.read_bytes()
    if len(data) < width * height:
        raise ValueError("Map file shorter than expected.")
    return [list(data[y * width : (y + 1) * width]) for y in range(height)]


# =========================================================
# 4. --- Get player location from PyBoy memory ---
# =========================================================
def get_player_position(pyboy):
    """
    Reads player map coordinates from Pokémon Red memory.
    Returns (x, y) in tile units.
    """
    mem = pyboy.memory

    # Player's X/Y coordinates in map blocks (tiles)
    player_x = mem[0xD362] * 2 #+1
    player_y = mem[0xD361] * 2 #+1
    looking_direction = mem[0xC109] #(0: down, 4: up, 8: left, $c: right)
    
    # Current map ID (not always needed for rendering one map)
    map_id = mem[0xD35E]

    return map_id, player_x, player_y, looking_direction #global_x, global_y, #player_x, player_y

def get_current_map(pyboy):
    mem = pyboy.memory
    map_id = mem[0xD35E]
    return map_id

# =========================================================
# 5. --- Collision and Walkability Grid ---
# =========================================================
def generate_walkability_tile_matrix(blocks, map_blocks, walkable_tiles):
    """
    Returns a 2D list of booleans at the TILE level.
    True = walkable, False = unwalkable.
    Each block = 4×4 tiles.
    """
    tiles_per_block = 4
    height_blocks = len(map_blocks)
    width_blocks = len(map_blocks[0])

    height_tiles = height_blocks * tiles_per_block
    width_tiles = width_blocks * tiles_per_block

    walk_matrix = [[False for _ in range(width_tiles)] for _ in range(height_tiles)]

    for by in range(height_blocks):
        for bx in range(width_blocks):
            block_idx = map_blocks[by][bx]
            if block_idx >= len(blocks):
                continue

            block = blocks[block_idx]
            for ty in range(tiles_per_block):
                for tx in range(tiles_per_block):
                    tile_id = block[ty][tx]
                    global_y = by * tiles_per_block + ty
                    global_x = bx * tiles_per_block + tx
                    walk_matrix[global_y][global_x] = tile_id in walkable_tiles

    return walk_matrix

def add_warp_tiles(walk_matrix, map_filename):
    map_name = map_filename.replace(".asm","")
    warp_events = MAP_OBJECTS.get(map_name).get("warp_events", None)
    try:
        for warp in warp_events:
            x = warp.get("x") * 2 +1
            y = warp.get("y") * 2 +1
            walk_matrix[y][x] = 'WARP'
    except:
        pass
    return walk_matrix


def get_warp_tiles(map_filename):
    map_name = map_filename.replace(".asm","")
    warp_events = MAP_OBJECTS.get(map_name).get("warp_events", None)
    warps=[]
    try:
        for warp in warp_events:
            x = warp.get("x") * 2 #+1
            y = warp.get("y") * 2 +1
            # y = warp.get("y") * 2 #+1
            dest = warp.get("dest_map")
            # warps.append((x,y)) 
            # warps["destination"] 
            warps.append({"destination":dest, "xy_coord":[x,y]})
    except:
        pass
    return warps

def get_map_connections(map_id, direction):
    # map_name = map_filename.replace(".asm","")
    map_connections = find_map_by_id(MAP_HEADERS, map_id).get("connections")
    connection_coords = []
    if map_connections != []:
        found_connection = next((c for c in map_connections if c["direction"].lower() == direction.lower()), None)
        # found_connections = [c for c in map_connections if c["direction"].lower() == direction.lower()]
        connection_coords = found_connection["connection_coords"]
    return connection_coords

def get_all_map_connections(map_id):
    # print(find_map_by_id(MAP_HEADERS, map_id).get("connections"))
    return find_map_by_id(MAP_HEADERS, map_id).get("connections")


def get_npc_coords(map_filename):
    map_name = map_filename.replace(".asm","")
    npc_events = MAP_OBJECTS.get(map_name).get("object_events", None)
    npcs=[]
    if npc_events != None and npc_events != []:
        try:
            for npc in npc_events:
                if npc.get("facing") == 'NONE':
                    pass
                else:
                    npcs.append({
                        "x": npc.get("x") * 2, #+1,
                        "y": npc.get("y") * 2 +1,
                        "sprite": npc.get("sprite"),
                        "name": npc.get("sprite").replace("SPRITE_", ""),
                        "text": npc.get("text"),
                        "movement": npc.get("movement"),
                        "facing": npc.get("facing"),
                    })
        except:
            pass
    return npcs

def get_map_signs(map_filename):
    map_name = map_filename.replace(".asm","")
    sign_events = MAP_OBJECTS.get(map_name).get("bg_events", None)
    signs=[]
    if sign_events != None and sign_events != []:
        try:
            for sign in sign_events:
                signs.append({
                    "x": sign.get("x") * 2, #+1,
                    "y": sign.get("y") * 2 +1,
                    "text": sign.get("text"),
                })
        except:
            pass
    return signs

def get_map_label(map_id):
    # print(find_map_by_id(MAP_HEADERS, map_id).get("label"))
    return find_map_by_id(MAP_HEADERS, map_id).get("label")

def get_map_filename(map_id):
    # print(find_map_by_id(MAP_HEADERS, map_id).get("file"))
    return find_map_by_id(MAP_HEADERS, map_id).get("file")


def print_tile_walk_matrix(matrix):
    """
    Prints a compact view of the walkability matrix.
    '-' = walkable, '#' = blocked
    """
    # for row in matrix:
    #     # print("".join("P" if cell in ("P", "PLAYER") else "." if cell else "#" for cell in row))
    #     line = ""
    #     for cell in row:
    #         if cell in ("P", "PLAYER"):
    #             line += "P"
    #         elif cell in ("W","WARP"):
    #             line += "W"
    #         elif cell:
    #             line += "-"
    #         else:
    #             line += "#"
    #     print(line)
    # print(matrix)

    rows = []
    for row in matrix:
        line = ""
        for cell in row:
            if cell in ("P", "PLAYER"):
                line += "P"
            elif cell in ("W","WARP"):
                line += "W"
            elif cell in ("G", "GOAL"):
                line += "G"
            elif cell:
                line += "-"
            else:
                line += "#"
        rows.append(line)
    walkable_grid_clean = "\n".join(rows)
    print(walkable_grid_clean)

def read_map(pyboy):
    map_id = get_current_map(pyboy)
    # print(f"Player at map {map_id}, X={px}, Y={py}, Looking={direction}") #(0: down, 4: up, 8: left, 12: right)
    # --- Load Map Values ---
    width = find_map_by_id(MAP_HEADERS, map_id).get("map_width")
    height = find_map_by_id(MAP_HEADERS, map_id).get("map_height")
    map_env = find_map_by_id(MAP_HEADERS, map_id).get("environment")
    map_filename = find_map_by_id(MAP_HEADERS, map_id).get("file")
    map_path = Path("src/pokemon_agent/utils/ref_data/maps/map_files") / f"{map_filename.replace(".asm",".blk")}" #/PalletTown.blk
    blockset_path = Path("src/pokemon_agent/utils/ref_data/maps/blocksets") / f"{map_env.lower()}.bst" #/overworld.bst
    WALKABLE_TILE_IDS = COLLISION.get(f"{map_env.replace("_","").upper()}_COLL")
    # print(f'WIDTH: {width}, HEIGHT: {height}, ENVR: {map_env}')

    # --- Load map graphics ---
    blocks = load_blockset(blockset_path)
    map_blocks = load_map_blk(map_path, width, height)

    walk_matrix = generate_walkability_tile_matrix(blocks, map_blocks, WALKABLE_TILE_IDS)
    # walk_matrix = add_warp_tiles(walk_matrix, map_filename)
    # walk_matrix[py][px] = 'PLAYER' #player location
    warp_tiles = get_warp_tiles(map_filename)

    return walk_matrix, width*4, height*4, warp_tiles



# =========================================================
# 6. --- Main: render + overlay player ---
# =========================================================
with open('src/pokemon_agent/utils/ref_data/maps/map_headers.json', 'r') as f:
    MAP_HEADERS = json.load(f)

with open('src/pokemon_agent/utils/ref_data/maps/collision_tiles.json', 'r') as f:
    COLLISION = json.load(f)

with open('src/pokemon_agent/utils/ref_data/maps/map_objects.json', 'r') as f:
    MAP_OBJECTS = json.load(f)

def main():

    ROM_PATH = 'ROMS/pokemon_red.gb'
    # LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'
    LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'

    # --- Start PyBoy in headless mode ---
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    pyboy.tick()  # initialize emulation
    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    while pyboy.tick():
        walk_matrix, map_width, map_height, warp_tiles = read_map(pyboy)
        pyboy.stop()

    # --- Print to console ---
    # print(walk_matrix)
    print("\nWalkable tile matrix ('-' = walkable, '#' = blocked):")
    print_tile_walk_matrix(walk_matrix)
    print(warp_tiles)

    map_id = get_current_map(pyboy)
    map_filename = find_map_by_id(MAP_HEADERS, map_id).get("file")

    print(get_npc_coords(map_filename))
    # print(get_map_signs(map_filename))


if __name__ == "__main__":
    main()

