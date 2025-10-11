# planner.py
# Simple planner: get through opening menu to get to a specific starting pokemon
import random
from utils.saved_macros import game_start_macro


class SimplePlanner:
    def __init__(self):
        self.goal = "explore"

    def gamestart_plan(self, frame): #, state
        action = game_start_macro.run_macro(frame=frame, init_frame=0)
        if action is None:
            return {"type": None}
        else:
            return action
    
    def plan(self, state, frame): #
        action = random.choice([
            {"type": "PRESS_A"},
            {"type": "PRESS_B"},
            {"type": "GO_UP"},
            {"type": "GO_DOWN"},
            {"type": "GO_LEFT"},
            {"type": "GO_RIGHT"},
            # {"type": "OPEN_MENU"},
        ])
        return action
