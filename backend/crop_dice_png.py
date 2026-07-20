"""
Crop exact real translucent dice from art/dice.png (1928x842)
Tightly crops out text/labels below each die.
"""

import os
from PIL import Image

DICE_PNG_PATH = "art/dice.png"
OUT_DIR = "frontend/public/art/dice"

os.makedirs(OUT_DIR, exist_ok=True)

img = Image.open(DICE_PNG_PATH)
w, h = img.size
print(f"Loaded dice.png: {w}x{h}")

# Tight crop boxes excluding all text below each die
dice_crops = [
    ("d20", (55, 140, 255, 295)),
    ("d12", (330, 140, 500, 295)),
    ("d10", (590, 140, 760, 295)),
    ("d%", (850, 140, 1020, 295)),
    ("d8", (1130, 140, 1300, 295)),
    ("d6", (1390, 140, 1560, 295)),
    ("d4", (1650, 140, 1820, 295)),
]

for name, box in dice_crops:
    cropped = img.crop(box)
    filepath = os.path.join(OUT_DIR, f"{name}.png")
    cropped.save(filepath, format="PNG")
    print(
        f"Saved text-free tight die: {filepath} ({cropped.size[0]}x{cropped.size[1]})"
    )

img.save("frontend/public/art/dice-destiny-chart.png", format="PNG")
print("Saved full 7 Dice of Destiny chart!")
