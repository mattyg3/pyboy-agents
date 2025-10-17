import cv2
import numpy as np
import os
from pathlib import Path
import pickle
# --- CONFIG ---
TEMPLATE_CHAR_ORDER = ["ABCDEFGHIJKLMNOP","QRSTUVWXYZ", 'abcdefghijklmnop', 'qrstuvwxyzé',"0123456789","?!."]
TEMPLATE_WIDTH = 8   # width of one character in pixels
TEMPLATE_HEIGHT = 8  # height of one character in pixels
folder_path='src/pokemon_agent/utils/ref_data/fonts/'
image_paths = [f"{folder_path}font_row1.png", f"{folder_path}font_row2.png", f"{folder_path}font_lower_row1.png", f"{folder_path}font_lower_row2.png", f"{folder_path}font_numbers.png", f"{folder_path}font_punc.png",]

# def build_templates_from_images(image_paths, char_order_list=TEMPLATE_CHAR_ORDER,
#                                 width=TEMPLATE_WIDTH, height=TEMPLATE_HEIGHT):
#     """
#     Build template dictionary from multiple font sheet images.
#     Each image should contain the characters in 'char_order', evenly spaced horizontally.
#     """
#     templates = {}

#     for j, path in enumerate(image_paths):
#         char_order=char_order_list[j]
#         img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
#         if img is None:
#             print(f"[WARN] Could not read {path}")
#             continue

#         img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
#         chars_per_row = img.shape[1] // width

#         for i, c in enumerate(char_order[:chars_per_row]):
#             x1, y1 = i * width, 0
#             x2, y2 = x1 + width, height
#             glyph = img[y1:y2, x1:x2]
#             if glyph.size > 0:
#                 templates[c] = glyph

#         print(f"[OK] Loaded {len(templates)} templates from {path}")

#     print(f"[DONE] Total templates loaded: {len(templates)}")
#     return templates

# templates = build_templates_from_images(image_paths) #



def save_templates_pkl(templates, filename="src/pokemon_agent/utils/ref_data/font_templates.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(templates, f)
    print(f"✅ Saved {len(templates)} templates to {filename}")

def load_templates_pkl(filename="src/pokemon_agent/utils/ref_data/font_templates.pkl"):
    with open(filename, "rb") as f:
        templates = pickle.load(f)
    print(f"✅ Loaded {len(templates)} templates from {filename}")
    return templates

# save_templates_pkl(templates)
templates = load_templates_pkl()

# print("Template sizes:", {c: t.shape for c, t in templates.items()})

# # Show a single character template
# import cv2
# cv2.imshow('Template A', templates['e'])
# cv2.waitKey(0)
# cv2.destroyAllWindows()






from utils.utility_funcs import TextCleaner

def match_text_region(region, templates, threshold=0.99, space_threshold=1, line_threshold=10):
    """
    Match text from a given region using template matching.
    - region: grayscale image of the text area
    - templates: dict of character -> glyph
    - threshold: match quality threshold
    - space_threshold: horizontal spacing multiplier for spaces
    - line_threshold: vertical distance threshold for separating lines
    """
    # Binarize and invert
    region = cv2.threshold(region, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    matches = []
    for ch, tmpl in templates.items():
        try:
            res = cv2.matchTemplate(region, tmpl, cv2.TM_CCOEFF_NORMED)
        except cv2.error:
            print("Template size:", tmpl.shape)
            print("Image size:", region.shape)
            continue

        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):  # (x, y)
            matches.append((pt[0], pt[1], ch, res[pt[1], pt[0]]))

    if not matches:
        return ""

    # Sort primarily by Y (line), then X (within line)
    matches.sort(key=lambda x: (x[1], x[0]))

    # Group into lines based on Y distance
    lines = []
    current_line = [matches[0]]
    for i in range(1, len(matches)):
        if abs(matches[i][1] - current_line[-1][1]) < line_threshold:
            current_line.append(matches[i])
        else:
            lines.append(current_line)
            current_line = [matches[i]]
    lines.append(current_line)

    # Sort each line by X position
    lines = [sorted(line, key=lambda x: x[0]) for line in lines]

    # Assemble text lines
    text_lines = []
    for line in lines:
        text = ""
        last_x = None
        for x, y, ch, score in line:
            tmpl_width = templates[ch].shape[1]
            if last_x is not None and x - last_x > tmpl_width * space_threshold:
                text += " "
            text += ch
            last_x = x
        text_lines.append(text.strip())

    return "\n".join(text_lines)



# from PIL import Image
def extract_regions(frame, regions):
    """
    Given a frame (grayscale or color) and a list of regions (x, y, w, h),
    extract them as subimages.
    """
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    
    # 1) sharpen slightly (optional)
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]], dtype=np.float32)
    gray = cv2.filter2D(gray, -1, kernel)


    extracted = []
    for (y1, y2, x1, x2) in regions:
        # extracted.append(frame[y:y+h, x:x+w])
        extracted.append(gray[y1:y2, x1:x2])
        # cv2.imwrite('dev_files/gray.png', gray[y1:y2, x1:x2])
    return extracted


def ocr_from_regions(frame, regions, templates):
    """
    Perform OCR over multiple regions using template matching.
    """
    results = []
    crops = extract_regions(frame, regions)
    for crop in crops:
        text = match_text_region(crop, templates)
        results.append(text)
    return results


if __name__ == "__main__":
    # # Example usage
    # folder_path='src/pokemon_agent/utils/ref_data/fonts/'
    # templates = build_templates_from_images([f"{folder_path}font_row1.png", f"{folder_path}font_row2.png", f"{folder_path}font_numbers.png", f"{folder_path}font_punc.png",])

    # Suppose these are menu text areas
    regions = [
        # (16, 32, 120, 16),   # top menu
        # (16, 48, 120, 16),   # middle line
        # (16, 64, 120, 16),   # bottom
        (104, 137, 6, 154) #dialog
    ]

    frame = cv2.imread("dev_files/frame_test.png")
    results = ocr_from_regions(frame, regions, templates)
    print(TextCleaner(results)[0])
    

    # for i, text in enumerate(results):
    #     print(f"Region {i}: {text}")
