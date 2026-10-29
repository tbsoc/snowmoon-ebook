"""Make device-screen screenshots e-ink friendly: light background, dark ink, hue kept.
Dark-background images get their lightness inverted (Lab L channel); every image then
has its background pushed to pure white and mid-tones darkened."""
import sys, json, shutil
from collections import Counter
from pathlib import Path
from PIL import Image

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
dst.mkdir(exist_ok=True)
GAMMA = float(sys.argv[3]) if len(sys.argv) > 3 else 2.2

for f in sorted(src.glob("*.png")):
    rgb = Image.open(f).convert("RGB")
    w, h = rgb.size
    lab = rgb.convert("LAB")
    L, a, b = lab.split()
    # background = most common lightness over the whole image (edges can carry stray strips)
    sample = [L.getpixel((x, y)) for x in range(0, w, 3) for y in range(0, h, 3)]
    bg = Counter(sample).most_common(1)[0][0]
    invert = bg < 128
    if invert:
        L = L.point(lambda v: 255 - v)
        bg = 255 - bg
    bg = max(bg, 1)
    L = L.point(lambda v: 255 if v >= bg else int(255 * (v / bg) ** GAMMA))
    out = Image.merge("LAB", (L, a, b)).convert("RGB")
    out.save(dst / f.name, optimize=True)
    print(f.name, "inverted" if invert else "kept", "bg", bg)

shutil.copy(src / "manifest.json", dst / "manifest.json")
