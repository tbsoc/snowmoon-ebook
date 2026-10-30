# Snowmoon — Vitalik Buterin

Offline and e-reader editions of *Snowmoon*, a 32-chapter novel by Vitalik Buterin,
built from the author's published HTML at https://vitalik.eth.limo/snowmoon/.
The text is unchanged; only formatting and illustrations are adapted per edition.

*Snowmoon* is released by its author under the **GNU General Public License v3**
(see [`LICENSE.txt`](LICENSE.txt)). Everything in this repository is distributed under the
same license, including the build scripts.

## Editions

| File | What it is |
|---|---|
| [`snowmoon.epub`](snowmoon.epub) | EPUB 3 for **black-and-white e-ink** (Kobo Clara, Kindle Paperwhite, …) |
| [`snowmoon-color.epub`](snowmoon-color.epub) | EPUB 3 for **color e-ink** (Kobo Clara/Libra Colour, Kindle Colorsoft, …) |
| [`snowmoon.pdf`](snowmoon.pdf) | 6×9 in book layout with page numbers and chapter bookmarks |
| [`snowmoon-complete.html`](snowmoon-complete.html) | All chapters on one page, with linked contents and dark-mode toggle |
| [`html/`](html/index.html) | The author's original chapter pages, one per chapter, with a contents page |

### Black-and-white EPUB

The original pages draw their in-story device screens as light text on dark navy, which
turns into gray-on-gray on e-ink. This edition:

- renders every screen as black text on white with a solid frame, and sets black text
  directly on all table cells so no reader can override it
- converts the 56 inline SVG illustrations to high-resolution PNGs: dark backgrounds are
  inverted to dark-on-white, labels are drawn in one dark ink with a white halo
- encodes meaning that was carried only by color as shape: chapter 8's vote ring
  (● green / ○ red, with a legend) and chapter 6's keeper cohorts (● this year,
  ○ last year, ◆ second-last year)
- replaces chapter 4's animation with key frames (generations 0–109, every 10th)
- renders screens with color emoji or form controls (chapters 1, 7, 20) as images
- swaps ✓, → and ≥ for inline glyph images, since Kobo's built-in fonts lack them
- adds table grid lines that Kobo's renderer honors (`border` attributes, not just CSS)
- adds small speaker labels (editorial, in sans-serif capitals) to dialogue in group conversations
  where the original relies on each character's color alone to show who is speaking. Speakers are
  inferred from the lines the author does tag; a color shared by two characters in a chapter is
  left unlabeled. On author-tagged lines held out for testing, the labels are right 98.6% of the
  time ([`scripts/speakers.py`](scripts/speakers.py))

### Color EPUB

Same structure, but keeps the original hues: each speaker's dialogue color, colored words
and labels in the screens, tinted screen backgrounds, chapter 8's green/red vote circles
and diagram colors. All colors are darkened in OKLab (hue preserved) so text keeps at least
a 5.6:1 contrast ratio against the page.

## Rebuilding

Requirements: Python 3.10+, Node 18+, and Google Chrome. Set `CHROME` to the browser
binary if it isn't at the default Windows path.

```bash
python -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
npm install --prefix scripts
```

The pipeline, from the repo root (`work/` holds intermediate images and is git-ignored):

```bash
# 1. HTML editions and print HTML
python scripts/build.py source .
# 2. Capture SVG illustrations, chapter 4's animation frames, and key-frame sheets
node scripts/shoot.js source/html work/shots
node scripts/frames.js source/html/chapter-4.html work/anim "$(python -c "print(','.join(f'{i*0.011+0.0055:.4f}' for i in range(1000)))")"
python scripts/dedupe_frames.py work/anim
python scripts/filmstrip.py work/anim work/shots
# 3. E-ink processing (gamma 2.2 for B&W, 1.4 for color) and symbol glyphs
python scripts/eink.py work/shots work/eink
python scripts/make_symbols.py work/eink   # optional 2nd arg: a font with ✓ → ≥
# 4. EPUB pass 1 marks screens to rasterize; capture them; pass 2 swaps them in
python scripts/build.py source . work/eink
node scripts/shoot_screens.js <unzipped snowmoon.epub>/OEBPS work/eink
python scripts/build.py source . work/eink
# 5. PDF
node scripts/render.js build/snowmoon-print.html snowmoon.pdf
```

For the color edition, run `eink.py` with gamma `1.4` into `work/eink_color`, copy in the
chapter 8 capture from `node scripts/shoot.js source/html work/shots_color color` and the
`sym-*.png` glyphs, then run the two `build.py` passes with a trailing `color` argument.

`scripts/audit.js <unzipped epub>/OEBPS` reports any rendered text that is light or
low-contrast.
