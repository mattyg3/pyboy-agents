from map_collision_read import *
from pyboy import PyBoy
from pathlib import Path
import heapq

# ------ Config ------
ROM_PATH = 'ROMS/pokemon_red.gb'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'
# LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'

with open('src/pokemon_agent/utils/ref_data/maps/map_headers.json', 'r') as f:
        MAP_HEADERS = json.load(f)

with open('src/pokemon_agent/utils/ref_data/maps/collision_tiles.json', 'r') as f:
        COLLISION = json.load(f)
    
def find_map_by_id(map_list, map_id):
    for m in map_list:
        if m["map_id"] == map_id:
            return m
    return None 


# ------ Pathfinding Algo ------
# def astar(grid, start, goal):
#     """
#     A* pathfinding on a boolean grid.
#     grid[y][x] = True if walkable, False if blocked
#     start = (x, y)
#     goal = (x, y)
#     Returns a list of coordinates from start to goal (inclusive), or None if no path.
#     """
#     h = len(grid)
#     w = len(grid[0])

#     def heuristic(a, b):
#         # Manhattan distance (since movement is 4-directional)
#         return abs(a[0] - b[0]) + abs(a[1] - b[1])

#     open_set = []
#     heapq.heappush(open_set, (0, start))
#     came_from = {}
#     g_score = {start: 0}

#     while open_set:
#         _, current = heapq.heappop(open_set)

#         if current == goal:
#             # reconstruct path
#             path = [current]
#             while current in came_from:
#                 current = came_from[current]
#                 path.append(current)
#             path.reverse()
#             return path

#         x, y = current
#         for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
#             nx, ny = x + dx, y + dy
#             if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:  # walkable
#                 tentative_g = g_score[current] + 1
#                 neighbor = (nx, ny)
#                 if tentative_g < g_score.get(neighbor, float('inf')):
#                     came_from[neighbor] = current
#                     g_score[neighbor] = tentative_g
#                     f_score = tentative_g + heuristic(neighbor, goal)
#                     heapq.heappush(open_set, (f_score, neighbor))
#     return None  # no path found 

def astar_next_step(grid, start, goal):
    """
    A* pathfinding that returns only the next step toward the goal, 
    stopping early once the next move is known.
    
    grid[y][x] = True if walkable, False if blocked
    start = (x, y)
    goal = (x, y)
    Returns (x, y) of the next step, or None if no path exists.
    """
    if start == goal:
        return start

    h = len(grid)
    w = len(grid[0])

    def heuristic(a, b):
        # Manhattan distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        # If we reached the goal, reconstruct just the first move
        if current == goal:
            # Backtrack once to find the step after start
            prev = current
            while came_from.get(prev) and came_from[prev] != start:
                prev = came_from[prev]
            return prev if came_from.get(prev) == start else None

        x, y = current
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
                neighbor = (nx, ny)
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))

                    # Early stop: if neighbor is goal, return it immediately if it's next to start
                    if neighbor == goal:
                        if current == start:
                            return neighbor
                        # otherwise backtrack one step
                        prev = current
                        while came_from.get(prev) and came_from[prev] != start:
                            prev = came_from[prev]
                        return prev if came_from.get(prev) == start else None

    return None  # No path found


def move_toward_path(pyboy, path): #top left is (0,0)

    # map_id, px, py, direction = get_player_position(pyboy)
    # print(f"Current map={map_id}, player=(Height: {py}, Width: {px}, Direction: {direction})")
    # if goal == (px,py):
    #     print(f"Goal Reached! {goal}")
    #     pyboy.stop()

    # while goal not in [path, (path[0]+1, path[1]), (path[0], path[1]+1), (path[0]+1, path[1]+1), (path[0]-1, path[1]), (path[0], path[1]-1), (path[0]-1, path[1]-1)]
    # while goal not in [[(path[0] + dx, path[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]]: #outside this func??
    # for (x, y), (nx, ny) in zip(path, path[1:]):
    map_id, px, py, direction = get_player_position(pyboy)
    print(f"Current map={map_id}, player=(Height: {py}, Width: {px}, Direction: {direction})")
    nx, ny = path
    if nx > px: 
        pyboy.button_press("right")
        print("RIGHT")
        for _ in range(2):
            pyboy.tick()
        pyboy.button_release("right")
    elif nx < px: 
        pyboy.button_press("left")
        print("LEFT")
        for _ in range(2):
            pyboy.tick()
        pyboy.button_release("left")
    elif ny > py: 
        pyboy.button_press("down")
        print("DOWN")
        for _ in range(2):
            pyboy.tick()
        pyboy.button_release("down")
    elif ny < py: 
        pyboy.button_press("up")
        print("UP")
        for _ in range(2):
            pyboy.tick()
        pyboy.button_release("up")
    
    for _ in range(60):  # wait a few frames for movement
        pyboy.tick()

    # break #only 1 iteration

        
        



