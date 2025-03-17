from PIL import Image
import numpy as np
import win32api, win32con, time, os
from skimage.color import rgb2lab, deltaE_cie76

# Configuration: canvas and tool coordinates
window = (595, 321)  # Top-left coordinate of the drawing canvas (for 1920x1080)
canvas_width = 875   # Maximum width of the drawing canvas
canvas_height = 489  # Maximum height of the drawing canvas

# Color tool coordinates on the palette
color_coords = {
    "black": (450, 410),
    "white": (450, 460),
    "#666666": (500, 410),
    "#0050CD": (540, 410),
    "#26C9FF": (540, 450),
    "#AAAAAA": (500, 450),
    "#017420": (450, 500),
    "#990000": (500, 500),
    "#964112": (540, 500),
    "#11B03C": (450, 550),
    "#FF0013": (500, 550),
    "#FF7829": (540, 550),
    "#B0701C": (450, 600),
    "#99004E": (500, 600),
    "#CB5A57": (540, 600),
    "#FFC126": (450, 650),
    "#FEAFA8": (540, 650),
    "#FF008F": (500, 650)
}

brush_coords = {
    2: (638, 920),   # 2x2 brush
    7: (700, 920),   # 8x8 brush
    11: (760, 920),  # 13x13 brush
    15: (824, 920),  # 18x18 brush
    20: (885, 920)   # 25x25 brush
}
scale = 1  # grid spacing: each image pixel maps 1:1 on screen

# Define palette RGB values for quantization
palette_rgb = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "#666666": (102, 102, 102),
    "#0050CD": (0, 80, 205),
    "#26C9FF": (38, 201, 255),
    "#AAAAAA": (170, 170, 170),
    "#017420": (1, 116, 32),
    "#990000": (153, 0, 0),
    "#964112": (150, 65, 18),
    "#11B03C": (17, 176, 60),
    "#FF0013": (255, 0, 19),
    "#FF7829": (255, 120, 41),
    "#B0701C": (176, 112, 28),
    "#99004E": (153, 0, 78),
    "#CB5A57": (203, 90, 87),
    "#FFC126": (255, 193, 38),
    "#FEAFA8": (254, 175, 168),
    "#FF008F": (255, 0, 143)
}

# Precompute the palette LAB values for more accurate color matching
def compute_palette_lab(palette_rgb):
    colors = np.array(list(palette_rgb.values()), dtype=np.float32)
    lab = rgb2lab(colors.reshape(1, -1, 3) / 255.0)[0]
    return {color: lab[i] for i, color in enumerate(palette_rgb.keys())}

palette_lab = compute_palette_lab(palette_rgb)

def click(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    time.sleep(0.001)

def select_brush(brush):
    bx, by = brush_coords[brush]
    click(bx, by)

def select_color(color):
    cx, cy = color_coords[color]
    click(cx, cy)

def choose_brush_size(ideal):
    options = [2, 7, 11, 15, 20]
    return max([op for op in options if op <= ideal], default=2)

# Updated color matching function using LAB color space and Delta E (CIE76)
def closest_palette_color(pixel):
    lab_pixel = rgb2lab(np.array(pixel).reshape(1, 1, 3) / 255.0)[0][0]
    best_color = None
    best_dist = float('inf')
    for color, lab in palette_lab.items():
        dist = deltaE_cie76(lab_pixel, lab)
        if dist < best_dist:
            best_dist = dist
            best_color = color
    return best_color

def image_to_palette_array(img):
    rgba_array = np.array(img)
    height, width, _ = rgba_array.shape
    palette_array = np.empty((height, width), dtype=object)
    for i in range(height):
        for j in range(width):
            if rgba_array[i, j, 3] == 0:
                palette_array[i, j] = None
            else:
                pixel = tuple(rgba_array[i, j, :3])
                palette_array[i, j] = closest_palette_color(pixel)
    return palette_array

def get_contiguous_block_size(i, j, palette_array, drawn_mask):
    height, width = palette_array.shape
    target_color = palette_array[i, j]
    s = 0
    while True:
        if i + s >= height or j + s >= width:
            break
        valid = True
        for x in range(i, i + s + 1):
            for y in range(j, j + s + 1):
                if drawn_mask[x, y] or palette_array[x, y] != target_color:
                    valid = False
                    break
            if not valid:
                break
        if not valid:
            break
        s += 1
    return s

if __name__ == "__main__":
    file_name = None
    for file in os.listdir(os.getcwd()):
        if file.endswith('.jpg') or file.endswith('.png'):
            file_name = file
            break
    if not file_name:
        exit(0)
    
    img = Image.open(file_name).convert("RGBA")
    img.thumbnail((canvas_width, canvas_height))
    palette_array = image_to_palette_array(img)
    height, width = palette_array.shape
    drawn_mask = np.zeros((height, width), dtype=bool)
    
    for i in range(height):
        for j in range(width):
            if drawn_mask[i, j] or palette_array[i, j] is None:
                continue
            pixel_color = palette_array[i, j]
            block_size = get_contiguous_block_size(i, j, palette_array, drawn_mask)
            ideal_size = block_size  # in screen pixels (scale = 1)
            brush_size = choose_brush_size(ideal_size)
            select_brush(brush_size)
            select_color(pixel_color)
            canvas_x = window[0] + j * scale
            canvas_y = window[1] + i * scale
            click(canvas_x, canvas_y)
            drawn_mask[i:i+block_size, j:j+block_size] = True
            time.sleep(0.002)
    
    print("Drawing complete!")
