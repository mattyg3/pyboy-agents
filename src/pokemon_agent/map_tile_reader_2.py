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

# def read_map(memory):
#     map_ptr = memory[0xD35E] + (memory[0xD35F] << 8)
#     width = memory[0xD35F]
#     height = memory[0xD360]
#     return [memory[map_ptr + i] for i in range(width * height)], width, height

def get_player_position(mem):
    # x = mem[0xD361]
    # y = mem[0xD362]
    # x = mem[0xD364]
    # y = mem[0xD363]
    # x = mem[get_mem_pointer("system_addresses", "player_x")]
    # y = mem[get_mem_pointer("system_addresses", "player_y")]
    #FLIP X AND Y
    x = mem[get_mem_pointer("system_addresses", "player_y")]
    y = mem[get_mem_pointer("system_addresses", "player_x")]
    map_id = mem[0xD35E]
    # map_id = mem[0xD367]

    return x, y, map_id

def get_collision_map(mem):
    """Reads current visible map collision data."""
    base = 0xC3A0
    width, height = 20, 18
    data = [mem[base + i] for i in range(width * height)]
    grid = np.array(data).reshape(height, width)
    return grid, width, height

def is_walkable(tile_id):
    # Simplified heuristic: floor tiles, not walls/books
    return tile_id in {0x11, 0x06, 0x16
        # 0x05, 0x06, 0x07, 0x10, 0x11, 0x12,
        # 0x29, 0x2A, 0x34, 0x43, 0x44
    }

def build_walkable_grid(mem, grid):
    # collision, w, h = get_collision_map(mem)
    walkable = np.vectorize(is_walkable)(grid)
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

# flat_map, w, h = read_map(mb)
# map_grid = np.array(flat_map).reshape(h, w)

# # destination = (12, 8)
IMPASSABLE = {0x15, 0x16, 0x24, 0x25, 0x1E, 0x1D, 0x0E, 0x0F}  # walls, water, etc.
# PASSABLE = {0x11, 0x06}

from heapq import heappop, heappush

def astar(grid, start, goal):
    h, w = grid.shape
    open_set = [(0, start)]
    came_from = {}
    g = {start: 0}

    def heuristic(a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])  # Manhattan distance

    while open_set:
        _, current = heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = current[0]+dx, current[1]+dy
            if 0 <= nx < h and 0 <= ny < w and grid[nx, ny] not in IMPASSABLE:
                tentative_g = g[current] + 1
                if (nx, ny) not in g or tentative_g < g[(nx, ny)]:
                    g[(nx, ny)] = tentative_g
                    f = tentative_g + heuristic((nx, ny), goal)
                    heappush(open_set, (f, (nx, ny)))
                    came_from[(nx, ny)] = current
    return []

# from pyboy.utils import WindowEvent

def move_toward_path(pyboy, path):
    for (x, y), (nx, ny) in zip(path, path[1:]):
        if nx > x: 
            pyboy.button_press("right")
            print("RIGHT")
            for _ in range(2):
                pyboy.tick()
            pyboy.button_release("right")
        elif nx < x: 
            pyboy.button_press("left")
            print("LEFT")
            for _ in range(2):
                pyboy.tick()
            pyboy.button_release("left")
        elif ny < y: 
            pyboy.button_press("down")
            print("DOWN")
            for _ in range(2):
                pyboy.tick()
            pyboy.button_release("down")
        elif ny > y: 
            pyboy.button_press("up")
            print("UP")
            for _ in range(2):
                pyboy.tick()
            pyboy.button_release("up")
        
        for _ in range(60):  # wait a few frames for movement
            pyboy.tick()

        player_x, player_y, map_id = get_player_position(pyboy.memory)
        print(f"Current map={map_id}, player=(Height: {player_y}, Width: {player_x})")

def read_visible_tiles(pyboy):
    """
    Reads the current on-screen 20x18 tile buffer (0xC3A0–0xC507)
    and returns a 2D list of tile IDs.
    """

    mem = pyboy.memory
    x, y, map_id = get_player_position(mem)
    # x = mem[get_mem_pointer("system_addresses", "player_x")]
    # y = mem[get_mem_pointer("system_addresses", "player_y")]
    # x = mem[0xC106]
    # y = mem[0xC104]
    # x = mem[0xC105]
    # y = mem[0xC103]
    # x = mem[0xC205]
    # y = mem[0xC204]
    base_addr = 0xC3A0
    width, height = 20, 18
    total_tiles = width * height  # 360

    tiles = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append(mem[base_addr + y * width + x])
        tiles.append(row)
    
    # print(f"X: {x}, Y: {y}")

    return tiles

