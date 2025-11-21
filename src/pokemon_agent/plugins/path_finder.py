from pokemon_agent.utils.map_collision_read import *
# from src.pokemon_agent.utils.map_render_from_rom import render_map_png
from pyboy import PyBoy
# from pathlib import Path
import heapq
from pokemon_agent.plugins.skills import SkillExecutor
from pokemon_agent.utils.utility_funcs import find_map_by_id
from pokemon_agent.plugins.perception import BattleFlag, DialogFlag

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

def astar_2wide(grid, start, goal):
    """
    A* pathfinding where start and goal can be single tiles, 
    but the path must have width-2 clearance everywhere else.

    The search operates on positions representing the *top-left* of a 2×2 footprint.
    """

    h = len(grid)
    w = len(grid[0])

    def has_width2_clearance(x, y):
        if x < 0 or y < 0 or x + 1 >= w or y + 1 >= h:
            return False
        return (
            grid[y][x] and grid[y][x+1] and
            grid[y+1][x] and grid[y+1][x+1]
        )

    # ------------------------------------------------------------------
    # Find all 2×2 legal locations that include a given 1×1 point
    # (for start/goal mapping)
    # ------------------------------------------------------------------
    def all_valid_footprints_touching(px, py):
        candidates = [
            (px, py),
            (px - 1, py),
            (px, py - 1),
            (px - 1, py - 1),
        ]
        return [(x, y) for (x, y) in candidates if has_width2_clearance(x, y)]

    # If start has no valid 2×2 footprint, we still allow its exact 1×1 position
    # as the start node, but the first move must go to a valid 2×2 footprint.
    start_nodes = all_valid_footprints_touching(*start)
    goal_nodes = all_valid_footprints_touching(*goal)

    # If goal is unreachable directly, allow "adjacent to goal".
    # This means any 2×2 footprint whose 4 tiles include a tile adjacent to goal.
    if not goal_nodes:
        gx, gy = goal
        adj = [(gx+1,gy), (gx-1,gy), (gx,gy+1), (gx,gy-1)]
        for ax, ay in adj:
            for x, y in all_valid_footprints_touching(ax, ay):
                goal_nodes.append((x, y))

    # If absolutely no goal nodes exist, impossible
    if not goal_nodes:
        return None

    import heapq

    # ------------------------------------------------------------------
    # A* search on 2×2 footprints
    # ------------------------------------------------------------------
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = []
    g_score = {}
    came_from = {}

    # If start is already in a width-2 footprint, treat that as start.
    # Otherwise search starts at the raw 1×1 tile, which has no clearance.
    if start_nodes:
        for sn in start_nodes:
            heapq.heappush(open_set, (0, sn))
            g_score[sn] = 0
    else:
        # Use the raw start tile; it has no neighbors except valid footprints.
        heapq.heappush(open_set, (0, start))
        g_score[start] = 0

    goal_nodes = set(goal_nodes)

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in goal_nodes:
            # Reconstruct path of 2×2 footprints
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        x, y = current

        # Move in 4 directions, but only into width-2 footprints
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x + dx, y + dy

            # If current was the raw 1×1 starting tile, neighbors are the valid footprints
            if current == start and not start_nodes:
                if has_width2_clearance(nx, ny):
                    tentative = g_score[current] + 1
                    if tentative < g_score.get((nx, ny), float('inf')):
                        g_score[(nx, ny)] = tentative
                        came_from[(nx, ny)] = current
                        f = tentative + min(heuristic((nx, ny), g) for g in goal_nodes)
                        heapq.heappush(open_set, (f, (nx, ny)))
                continue

            # Normal case: moving from a 2×2 footprint to another
            if has_width2_clearance(nx, ny):
                neighbor = (nx, ny)
                tentative = g_score[current] + 1
                if tentative < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    f = tentative + min(heuristic(neighbor, g) for g in goal_nodes)
                    heapq.heappush(open_set, (f, neighbor))

    return None

def move_toward_path(pyboy, path): #top left is (0,0)
    map_id, px, py, direction = get_player_position(pyboy)
    # print(f"Current map={map_id}, player=(Height: {py}, Width: {px}, Direction: {direction})")
    nx, ny = path
    skills = SkillExecutor(pyboy)
    if nx > px: 
        skills.execute({"type": "GO_RIGHT"})
        # print("RIGHT")
        return {"type": "GO_RIGHT"}
        
    elif nx < px: 
        skills.execute({"type": "GO_LEFT"})
        # print("LEFT")
        return {"type": "GO_LEFT"}
    elif ny > py: 
        skills.execute({"type": "GO_DOWN"})
        # print("DOWN")
        return {"type": "GO_DOWN"}
    elif ny < py: 
        skills.execute({"type": "GO_UP"})
        # print("UP")
        return {"type": "GO_UP"}
    
    for _ in range(10):  # wait a few frames for movement
        pyboy.tick()

        
