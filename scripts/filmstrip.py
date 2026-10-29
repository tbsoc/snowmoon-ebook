"""Turn the chapter 4 animation (captured frames, one per generation) into 2x2 key-frame
sheets with large captions, for readers that can't animate (e-ink)."""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

anim, shots = Path(sys.argv[1]), Path(sys.argv[2])
keep = (anim / "keep.txt").read_text().split("\n")[1:]  # drop t≈0 transition frame; keep[g] = generation g
gens = list(range(0, 101, 10)) + [len(keep) - 1]
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 54)
except OSError:
    font = ImageFont.load_default()

frames = [Image.open(keep[g]).convert("RGB") for g in gens]
fw, fh = frames[0].size
pad, cap = 24, 80
sheets = []
for s in range(0, len(frames), 4):
    sheet = Image.new("RGB", (2 * fw + 3 * pad, 2 * (fh + cap) + 3 * pad), "white")
    d = ImageDraw.Draw(sheet)
    for j, (im, g) in enumerate(zip(frames[s:s + 4], gens[s:s + 4])):
        x = pad + (j % 2) * (fw + pad)
        y = pad + (j // 2) * (fh + cap + pad)
        sheet.paste(im, (x, y))
        d.rectangle([x - 2, y - 2, x + fw + 1, y + fh + 1], outline="black", width=3)
        label = f"t = {g}"
        tw = d.textlength(label, font=font)
        d.text((x + (fw - tw) / 2, y + fh + 12), label, fill="black", font=font)
    name = f"ch4-0-{s // 4 + 1}.png"
    sheet.save(shots / name, optimize=True)
    sheets.append(name)

m = json.loads((shots / "manifest.json").read_text())
m["4"][0]["frames"] = sheets
m["4"][0]["caption"] = (f"Animated in the original edition. Shown here as key frames, generations "
                        f"0\u2013{gens[-1]}, read left to right, top to bottom.")
(shots / "manifest.json").write_text(json.dumps(m, indent=1))
print(sheets, gens)
