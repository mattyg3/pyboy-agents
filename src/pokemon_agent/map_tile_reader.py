from pyboy import PyBoy #, WindowEvent
from collections import deque
import numpy as np
import time
import json

ROM_PATH = "ROMS/pokemon_red.gb"
# --- Load RAM address references ---
with open('src/pokemon_agent/utils/ref_data/ram_addresses.json', 'r') as f:
    RAM_POINTERS = json.load(f)

def get_mem_pointer(address_book, pointer_name):
    """Get a memory address by name from the JSON reference."""
    return int(next(entry["address"] for entry in RAM_POINTERS[address_book]
                    if entry["name"] == pointer_name), 16)

def get_player_position(mem):
    # x = mem[0xD361]
    # y = mem[0xD362]
    x = mem[get_mem_pointer("system_addresses", "player_x")]
    y = mem[get_mem_pointer("system_addresses", "player_y")]
    map_id = mem[0xD35E]
    # map_id = mem[0xD367]

    return x, y, map_id

def get_collision_map(mem):
    """Reads current visible map collision data."""
    base = 0xC3A0
    width, height = 20, 18
    data = [mem[base + i] for i in range(width * height)]
    grid = np.array(data).reshape(height, width)
    return grid

def get_warp_positions(mem):
    """Get up to 4 warp tiles (doors) for current map."""
    warps = []
    for i in range(4):
        y = mem[0xD4A0 + i*4]
        x = mem[0xD4A1 + i*4]
        print(f"{x}, {y}")
        # print(mem[0xD370])
        if x != 0xFF and y != 0xFF:  # valid warp
        # if x == 0x16 and y == 0x16:  # valid warp
            warps.append((x, y))
        # warps[(9,5)]
    return warps

# def get_warp_positions(mem, rom):
#     """
#     Returns a list of warp tiles for the current map.
#     Each warp is a tuple: (x, y, dest_map_group, dest_map_id)
#     """
#     warps = []
#     # Get warp table pointer from map header
#     warp_pointer = mem[0xD36E] + (mem[0xD36F] << 8)
    
#     for i in range(4):
#         y = rom[warp_pointer + i*4]
#         x = rom[warp_pointer + i*4 + 1]
#         # dest_map_group = mem[warp_pointer + i*4 + 2]
#         # dest_map_id = mem[warp_pointer + i*4 + 3]
        
#         if x != 0xFF and y != 0xFF:
#             # warps.append((x, y, dest_map_group, dest_map_id))
#             warps.append((x, y))

    
#     return warps

def is_walkable(tile_id):
    # Simplified heuristic: floor tiles, not walls/books
    return tile_id in {0x11, 0x06
        # 0x05, 0x06, 0x07, 0x10, 0x11, 0x12,
        # 0x29, 0x2A, 0x34, 0x43, 0x44
    }

def build_walkable_grid(mem):
    collision = get_collision_map(mem)
    walkable = np.vectorize(is_walkable)(collision)
    return walkable

def bfs_path(grid, start, goal):
    """Simple BFS pathfinder on a boolean grid."""
    h, w = grid.shape
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        (x, y), path = queue.popleft()
        if (x, y) == goal:
            return path
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
    return None

def move_towards(pyboy, from_xy, to_xy):
    dx, dy = to_xy[0] - from_xy[0], to_xy[1] - from_xy[1]
    if dx == 1:
        # pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)
        pyboy.button_press("right")
        print("RIGHT")
        for _ in range(10):
            pyboy.tick()
        pyboy.button_release("right")
    elif dx == -1:
        # pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
        pyboy.button_press("left")
        print("LEFT")
        for _ in range(10):
            pyboy.tick()
        pyboy.button_release("left")
    elif dy == 1:
        # pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        pyboy.button_press("down")
        print("DOWN")
        for _ in range(10):
            pyboy.tick()
        pyboy.button_release("down")
        
    elif dy == -1:
        # pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
        pyboy.button_press("up")
        print("UP")
        for _ in range(10):
            pyboy.tick()
        pyboy.button_release("up")
        

    # for _ in range(8):
    #     pyboy.tick()
        
    # pyboy.send_input(WindowEvent.RELEASE_ALL)
    pyboy.tick()

def main():
    pyboy = PyBoy(ROM_PATH, window_type="SDL2")  # set to "SDL2" to see screen
    # Load Save State
    LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)
    
    mem = pyboy.memory

    # Wait a few frames for stability
    for _ in range(60):
        pyboy.tick()

    player_x, player_y, map_id = get_player_position(mem)
    print(f"Current map={map_id}, player=({player_x},{player_y})")

    warps = get_warp_positions(mem) #, rom
    print("Detected warps:", warps)
    if not warps:
        print("No warps found!")
        return

    exit_tile = warps[0]  # assume first warp is the door
    print(f"Target exit tile: {exit_tile}")

    grid = build_walkable_grid(mem)
    print(grid)

    # NOTE: grid uses (x,y) -> grid[y][x]
    start = (player_x, player_y)
    goal = exit_tile

    path = bfs_path(grid, start, goal)
    if not path:
        print("No path found!")
        return

    print("Path:", path)

    current = start
    for step in path[1:]:
        move_towards(pyboy, current, step)
        current = step
        time.sleep(0.05)

    print("Reached exit tile!")

    pyboy.stop()

