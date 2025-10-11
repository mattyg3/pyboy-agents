# planner.py
# Simple planner: very small rule-based planner that issues high-level commands from state.

class SimplePlanner:
    def __init__(self):
        self.goal = "explore"

    def plan(self, state):
        # If in text or menu, press A
        if state.get("has_text"):
            return {"type": "PRESS_A"}

        if state.get("scene") == "battle":
            return {"type": "PRESS_A"}

        # Otherwise, move up
        return {"type": "GO_UP"}