def path_finder(pyboy, goal, astar_2=False):
    # skills = SkillExecutor(pyboy)
    walk_matrix, map_width, map_height, warp_tiles = read_map(pyboy)
    # --- Get player position ---
    map_id, px, py, direction = get_player_position(pyboy)
    battle_flag = BattleFlag(pyboy)
    dialog_flag = DialogFlag(pyboy)
    try:
        print(f"Player at map {map_id}, X={px}, Y={py}, Looking={direction}") #(0: down, 4: up, 8: left, 12: right)
        walk_matrix[py][px] = 'P' #player location
        walk_matrix[goal[1]][goal[0]] = 'G' #goal location
    except:
        pass
    print("\nWalkable tile matrix ('-' = walkable, '#' = blocked):")
    print_tile_walk_matrix(walk_matrix)


    # --- Load Map Values ---
    width = find_map_by_id(MAP_HEADERS, map_id).get("map_width")
    height = find_map_by_id(MAP_HEADERS, map_id).get("map_height")
    map_env = find_map_by_id(MAP_HEADERS, map_id).get("environment")
    map_filename = find_map_by_id(MAP_HEADERS, map_id).get("file")

    at_goal=False
    repeat_cnt=0 #if stuck trying to get to impossible tile
    prev_px=0
    prev_py=0
    prev_move=None
    max_steps=250
    step_count=0
    try_next_xy=False
    while not at_goal:
        if step_count > max_steps:
            at_goal=True
            try_next_xy=True
            continue
            # break
        step_count+=1
        new_map_id, px, py, direction = get_player_position(pyboy)
        if prev_px==px and prev_py==py:
            repeat_cnt+=1
            # print(f"px: {px}, py:{py}, prev_px:{prev_px}, prev_py:{prev_py}")
            # print(f"REPEAT COUNTER: {repeat_cnt}")
            if repeat_cnt > 10:
                at_goal=True
                continue
                # break
        else:
            repeat_cnt=0

        if new_map_id != map_id:
            at_goal=True
            continue
        if goal in [(px + dx, py + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]:
            # last_path = astar_next_step(walk_matrix, (px, py), goal)
            
            try:
                if astar_2:
                    a_path = astar_2wide(walk_matrix, (px, py), goal)
                else:
                    a_path = astar(walk_matrix, (px, py), goal)
                last_path = a_path[1] # get next move
            except:
                last_path = goal
            if last_path == (px, py):
                at_goal=True
                continue
            else:
                battle_info = battle_flag.read_memory_state()
                # print(f"BATTLE_TYPE: {battle_info["battle_type"]}")
                dialog_info = dialog_flag.read_memory_state()
                if battle_info["battle_type"] != 0: #break out of path_finding to battle
                    at_goal=True
                    continue
                    # break
                elif dialog_info: #break out of path_finding for dialog
                    at_goal=True
                    continue
                    # break
                else:
                    prev_px=px
                    prev_py=py
                    prev_move = move_toward_path(pyboy, last_path)
                    

        else:
            
            try:
                # path = astar_next_step(walk_matrix, (px, py), goal)
                if astar_2:
                    a_path = astar_2wide(walk_matrix, (px, py), goal)
                else:
                    a_path = astar(walk_matrix, (px, py), goal)
                path = a_path[1] # get next move
            except:
                path = prev_move

            if path:
                battle_info = battle_flag.read_memory_state()
                # print(f"BATTLE_TYPE: {battle_info["battle_type"]}")
                if battle_info["battle_type"] != 0:  #break out of path_finding to battle
                    at_goal=True
                    continue
                    # break
                else:
                    prev_px=px
                    prev_py=py  
                    prev_move = move_toward_path(pyboy, path)
                #TOP LEFT OF MAP is (0,0)
                # print(f"Current map={new_map_id}, Map name={map_filename.replace(".asm","")}, map=(Width_blk: {width}, Height_blk: {height}) ,player=(Width: {px}, Height: {py})")
            else:
                print("No path found.")
                break
    return {"prev_move":prev_move, "try_next_xy":try_next_xy}



with open('src/pokemon_agent/maps/map_headers.json', 'r') as f:
    MAP_HEADERS = json.load(f)

with open('src/pokemon_agent/maps/collision_tiles.json', 'r') as f:
    COLLISION = json.load(f)


    


# ------ MAIN ------
def main():
    # ------ Config ------
    ROM_PATH = 'ROMS/pokemon_red.gb'
    # LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'
    LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight.sav'
    pyboy = PyBoy(ROM_PATH, window="SDL2")
    pyboy.tick()  # initialize emulation
    # pyboy.set_emulation_speed(0)
    # Load Save State
    with open(LOAD_STATE_PATH, "rb") as f:
            pyboy.load_state(f)

    while pyboy.tick(): #100
        path_finder(pyboy, goal=(10,23))
        pyboy.stop()

    # pyboy.stop()
    
if __name__ == "__main__":
    main()