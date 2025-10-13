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



    # def print_memory_region(self, pyboy, base_pointer, radius=10):
    #     """
    #     Print memory values around a given pointer.
        
    #     Args:
    #         pyboy: PyBoy instance
    #         base_pointer: int, memory address to center on
    #         radius: int, number of bytes before and after to print
    #     """
    #     start = max(base_pointer - radius, 0)
    #     end = base_pointer + radius + 1
    #     mem = pyboy.memory
    #     print(f"Memory region around 0x{base_pointer:04X} (±{radius} bytes):")
    #     for addr in range(start, end):
    #         val = mem[addr]
    #         print(f"0x{addr:04X}: 0x{val:02X}")
