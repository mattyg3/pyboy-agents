from map_collision_read import *
from pyboy import PyBoy
from pathlib import Path
import heapq

# ------ Config ------
ROM_PATH = 'ROMS/pokemon_red.gb'
blockset_path = Path("src/pokemon_agent/utils/ref_data/maps/blocksets/overworld.bst")
map_path = Path("src/pokemon_agent/utils/ref_data/maps/map_files/PalletTown.blk")
width = 10
height = 9
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'

# ------ Pathfinding Algo ------
def astar(grid, start, goal):
    """
    A* pathfinding on a boolean grid.
    grid[y][x] = True if walkable, False if blocked
    start = (x, y)
    goal = (x, y)
    Returns a list of coordinates from start to goal (inclusive), or None if no path.
    """
    h = len(grid)
    w = len(grid[0])

    def heuristic(a, b):
        # Manhattan distance (since movement is 4-directional)
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            # reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        x, y = current
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:  # walkable
                tentative_g = g_score[current] + 1
                neighbor = (nx, ny)
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))

    return None  # no path found

def move_toward_path(pyboy, path): #top left is (0,0)
    for (x, y), (nx, ny) in zip(path, path[1:]):
        if nx > x: 
            # pyboy.button_press("right")
            print("RIGHT")
            # for _ in range(2):
            #     pyboy.tick()
            # pyboy.button_release("right")
        elif nx < x: 
            # pyboy.button_press("left")
            print("LEFT")
            # for _ in range(2):
            #     pyboy.tick()
            # pyboy.button_release("left")
        elif ny > y: 
            # pyboy.button_press("down")
            print("DOWN")
            # for _ in range(2):
            #     pyboy.tick()
            # pyboy.button_release("down")
        elif ny < y: 
            # pyboy.button_press("up")
            print("UP")
            # for _ in range(2):
            #     pyboy.tick()
            # pyboy.button_release("up")
        
        # for _ in range(60):  # wait a few frames for movement
        #     pyboy.tick()

        # player_x, player_y, map_id, tileset_id = get_player_position(pyboy.memory)
        # print(f"Current map={map_id}, Tileset={tileset_id}, player=(Height: {player_y}, Width: {player_x})")



# ------ MAIN ------
def main():
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
        # tiles = load_tileset_2bpp(tileset_path)
        blocks = load_blockset(blockset_path)
        map_blocks = load_map_blk(map_path, width, height)

    

        # --- Compute tile-level walkability matrix ---
        walk_matrix = generate_walkability_tile_matrix(blocks, map_blocks, WALKABLE_TILE_IDS)
        start = (px, py)
        goal = (22, 0)  # change this to your desired target tile (x,y)
        path = astar(walk_matrix, start, goal)



    pyboy.stop()
    walk_matrix[py][px] = 'P' #player location
    # walk_matrix[goal[1], goal[0]] = 'G'
    # --- Print to console ---
    print("\nWalkable tile matrix ('.' = walkable, '#' = blocked):")
    print_tile_walk_matrix(walk_matrix)
    print(path)
    move_toward_path(pyboy, path)


if __name__ == "__main__":
    main()