def clean_tiles(tiles, pyboy):
    player_x, player_y, map_id = get_player_position(pyboy.memory)
    # cleaned_tiles = tiles
    cleaned_tiles = []
    for row in tiles:
        cleaned_row = []
        for t in row:
            # print(type(t))
            if f"{t:02X}" != '0F': cleaned_row.append(t) #remove black borders from map
        if len(cleaned_row)>0: cleaned_tiles.append(cleaned_row)

    #Add player location on map
    # rev_cleaned_tiles = cleaned_tiles[::-1] 
    # # rev_cleaned_tiles[player_y][player_x] = '@'
    # rev_cleaned_tiles[player_x][player_y] = '@'
    # cleaned_tiles = rev_cleaned_tiles[::-1]
    # print(len(tiles))
    # print(len(cleaned_tiles))
    # print(player_y)
    print(f"HEIGHT:{len(cleaned_tiles)}, WIDTH:{len(cleaned_tiles[0])}")
    # print(f"HEIGHT:{len(tiles)}, WIDTH:{len(tiles[0])}")
    # cleaned_tiles[len(cleaned_tiles)-(player_y + 1)][player_x] = '@'
    if player_y > len(cleaned_tiles):
        cleaned_tiles[len(cleaned_tiles)-1][player_x] = -1
    elif player_x > len(cleaned_tiles[0]):
        cleaned_tiles[player_y][len(cleaned_tiles[0])-1] = -1
    elif player_y > len(cleaned_tiles) and player_x > len(cleaned_tiles[0]):
        cleaned_tiles[len(cleaned_tiles)-1][len(cleaned_tiles[0])-1] = -1
    else:
        cleaned_tiles[player_y][player_x] = -1

    for row in cleaned_tiles:
        print(' '.join(f"{t:02X}" for t in row)) # if f"{t:02X}" != '0F'

    # print(f"HEIGHT:{len(cleaned_tiles)}, WIDTH:{len(cleaned_tiles[0])}")
    return cleaned_tiles

def main():
    pyboy = PyBoy(ROM_PATH, window="SDL2")  # set to "SDL2" to see screen
    # Load Save State
    LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_left.sav'
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)
    # Wait a few frames for stability
    for _ in range(60):
        pyboy.tick()
    mb = pyboy.memory
    # start = (mb[0xD362], mb[0xD361])  # (y, x)
    # goal = (5, 11)
    goal = (5, 5) #(x, y) (0,0) is bottom left, y-inverted
    
    # (height, width)


    # grid, w, h = np.array(read_map(mb)[0]).reshape(h, w), w, h
    # flat_map, w, h = read_map(mb)
    # grid = np.array(flat_map).reshape(h, w)
    # path = astar(grid, start, goal)

    player_x, player_y, map_id = get_player_position(mb)
    tiles = read_visible_tiles(pyboy)
    # Print numeric grid of tile IDs
    cleaned_tiles = clean_tiles(tiles, pyboy)
    print(f"Current map={map_id}, player=(Height: {player_y}, Width: {player_x})")
    grid = build_walkable_grid(mb, cleaned_tiles)
    print(grid)
    start = (player_x, player_y)
    # goal = exit_tile
    # path = bfs_path(grid, start, goal)
    path = astar(grid, start, goal)

    
    

    if path:
        move_toward_path(pyboy, path)
        #TOP LEFT OF MAP is (0,0)
        mb = pyboy.memory
        player_x, player_y, map_id = get_player_position(mb)
        print(f"Current map={map_id}, player=(Height: {player_y}, Width: {player_x})")
        tiles = read_visible_tiles(pyboy)
        # Print numeric grid of tile IDs
        cleaned_tiles = clean_tiles(tiles, pyboy)
    else:
        print("No path found.")
    pyboy.stop()

if __name__ == "__main__":
    main()
