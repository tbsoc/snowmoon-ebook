"""Render ✓ → ≥ as inline glyph images (sym-*.png) for readers whose fonts lack them.
All share one ascent+descent band so they line up on the baseline at the same size."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
font_path = sys.argv[2] if len(sys.argv) > 2 else "C:/Windows/Fonts/seguisym.ttf"  # any font with these glyphs
f = ImageFont.truetype(font_path, 160)
asc, desc = f.getmetrics()
for name, ch in [("check", "\u2713"), ("arrow", "\u2192"), ("geq", "\u2265")]:
    im = Image.new("LA", (300, asc + desc), (0, 0))
    ImageDraw.Draw(im).text((40, 0), ch, font=f, fill=(0, 255))
    x0, _, x1, _ = im.getbbox()
    im.crop((x0 - 8, 0, x1 + 8, asc + desc)).save(out / f"sym-{name}.png", optimize=True)
