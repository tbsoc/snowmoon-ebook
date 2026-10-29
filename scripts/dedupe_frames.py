"""Keep only frames that differ from the previous one (frames.js output -> keep.txt for filmstrip.py)."""
import sys, hashlib
from pathlib import Path
from PIL import Image

anim = Path(sys.argv[1])
frames = sorted(anim.glob("t*.png"), key=lambda f: float(f.stem[1:]))
keep, prev = [], None
for f in frames:
    h = hashlib.md5(Image.open(f).convert("L").tobytes()).hexdigest()
    if h != prev:
        keep.append(str(f))
        prev = h
(anim / "keep.txt").write_text("\n".join(keep))
print(len(frames), "captured", len(keep), "distinct")
