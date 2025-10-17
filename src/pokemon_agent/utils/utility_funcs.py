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



# Type Effectivness Multiplier
from functools import reduce
from operator import mul
import json

with open("src/pokemon_agent/utils/ref_data/type_chart.json") as f:
    TYPE_CHART = json.load(f)

def type_multiplier(attacking_type, defending_types, attacker_types=None):
    """
    attacking_type : str
        Type of the move being used (e.g. "Fire")
    defending_types : list[str]
        Defending Pokémon's types (e.g. ["Water", "Flying"])
    attacker_types : list[str] | None
        Attacker's Pokémon types (e.g. ["Fire", "Flying"])
    """

    # Base effectiveness vs all defender types
    base_mult = reduce(
        mul, [TYPE_CHART.get(attacking_type, {}).get(defn, 1.0) for defn in defending_types], 1.0
    )

    # Apply STAB if move type matches attacker type
    stab = 1.5 if attacker_types and attacking_type in attacker_types else 1.0

    return base_mult * stab


# # Example usage:
# if __name__ == "__main__":
#     # Charizard (Fire/Flying) uses Fire move vs Water opponent
#     result = type_multiplier("Fire", ["Water"], ["Fire", "Flying"])
#     print(f"Effectiveness: {result}x")  # 0.75x (0.5 * 1.5)


# Clean noisy text
class TextCleaner():
    def __new__(cls, ocr_outputs):
        cleaned = cls.collapse_ocr_sequence(ocr_outputs)
        stripped = cls.extract_final_texts(cleaned)
        final = [cls.post_process(msg) for msg in stripped]
        return ' '.join(final)
        # return stripped
    
    def __init__(self):
        pass
        


    def collapse_ocr_sequence(ocr_outputs, min_len=3):
        """
        Reduce noisy OCR frame outputs to meaningful full lines.
        - Removes duplicates and partial overlaps.
        - Keeps only distinct final states of each message.
        """
        cleaned = []
        last = ""

        for text in ocr_outputs:
            # Normalize newlines and spaces
            t = text.strip().replace("\r", "")
            # Ignore if it's just a prefix of the previous
            if t.startswith(last) and len(t) <= len(last):
                continue
            # Ignore if it's too short
            if len(t) < min_len:
                continue
            # Only append if different enough
            if t != last:
                cleaned.append(t)
                last = t
        return cleaned

    def extract_final_texts(cleaned):
        """
        Split sequence into message chunks and take final text of each.
        A reset (shorter text) signals new message.
        """
        finals = []
        current_chunk = []
        last_len = 0

        for text in cleaned:
            if len(text) >= last_len:
                current_chunk.append(text)
            else:
                if current_chunk:
                    finals.append(current_chunk[-1])
                current_chunk = [text]
            last_len = len(text)

        if current_chunk:
            finals.append(current_chunk[-1])

        return finals
    
    def post_process(text):
        """Fix common OCR quirks and improve readability."""
        text = text.replace("\n", " ").replace("  ", " ")
        return text.strip()










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