if __name__ == "__main__":
    main()


# from pyboy import PyBoy
# import json
# import time

# # --- Load RAM address references ---
# with open('src/pokemon_agent/utils/ref_data/ram_addresses.json', 'r') as f:
#     RAM_POINTERS = json.load(f)

# def get_mem_pointer(address_book, pointer_name):
#     """Get a memory address by name from the JSON reference."""
#     return int(next(entry["address"] for entry in RAM_POINTERS[address_book]
#                     if entry["name"] == pointer_name), 16)
# def is_walkable(tile_id):
#     # Simplified heuristic: floor tiles, not walls/books
#     return tile_id in {
#          0x11
#         # 0x05, 0x06, 0x07, 0x10, 0x11, 0x12,
#         # 0x29, 0x2A, 0x34, 0x43, 0x44
#     }

# def build_walkable_grid(mem):
#     # mem = pyboy.memory
#     collision = read_visible_tiles(mem)
#     walkable = np.vectorize(is_walkable)(collision)
#     return walkable
# # --- Visible Tile Reader ---
# # def read_visible_tiles(pyboy):
# #     """
# #     Reads the current on-screen 20x18 tile buffer (0xC3A0–0xC507)
# #     and returns a 2D list of tile IDs + player on-screen position.
# #     """

# #     mem = pyboy.memory

# #     # --- Player and camera positions ---
# #     player_x = mem[get_mem_pointer("system_addresses", "player_x")]
# #     player_y = mem[get_mem_pointer("system_addresses", "player_y")]
# #     camera_x = mem[get_mem_pointer("system_addresses", "camera_x")]
# #     camera_y = mem[get_mem_pointer("system_addresses", "camera_y")]

# #     # On-screen coordinates (relative to camera)
# #     screen_x = player_x - camera_x
# #     screen_y = player_y - camera_y

# #     base_addr = 0xC3A0
# #     width, height = 20, 18

# #     tiles = []
# #     for y in range(height):
# #         row = []
# #         for x in range(width):
# #             row.append(mem[base_addr + y * width + x])
# #         tiles.append(row)

# #     print(f"Player Map Pos: ({player_x}, {player_y})")
# #     print(f"Camera Top-Left: ({camera_x}, {camera_y})")
# #     print(f"Player Screen Pos: ({screen_x}, {screen_y})")

# #     return tiles, screen_x, screen_y

# # # # --- Walkability Calculator ---
# # # def get_walkable_tiles(pyboy):
# # #     """
# # #     Reads the visible map and collision data from Pokémon Red (via PyBoy)
# # #     and returns a 2D list of booleans indicating walkable tiles.
# # #     """
# # #     mem = pyboy.memory
# # #     map_header_ptr = mem[0xD366] + (mem[0xD367] << 8)
# # #     collision_ptr = mem[map_header_ptr + 3] + (mem[map_header_ptr + 4] << 8)
# # #     collision_table = [mem[collision_ptr + i] for i in range(256)]

# # #     base_addr = 0xC3A0
# # #     width, height = 20, 18
# # #     walkable = []
# # #     for y in range(height):
# # #         row = []
# # #         for x in range(width):
# # #             tile_id = mem[base_addr + y * width + x]
# # #             collision_value = collision_table[tile_id]
# # #             row.append(collision_value == 0x00)
# # #         walkable.append(row)
# # #     return walkable

# # # # --- Main ---
# # # if __name__ == "__main__":
# # #     pyboy = PyBoy('ROMS/pokemon_red.gb', window='SDL2')

# # #     LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'
# # #     with open(LOAD_STATE_PATH, "rb") as f:
# # #         pyboy.load_state(f)

# # #     # Let the game initialize
# # #     for _ in range(500):
# # #         pyboy.tick()

# # #     # Read visible tiles
# # #     tiles, screen_x, screen_y = read_visible_tiles(pyboy)

# # #     # Optional: get walkable map
# # #     # walkable = get_walkable_tiles(pyboy)
# # #     # tiles = read_visible_tiles(pyboy)

# # #     # Print numeric grid of tile IDs
# # #     for row in tiles:
# # #         print(' '.join(f"{t:02X}" for t in row))

