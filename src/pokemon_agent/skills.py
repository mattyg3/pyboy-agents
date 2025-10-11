# skills.py
# Convert high-level plans into PyBoy input sequences (macros). Very small macro language included.

from pyboy.utils import WindowEvent

class SkillExecutor:
    def __init__(self, pyboy):
        self.pyboy = pyboy

    def _press(self, button_event, hold_frames=1):
        # Use button_press and button_release manually for fine control
        self.pyboy.button_press(button_event)
        for _ in range(hold_frames):
            self.pyboy.tick()
        self.pyboy.button_release(button_event)
        # Allow at least one more tick so the command registers
        self.pyboy.tick()

    def execute(self, plan, state):
        t = plan.get("type",None)
        if t is None or t == "NOOP":
            return "noop"

        if t == "PRESS_A":
            self._press("a", hold_frames=2)
            return "pressed_a"
        
        if t == "PRESS_B":
            self._press("b", hold_frames=2)
            return "pressed_b"

        if t == "GO_UP":
            self._press("up", hold_frames=2)
            return "moved_up"
        
        if t == "GO_DOWN":
            self._press("down", hold_frames=2)
            return "moved_down"
        
        if t == "GO_LEFT":
            self._press("left", hold_frames=2)
            return "moved_left"

        if t == "GO_RIGHT":
            self._press("right", hold_frames=2)
            return "moved_right"

        if t == "OPEN_MENU":
            self._press("start", hold_frames=2)
            return "menu_opened"

        if t == "RUN_MACRO":
            macro = plan.get("macro", [])
            for btn_event, frames in macro:
                self._press(btn_event, hold_frames=frames)
            return "macro_done"

        return "unknown"
