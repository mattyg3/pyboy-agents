import sys
from pathlib import Path
from PIL import Image, ImageDraw
from pyboy import PyBoy


# =========================================================
# 1. --- Load tiles from 2bpp format ---
# =========================================================
def load_tileset_2bpp(path):
    """
    Load a tileset in 2bpp format (Game Boy graphics format).
    Each tile = 8x8 pixels, 16 bytes total.
    Returns a list of 8x8 tiles (each pixel value is 0–3).
    """
    data = path.read_bytes()
    tile_size = 16
    tiles = []

    for t in range(0, len(data), tile_size):
        tile_data = data[t : t + tile_size]
        tile = []
        for y in range(8):
            byte1 = tile_data[y * 2]
            byte2 = tile_data[y * 2 + 1]
            row = []
            for x in range(8):
                bit = 7 - x
                lo = (byte1 >> bit) & 1
                hi = (byte2 >> bit) & 1
                val = (hi << 1) | lo
                row.append(val)
            tile.append(row)
        tiles.append(tile)

    return tiles


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
# 4. --- Render map to Image ---
# =========================================================
def render_map(tileset, blocks, map_blocks):
    """
    Assemble the map into a PIL Image.
    - Each tile = 8×8 px
    - Each block = 4×4 tiles
    - Each map cell = 32×32 px
    """
    tiles_per_block = 4
    tile_size = 8
    block_px = tiles_per_block * tile_size

    height_blocks = len(map_blocks)
    width_blocks = len(map_blocks[0])

    img_w = width_blocks * block_px
    img_h = height_blocks * block_px

    # Create grayscale image (mode "L")
    img = Image.new("L", (img_w, img_h))

    # Map grayscale palette (0–3 -> 255–0 for GB style)
    palette = [255, 170, 85, 0]

    for by in range(height_blocks):
        for bx in range(width_blocks):
            block_idx = map_blocks[by][bx]
            if block_idx >= len(blocks):
                continue
            block = blocks[block_idx]

            # Draw block
            for ty in range(tiles_per_block):
                for tx in range(tiles_per_block):
                    tile_idx = block[ty][tx]
                    if tile_idx >= len(tileset):
                        continue
                    tile = tileset[tile_idx]

                    for py in range(tile_size):
                        for px in range(tile_size):
                            color = palette[tile[py][px]]
                            x = bx * block_px + tx * tile_size + px
                            y = by * block_px + ty * tile_size + py
                            img.putpixel((x, y), color)

    return img

# =========================================================
# 5. --- Get player location from PyBoy memory ---
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
    # global_x = mem[0xD35C]
    # global_y = mem[0xD35D]

    # player_x = mem[0xC205]
    # player_y = mem[0xC204]

    # player_x = mem[0xC106]
    # player_y = mem[0xC104]

    # player_x_off = mem[0xC105]
    # player_y_off = mem[0xC103]

    looking_direction = mem[0xC109] #(0: down, 4: up, 8: left, $c: right)
    

    # Current map ID (not always needed for rendering one map)
    map_id = mem[0xD35E]

    return map_id, player_x, player_y, looking_direction #global_x, global_y, #player_x, player_y

# =========================================================
# 6. --- Collision and Walkability Grid ---
# =========================================================
# IMPASSABLE_TILE_IDS = [0x00, 0x10, 0x1b, 0x20, 0x21, 0x23, 0x2c, 0x2d, 0x2e, 0x30, 0x31, 0x33, 0x39, 0x3c, 0x3e, 0x52, 0x54, 0x58, 0x5b] #from collision_tile_ids
WALKABLE_TILE_IDS = [0x00, 0x10, 0x1b, 0x20, 0x21, 0x23, 0x2c, 0x2d, 0x2e, 0x30, 0x31, 0x33, 0x39, 0x3c, 0x3e, 0x52, 0x54, 0x58, 0x5b] #from collision_tile_ids, actually walkable tiles?

def is_block_walkable(block, impassable_tiles):
    """
    Returns True if all tiles in this block are walkable.
    """
    for row in block:
        for tile_id in row:
            if tile_id in impassable_tiles:
                return False
    return True

def generate_walkability_matrix(blocks, map_blocks, impassable_tiles):
    """
    Returns a 2D list of booleans: True = walkable, False = blocked.
    """
    matrix = []
    for row in map_blocks:
        matrix_row = []
        for block_idx in row:
            if block_idx < len(blocks):
                walkable = is_block_walkable(blocks[block_idx], impassable_tiles)
                matrix_row.append(walkable)
            else:
                matrix_row.append(False)
        matrix.append(matrix_row)
    return matrix

def overlay_walkability(draw, walk_matrix, block_size):
    """
    Overlay red translucent rectangles on unwalkable blocks.
    """
    for y, row in enumerate(walk_matrix):
        for x, walkable in enumerate(row):
            if not walkable:
                x0, y0 = x * block_size, y * block_size
                x1, y1 = x0 + block_size, y0 + block_size
                draw.rectangle([x0, y0, x1, y1], outline="red", width=1)