# # #     # --- Print visible map with player marker ---
# # #     print("\nVisible Tile Map (player marked as '@'):")
# # #     width, height = 20, 18
# # #     for y in range(height):
# # #         row_display = []
# # #         for x in range(width):
# # #             if y == screen_y and x == screen_x:
# # #                 row_display.append('@')
# # #             else:
# # #                 row_display.append('.' if x==11 else '#')
# # #         print(''.join(row_display))

# # #     pyboy.stop()



# from pyboy import PyBoy
# import time

# # def get_walkable_tiles(pyboy):
# #     """
# #     Reads the visible map and collision data from Pokémon Red (via PyBoy)
# #     and returns a 2D list of booleans indicating walkable tiles.

# #     True = walkable
# #     False = blocked
# #     """

# #     mem = pyboy.memory

# #     # --- Step 1: Get map header pointer ---
# #     map_header_ptr = mem[0xD366] + (mem[0xD367] << 8)

# #     # --- Step 2: Get collision table pointer from header ---
# #     # collision pointer = header + 3 (little-endian word)
# #     collision_ptr = mem[map_header_ptr + 3] + (mem[map_header_ptr + 4] << 8)

# #     # --- Step 3: Load collision table (up to 256 entries) ---
# #     collision_table = [mem[collision_ptr + i] for i in range(256)]

# #     # --- Step 4: Get visible tilemap (20x18) ---
# #     tilemap_base = 0xC3A0#0xD5B0
# #     width, height = 20, 18

# #     walkable = []
# #     for y in range(height):
# #         row = []
# #         for x in range(width):
# #             tile_id = mem[tilemap_base + y * width + x]
# #             collision_value = collision_table[tile_id]

# #             # Most maps: 0x00 = walkable, anything else = blocked
# #             row.append(collision_value == 0x00)
# #         walkable.append(row)

# #     return walkable
# # def get_walkable_tiles(tiles):
     
# #      return walkable

# def read_visible_tiles(pyboy):
#     """
#     Reads the current on-screen 20x18 tile buffer (0xC3A0–0xC507)
#     and returns a 2D list of tile IDs.
#     """

#     mem = pyboy.memory
#     # x = mem[get_mem_pointer("system_addresses", "player_x")]
#     # y = mem[get_mem_pointer("system_addresses", "player_y")]
#     # x = mem[0xC106]
#     # y = mem[0xC104]
#     # x = mem[0xC105]
#     # y = mem[0xC103]
#     x = mem[0xC205]
#     y = mem[0xC204]
#     base_addr = 0xC3A0
#     width, height = 20, 18
#     total_tiles = width * height  # 360

#     tiles = []
#     for y in range(height):
#         row = []
#         for x in range(width):
#             row.append(mem[base_addr + y * width + x])
#         tiles.append(row)
    
#     print(f"X: {x}, Y: {y}")

#     return tiles
# import json
# with open('src/pokemon_agent/utils/ref_data/ram_addresses.json', 'r') as f:
#     RAM_POINTERS = json.load(f)
# def get_mem_pointer(address_book, pointer_name):
#         return int(next(entry["address"] for entry in RAM_POINTERS[address_book] if entry["name"] == pointer_name), 16)

# # Load ROM (make sure the path is correct)
# pyboy = PyBoy('ROMS/pokemon_red.gb', window='SDL2')  # Use 'SDL2' for GUI window
# # pyboy.set_emulation_speed(0)
# # Load Save State
# LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'
# with open(LOAD_STATE_PATH, "rb") as f:
#         pyboy.load_state(f)

# # Wait for the game to boot up
# for _ in range(500):  # Run ~500 frames (~8 seconds)
#     pyboy.tick()

# # # Access memory directly
# # mem = pyboy.memory

# # # WRAM0 starts at 0xC000, tile buffer is at 0xC3E0
# # tilemap_address = 0xC3E0
# # tilemap_size = 20 * 18  # 360 tiles

# # tile_bytes = mem[tilemap_address: tilemap_address + tilemap_size]
# # tile_ids = list(tile_bytes)

# # # Print the tilemap as a 20x18 grid
# # print("Visible Tile Map (20x18):")
# # for y in range(18):
# #     row = tile_ids[y*20:(y+1)*20]
# #     print(' '.join(f"{tile:02X}" for tile in row))


# # walkable_grid = get_walkable_tiles(pyboy)

# # # Print simple text map ('.' = walkable, '#' = blocked)
# # for row in walkable_grid:
# #     print(''.join('.' if t else '#' for t in row))

# tiles = read_visible_tiles(pyboy)

# # print(build_walkable_grid(pyboy))
# # Print numeric grid of tile IDs
# for row in tiles:
#     print(' '.join(f"{t:02X}" for t in row))

# # for row in tiles:
# #     print(' '.join(f"{t}" for t in row))
# walkable = np.vectorize(is_walkable)(tiles)
# print(walkable)
# # for row in tiles:
# #      print(' '.join(if t==11 True else False for t in row))


# # Close emulator
# pyboy.stop()
