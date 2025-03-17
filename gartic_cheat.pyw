from PIL import Image
import numpy as np
import win32api, win32con, time, os
from skimage.color import rgb2lab, deltaE_cie76

# Configuration: canvas and tool coordinates
window = (595, 321)
canvas_width = 875
canvas_height = 489

# Color tool coordinates on the palette
color_coords = {
    "black": (450, 410), "white": (450, 460), "#666666": (500, 410), "#0050CD": (540, 410), "#26C9FF": (540, 450),
    "#AAAAAA": (500, 450), "#017420": (450, 500), "#990000": (500, 500), "#964112": (540, 500), "#11B03C": (450, 550),
    "#FF0013": (500, 550), "#FF7829": (540, 550), "#B0701C": (450, 600), "#99004E": (500, 600), "#CB5A57": (540, 600),
    "#FFC126": (450, 650), "#FEAFA8": (540, 650), "#FF008F": (500, 650)
}

brush_coords = {2: (638, 920)}  # Only the 2x2 brush
scale = 1

# Define palette RGB values for quantization
palette_rgb = {
    "black": (0, 0, 0), "white": (255, 255, 255), "#666666": (102, 102, 102), "#0050CD": (0, 80, 205),
    "#26C9FF": (38, 201, 255), "#AAAAAA": (170, 170, 170), "#017420": (1, 116, 32), "#990000": (153, 0, 0),
    "#964112": (150, 65, 18), "#11B03C": (17, 176, 60), "#FF0013": (255, 0, 19), "#FF7829": (255, 120, 41),
    "#B0701C": (176, 112, 28), "#99004E": (153, 0, 78), "#CB5A57": (203, 90, 87), "#FFC126": (255, 193, 38),
    "#FEAFA8": (254, 175, 168), "#FF008F": (255, 0, 143)
}

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

def select_brush():
    bx, by = brush_coords[2]
    click(bx, by)

def select_color(color):
    cx, cy = color_coords[color]
    click(cx, cy)

def closest_palette_color(pixel):
    lab_pixel = rgb2lab(np.array(pixel).reshape(1, 1, 3) / 255.0)[0][0]
    return min(palette_lab, key=lambda color: deltaE_cie76(lab_pixel, palette_lab[color]))

def image_to_palette_array(img):
    rgba_array = np.array(img)
    height, width, _ = rgba_array.shape
    return np.array([[None if rgba_array[i, j, 3] == 0 else closest_palette_color(tuple(rgba_array[i, j, :3])) 
                      for j in range(width)] for i in range(height)], dtype=object)

if __name__ == "__main__":
    file_name = next((file for file in os.listdir(os.getcwd()) if file.endswith(('.jpg', '.png'))), None)
    if not file_name:
        exit(0)
    
    img = Image.open(file_name).convert("RGBA")
    img.thumbnail((canvas_width, canvas_height))
    palette_array = image_to_palette_array(img)
    height, width = palette_array.shape
    
    select_brush()
    
    for i in range(height):
        for j in range(width):
            if palette_array[i, j] is None:
                continue
            select_color(palette_array[i, j])
            click(window[0] + j * scale, window[1] + i * scale)
            time.sleep(0.002)
    
    print("Drawing complete!")
