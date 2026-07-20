"""
SoulSmith Image Cropping & Asset Extractor
Splits graphics_bundle.png into isolated UI icons, dice assets, portraits, and frames.
"""

import os
from PIL import Image

BUNDLE_PATH = 'art/graphics_bundle.png'
OUT_DIR = 'frontend/public/art'

os.makedirs(os.path.join(OUT_DIR, 'dice'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'resources'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'phenomena'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'portraits'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'elements'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'frames'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'effects'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'sections'), exist_ok=True)

img = Image.open(BUNDLE_PATH)

def crop_and_save(box, filepath):
    cropped = img.crop(box)
    cropped.save(filepath, format='PNG')
    print(f"Saved: {filepath} ({cropped.size[0]}x{cropped.size[1]})")

# 1. Main Logo with extra vertical padding at top/bottom
crop_and_save((20, 5, 350, 165), os.path.join(OUT_DIR, 'soulsmith-logo.png'))

# 2. Seven Dice Individual Crops
dice_mapping = [
    ('d4', (395, 140, 465, 290)),
    ('d6', (470, 140, 540, 290)),
    ('d8', (545, 140, 615, 290)),
    ('d10', (620, 140, 690, 290)),
    ('d%', (695, 140, 765, 290)),
    ('d12', (770, 140, 840, 290)),
    ('d20', (845, 140, 915, 290)),
]

for name, box in dice_mapping:
    crop_and_save(box, os.path.join(OUT_DIR, 'dice', f'{name}.png'))

# 3. Seven Dice Full Banner
crop_and_save((390, 120, 920, 310), os.path.join(OUT_DIR, 'seven-dice-set.png'))

# 4. Resource Tokens
resources_mapping = [
    ('resonance', (925, 140, 980, 290)),
    ('strain', (985, 140, 1040, 290)),
    ('thread', (1045, 140, 1100, 290)),
    ('fate', (1105, 140, 1160, 290)),
    ('soul', (1165, 140, 1220, 290)),
    ('momentum', (1225, 140, 1280, 290)),
]

for name, box in resources_mapping:
    crop_and_save(box, os.path.join(OUT_DIR, 'resources', f'{name}.png'))

# 5. Phenomena Icons
phenomena_mapping = [
    ('echoes', (925, 410, 985, 570)),
    ('knots', (990, 410, 1050, 570)),
    ('veils', (1055, 410, 1115, 570)),
    ('wells', (1120, 410, 1180, 570)),
    ('awakenings', (1185, 410, 1245, 570)),
]

for name, box in phenomena_mapping:
    crop_and_save(box, os.path.join(OUT_DIR, 'phenomena', f'{name}.png'))

# 6. NPC Portraits
portraits_mapping = [
    ('archivist', (515, 720, 600, 830)),
    ('wanderer', (615, 720, 700, 830)),
    ('shadow', (715, 720, 800, 830)),
    ('maiden', (815, 720, 900, 830)),
    ('dwarf', (915, 720, 1000, 830)),
]

for name, box in portraits_mapping:
    crop_and_save(box, os.path.join(OUT_DIR, 'portraits', f'{name}.png'))

# 7. UI Frames
crop_and_save((1305, 130, 1415, 235), os.path.join(OUT_DIR, 'frames', 'frame-rect-1.png'))
crop_and_save((1420, 130, 1525, 235), os.path.join(OUT_DIR, 'frames', 'frame-oval-1.png'))
crop_and_save((1305, 235, 1415, 340), os.path.join(OUT_DIR, 'frames', 'frame-rect-2.png'))
crop_and_save((1420, 235, 1525, 340), os.path.join(OUT_DIR, 'frames', 'frame-round-1.png'))

# 8. Relics & Artifacts Grid
crop_and_save((0, 595, 500, 835), os.path.join(OUT_DIR, 'sections', 'relics-grid.png'))

# 9. Magic Circles
crop_and_save((860, 650, 1430, 820), os.path.join(OUT_DIR, 'sections', 'magic-circles.png'))

# 10. Effects & Overlays
crop_and_save((1140, 875, 1520, 990), os.path.join(OUT_DIR, 'effects', 'magic-overlays.png'))

print("Logo bounding box adjusted successfully!")