# ------ MAIN ------
def main():
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    pyboy.tick()  # initialize emulation
    # pyboy.set_emulation_speed(0)
    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    while pyboy.tick(): #100

        # --- Get player position ---
        map_id, px, py, direction = get_player_position(pyboy)
        print(f"Player at map {map_id}, X={px}, Y={py}, Looking={direction}") #(0: down, 4: up, 8: left, 12: right)

        # --- Load Map Values ---
        width = find_map_by_id(MAP_HEADERS, map_id).get("map_width")
        height = find_map_by_id(MAP_HEADERS, map_id).get("map_height")
        map_env = find_map_by_id(MAP_HEADERS, map_id).get("environment")
        map_filename = find_map_by_id(MAP_HEADERS, map_id).get("file")
        map_path = Path("src/pokemon_agent/utils/ref_data/maps/map_files") / f"{map_filename.replace(".asm",".blk")}" #/PalletTown.blk
        blockset_path = Path("src/pokemon_agent/utils/ref_data/maps/blocksets") / f"{map_env.lower()}.bst" #/overworld.bst
        print(f'WIDTH: {width}, HEIGHT: {height}, ENVR: {map_env}')

        # --- Load map graphics ---
        # tiles = load_tileset_2bpp(tileset_path)
        blocks = load_blockset(blockset_path)
        map_blocks = load_map_blk(map_path, width, height)

    

        # --- Compute tile-level walkability matrix ---
        WALKABLE_TILE_IDS = COLLISION.get(f"{map_env.replace("_","").upper()}_COLL")
        walk_matrix = generate_walkability_tile_matrix(blocks, map_blocks, WALKABLE_TILE_IDS)
        # start = (px, py)
        goal = (21, 0)  # change this to your desired target tile (x,y)
        at_goal=False
        while not at_goal:
        # while at_goal==False:
            map_id, px, py, direction = get_player_position(pyboy)
            # print([(px + dx, py + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)])
            if goal in [(px + dx, py + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]:
                at_goal=True
            else:
                path = astar_next_step(walk_matrix, (px, py), goal)

                if path:
                    move_toward_path(pyboy, path)
                    #TOP LEFT OF MAP is (0,0)
                    print(f"Current map={map_id}, Map name={map_filename.replace(".asm","")}, map=(Height: {height}, Width: {width}) ,player=(Height: {py}, Width: {px})")
                else:
                    print("No path found.")
                    pyboy.stop()

        

        # --- Print to console ---
        walk_matrix[py][px] = 'P' #player location
        # walk_matrix[goal[1], goal[0]] = 'G'
        print("\nWalkable tile matrix ('.' = walkable, '#' = blocked):")
        print_tile_walk_matrix(walk_matrix)



    pyboy.stop()
    
    
    # # --- Print to console ---
    # walk_matrix[py][px] = 'P' #player location
    # # walk_matrix[goal[1], goal[0]] = 'G'
    # print("\nWalkable tile matrix ('.' = walkable, '#' = blocked):")
    # print_tile_walk_matrix(walk_matrix)
    # # print(path)
    # if path:
    #     move_toward_path(pyboy, path)
    #     #TOP LEFT OF MAP is (0,0)
    #     mb = pyboy.memory
    #     player_x, player_y, map_id, tileset_id = get_player_position(mb)
    #     print(f"Current map={map_id}, Tileset={tileset_id}, player=(Height: {player_y}, Width: {player_x})")
    #     tiles = read_visible_tiles(pyboy)
    #     # Print numeric grid of tile IDs
    #     cleaned_tiles = clean_tiles(tiles, pyboy)
    # else:
    #     print("No path found.")
    # # move_toward_path(pyboy, path)


if __name__ == "__main__":
    main()