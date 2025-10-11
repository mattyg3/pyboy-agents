# Macro Action Creation
class create_macro:
    def __init__(self):
        self.ordered_steps = []

    def add_step(self, button_action, frame_len):
        self.ordered_steps.append({'action':button_action, 'frame_length':frame_len})

    def run_macro(self, frame, init_frame=0):
        current_frame = init_frame
        #compile steps
        for i, step in enumerate(self.ordered_steps):
            self.ordered_steps[i] = {'action':step.get('action'), 'frame_length':step.get('frame_length'), 'frame_start':current_frame}
            current_frame += step.get('frame_length')
        #run compiled steps
        for step in self.ordered_steps:
            if frame >= step.get("frame_start") and frame < (step.get("frame_start") + step.get("frame_length")):
                return step.get("action")
            else:
                pass

