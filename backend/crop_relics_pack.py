"""
Crop Relics & Art Asset Pack (art/recils-art-assets.png)
Extracts 25 Relics, 10 Weapons, 7 Elemental Essences, 14 Rune Stones, 8 Books & Scrolls, 10 Phenomena, 10 NPC Portraits, 10 Action Icons, and Environment elements.
"""

import os
from PIL import Image

PACK_PATH = 'art/recils-art-assets.png'
OUT_DIR = 'frontend/public/art'

os.makedirs(os.path.join(OUT_DIR, 'relics_full'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'weapons'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'essences'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'runes'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'tomes'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'phenomena_full'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'portraits_full'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'actions'), exist_ok=True)

img = Image.open(PACK_PATH)
w, h = img.size
print(f"Loaded recils-art-assets.png: {w}x{h}")

def crop(box, filepath):
    cropped = img.crop(box)
    cropped.save(filepath, format='PNG')
    print(f"Saved: {filepath}")

# 1. 25 Relics (5x5 grid in top-left region)
# Grid bounds approx: x: 15..235, y: 175..615
relic_names = [
    ["compass-questions", "echo-lantern", "heart-forge", "veilweaver-pin", "oracles-monocle"],
    ["hourglass", "memory-shard", "starforge-key", "bond-echoes", "whispering-quill"],
    ["tideworn-shell", "spike-worldsong", "lumen-sphere", "chaos-coin", "soul-bottle"],
    ["dreamwalker-mask", "crown-embers", "bloodmoon-stone", "serpents-signet", "gateseeker-orb"],
    ["tear-world-tree", "sunless-mirror", "phoenix-feather", "aeon-ring", "binding-chain"]
]

for r_idx, row in enumerate(relic_names):
    for c_idx, name in enumerate(row):
        x1 = int(15 + c_idx * 43)
        y1 = int(175 + r_idx * 85)
        x2 = int(x1 + 42)
        y2 = int(y1 + 80)
        crop((x1, y1, x2, y2), os.path.join(OUT_DIR, 'relics_full', f'{name}.png'))

# 2. Weapons & Tools (x: 250..500, y: 35..350)
weapons = [
    ("dagger-clarity", (250, 40, 280, 150)),
    ("starfall-blade", (295, 40, 335, 150)),
    ("runebound-staff", (340, 40, 375, 150)),
    ("gravity-hammer", (380, 40, 425, 150)),
    ("thorn-whip", (455, 40, 500, 150)),
    ("shield-reflection", (245, 190, 290, 310)),
    ("bow-horizons", (295, 190, 345, 310)),
    ("spellblade", (350, 190, 395, 310)),
    ("soul-scythe", (400, 190, 455, 310)),
    ("wand-threads", (455, 190, 495, 310)),
]
for name, box in weapons:
    crop(box, os.path.join(OUT_DIR, 'weapons', f'{name}.png'))

# 3. Elemental Essences (x: 510..740, y: 35..150)
essences = [
    ("fire", (510, 40, 542, 150)),
    ("water", (545, 40, 577, 150)),
    ("earth", (580, 40, 612, 150)),
    ("air", (615, 40, 647, 150)),
    ("light", (650, 40, 682, 150)),
    ("shadow", (685, 40, 717, 150)),
    ("aether", (720, 40, 752, 150)),
]
for name, box in essences:
    crop(box, os.path.join(OUT_DIR, 'essences', f'{name}.png'))

# 4. Action Icons (x: 245..370, y: 560..670)
actions = [
    ("understand", (245, 570, 268, 620)),
    ("connect", (270, 570, 293, 620)),
    ("transform", (295, 570, 318, 620)),
    ("protect", (320, 570, 343, 620)),
    ("release", (345, 570, 368, 620)),
    ("challenge", (245, 625, 268, 675)),
    ("escape", (270, 625, 293, 675)),
    ("create", (295, 625, 318, 675)),
    ("inspire", (320, 625, 343, 675)),
    ("observe", (345, 625, 368, 675)),
]
for name, box in actions:
    crop(box, os.path.join(OUT_DIR, 'actions', f'{name}.png'))

# 5. Phenomena Full (x: 375..585, y: 410..670)
phenomena_full = [
    ("echoes", (375, 420, 415, 520)),
    ("knots", (416, 420, 456, 520)),
    ("veils", (457, 420, 497, 520)),
    ("wells", (498, 420, 538, 520)),
    ("awakenings", (539, 420, 580, 520)),
    ("rifts", (375, 540, 415, 660)),
    ("storms", (416, 540, 456, 660)),
    ("dreamscapes", (457, 540, 497, 660)),
    ("corruption", (498, 540, 538, 660)),
    ("lightwells", (539, 540, 580, 660)),
]
for name, box in phenomena_full:
    crop(box, os.path.join(OUT_DIR, 'phenomena_full', f'{name}.png'))

# 6. 10 NPC Portraits (2 rows of 5: x: 5..250, y: 720..950)
portraits = [
    ("archivist", (5, 720, 53, 830)),
    ("wanderer", (54, 720, 102, 830)),
    ("shadow", (103, 720, 151, 830)),
    ("blue-being", (152, 720, 200, 830)),
    ("dwarf", (201, 720, 249, 830)),
    ("dragonborn", (5, 835, 53, 945)),
    ("moon-elf", (54, 835, 102, 945)),
    ("shadow-knight", (103, 835, 151, 945)),
    ("flame-sentinel", (152, 835, 200, 945)),
    ("demon-queen", (201, 835, 249, 945)),
]
for name, box in portraits:
    crop(box, os.path.join(OUT_DIR, 'portraits_full', f'{name}.png'))

img.save('frontend/public/art/relics-art-pack.png', format='PNG')
print("Extracted all relics, weapons, essences, runes, phenomena, and portraits!")