# def generate_walkability_tile_matrix(blocks, map_blocks, impassable_tiles):
#     """
#     Returns a 2D list of booleans at the TILE level.
#     True = walkable, False = blocked.
#     Each block is 4×4 tiles.
#     """
#     tiles_per_block = 4
#     height_blocks = len(map_blocks)
#     width_blocks = len(map_blocks[0])

#     height_tiles = height_blocks * tiles_per_block
#     width_tiles = width_blocks * tiles_per_block

#     walk_matrix = [[True for _ in range(width_tiles)] for _ in range(height_tiles)]

#     for by in range(height_blocks):
#         for bx in range(width_blocks):
#             block_idx = map_blocks[by][bx]
#             if block_idx >= len(blocks):
#                 continue

#             block = blocks[block_idx]
#             for ty in range(tiles_per_block):
#                 for tx in range(tiles_per_block):
#                     tile_id = block[ty][tx]
#                     walkable = tile_id not in impassable_tiles
#                     global_y = by * tiles_per_block + ty
#                     global_x = bx * tiles_per_block + tx
#                     walk_matrix[global_y][global_x] = walkable

#     return walk_matrix

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


def print_tile_walk_matrix(matrix):
    """
    Prints a compact view of the walkability matrix.
    '.' = walkable, '#' = blocked
    """
    for row in matrix:
        print("".join("P" if cell == "P" else "." if cell else "#" for cell in row))

def overlay_tile_walkability(draw, walk_matrix, tile_size):
    """
    Draws red outlines for unwalkable tiles.
    """
    for y, row in enumerate(walk_matrix):
        for x, walkable in enumerate(row):
            if not walkable:
                x0, y0 = x * tile_size, y * tile_size
                x1, y1 = x0 + tile_size, y0 + tile_size
                draw.rectangle([x0, y0, x1, y1], outline="red", width=1)

# =========================================================
# 7. --- Main: render + overlay player ---
# =========================================================
def main():

    ROM_PATH = 'ROMS/pokemon_red.gb'
    tileset_path = Path("src/pokemon_agent/utils/ref_data/maps/tilesets/overworld.2bpp")
    blockset_path = Path("src/pokemon_agent/utils/ref_data/maps/blocksets/overworld.bst")
    map_path = Path("src/pokemon_agent/utils/ref_data/maps/map_files/PalletTown.blk")
    # tileset_path = Path("src/pokemon_agent/utils/ref_data/maps/tilesets/gym.2bpp")
    # blockset_path = Path("src/pokemon_agent/utils/ref_data/maps/blocksets/gym.bst")
    # map_path = Path("src/pokemon_agent/utils/ref_data/maps/map_files/OaksLab.blk")
    width = 10
    height = 9
    out_path = Path("src/pokemon_agent/saves/render_map_test.png")
    # LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown_right.sav'
    LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'
    # LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'

    # --- Start PyBoy in headless mode ---
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    pyboy.tick()  # initialize emulation
    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    while pyboy.tick():

        # --- Get player position ---
        map_id, px, py, direction = get_player_position(pyboy)
        print(f"Player at map {map_id}, X={px}, Y={py}, Looking={direction}") #(0: down, 4: up, 8: left, 12: right)

        # --- Load map graphics ---
        tiles = load_tileset_2bpp(tileset_path)
        blocks = load_blockset(blockset_path)
        map_blocks = load_map_blk(map_path, width, height)

        # --- Render base map ---
        img = render_map(tiles, blocks, map_blocks).convert("RGB")

        # --- Overlay player marker ---
        draw = ImageDraw.Draw(img)
        block_size = 32  # pixels per map block (4x4 tiles)
        tile_size = 8
        player_px = px * tile_size
        player_py = py * tile_size

        # Red square marker
        marker_size = 5
        draw.rectangle(
            [(player_px - marker_size, player_py - marker_size),
            (player_px + marker_size, player_py + marker_size)],
            outline="red", width=2, fill="red"
        )

        

    pyboy.stop()
    img.save(out_path)
    print(f"Saved map with player marker to {out_path}")


    # walk_matrix = generate_walkability_matrix(blocks, map_blocks, IMPASSABLE_TILE_IDS)
    # # print("\nWalkability matrix (True=walkable, False=blocked):")
    # for row in walk_matrix:
    #     print(" ".join(["." if w else "#" for w in row]))

    # # --- Overlay walkability ---
    # # overlay_walkability(draw, walk_matrix, block_size)

    # --- Compute tile-level walkability matrix ---
    walk_matrix = generate_walkability_tile_matrix(blocks, map_blocks, WALKABLE_TILE_IDS)
    walk_matrix[py][px] = 'P' #player location

    # --- Print to console ---
    print("\nWalkable tile matrix ('.' = walkable, '#' = blocked):")
    print_tile_walk_matrix(walk_matrix)


if __name__ == "__main__":
    main()

