"""Build Snowmoon (GPL v3, by Vitalik Buterin) into per-chapter HTML, combined HTML,
print HTML (for PDF) and EPUB 3. Source: https://vitalik.eth.limo/snowmoon/"""
import re, sys, json, shutil, uuid, zipfile, datetime, html
from pathlib import Path
from bs4 import BeautifulSoup

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
N = 32
TITLE, AUTHOR = "Snowmoon", "Vitalik Buterin"
SOURCE_URL = "https://vitalik.eth.limo/snowmoon/"

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "html").mkdir(exist_ok=True)

def read(p):
    return Path(p).read_text(encoding="utf-8")

first = read(SRC / "html/chapter-1.html")
SITE_CSS = re.search(r"<style>(.*?)</style>", first, re.S).group(1)

# Author's front-matter declarations (license, AI usage) from the index page
idx = BeautifulSoup(read(SRC / "index.html"), "lxml")
decl = idx.select_one(".declaration")
for s in decl.select("script"):
    s.decompose()
DECL_HTML = decl.decode_contents() if decl else ""

chapters = []  # (n, title, dateline_text, inner_html)
for n in range(1, N + 1):
    soup = BeautifulSoup(read(SRC / f"html/chapter-{n}.html"), "lxml")
    page = soup.select_one(".document-page")
    for nav in page.select("nav.chapter-nav"):
        nav.decompose()
    for a in page.select('a[href^="chapter-"]'):
        a["href"] = "#" + a["href"].replace(".html", "")
    h1 = page.find("h1")
    title = h1.get_text(strip=True) if h1 else f"Chapter {n}"
    dl = page.select_one(".dateline.chapter-open .txt")
    dateline = " · ".join(s.get_text(strip=True) for s in dl.select(".place, .date")) if dl else ""
    chapters.append((n, title, dateline, page.decode_contents().strip()))
    shutil.copy(SRC / f"html/chapter-{n}.html", OUT / f"html/chapter-{n}.html")

shutil.copy(SRC / "LICENSE.txt", OUT / "LICENSE.txt")
shutil.copy(SRC / "LICENSE.txt", OUT / "html/LICENSE.txt")

LICENSE_NOTE = f"""<p><em>{TITLE}</em> &copy; {AUTHOR}. Released under the
<a href="https://www.gnu.org/licenses/gpl-3.0.html">GNU General Public License v3</a>.
Original source: <a href="{SOURCE_URL}">{SOURCE_URL}</a>. This edition reformats the
author's published HTML without changes to the text. The full license text is included
alongside this file as LICENSE.txt.</p>"""

DARK_JS = read(SRC / "html/chapter-1.html").split("<script>")[-1].split("</script>")[0]

# ---------- per-chapter index ----------
toc_items = "\n".join(
    f'<li><a href="chapter-{n}.html">{html.escape(t)}</a><span class="dl">{html.escape(d)}</span></li>'
    for n, t, d, _ in chapters)
(OUT / "html/index.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE} — Contents</title><style>{SITE_CSS}
.toc {{ list-style: none !important; padding-left: 0 !important; }}
.toc li {{ display: flex; justify-content: space-between; gap: 1em; border-bottom: 1px solid #eee; padding: 4px 0; }}
.toc .dl {{ color: #8a83a8; font-size: .85rem; }}
</style></head><body>
<button class="dark-toggle" onclick="toggleDarkMode()">☀️</button>
<div class="document-page"><h1>{TITLE}</h1><p>by {AUTHOR}</p>
<p><a href="../snowmoon-complete.html">Read all chapters on one page</a></p>
<ol class="toc">{toc_items}</ol><hr>{LICENSE_NOTE}</div>
<script>{DARK_JS}</script></body></html>""", encoding="utf-8")

# ---------- combined single-page HTML ----------
toc_combined = "\n".join(
    f'<li><a href="#chapter-{n}">{html.escape(t)}</a><span class="dl">{html.escape(d)}</span></li>'
    for n, t, d, _ in chapters)
sections = "\n".join(
    f'<section class="document-page chapter" id="chapter-{n}">{body}\n'
    f'<p class="back"><a href="#contents">↑ Contents</a></p></section>'
    for n, _, _, body in chapters)
(OUT / "snowmoon-complete.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE} — Complete</title><style>{SITE_CSS}
html {{ scroll-behavior: smooth; }}
.document-page {{ margin-bottom: 40px !important; }}
.toc {{ list-style: none !important; padding-left: 0 !important; }}
.toc li {{ display: flex; justify-content: space-between; gap: 1em; border-bottom: 1px solid rgba(128,128,128,.2); padding: 4px 0; }}
.toc .dl {{ color: #8a83a8; font-size: .85rem; }}
.back {{ text-align: right; font-size: .9rem !important; }}
.back a {{ color: #a49dc4; text-decoration: none; }}
</style></head><body>
<button class="dark-toggle" onclick="toggleDarkMode()">☀️</button>
<div class="document-page" id="contents"><h1>{TITLE}</h1><p>by {AUTHOR}</p>
<h2>Contents</h2><ol class="toc">{toc_combined}</ol>
<h2>About this book</h2><div class="declaration">{DECL_HTML}</div><hr>{LICENSE_NOTE}</div>
{sections}
<script>{DARK_JS}</script></body></html>""", encoding="utf-8")

# ---------- book CSS shared by print + EPUB ----------
BOOK_CSS = """
body { font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', serif; line-height: 1.5; color: #1a1a1a; }
p { margin: 0; text-indent: 1.4em; text-align: justify; hyphens: auto; -webkit-hyphens: auto; }
h1 + p, .dateline + p, blockquote p, td p, .device-view p, hr + p, .noindent { text-indent: 0; }
h1 { font-weight: normal; font-size: 1.9em; text-align: center; margin: 2.5em 0 .3em; letter-spacing: .04em; }
h2 { font-weight: normal; font-size: 1.3em; margin: 1.4em 0 .5em; }
h3 { font-size: 1.05em; margin: 1em 0 .4em; }
em { font-style: italic; }
blockquote { margin: 1em 1.5em; font-style: italic; }
blockquote p { margin-bottom: .5em; }
.dateline { text-align: center; margin: 0 0 2em; }
.dateline .rule { display: none; }
.dateline .txt { font-size: .8em; letter-spacing: .08em; color: #555; }
.dateline .place { font-weight: bold; }
.dateline .sep { margin: 0 .5em; color: #999; }
.dateline .date { text-transform: uppercase; letter-spacing: .15em; font-size: .9em; }
.dateline.scene-break { margin: 1.6em 0 1em; }
.dateline.scene-break .txt { font-size: .7em; text-transform: uppercase; letter-spacing: .14em; color: #777; }
.dateline.scene-break::before { content: "⁂"; display: block; color: #999; margin-bottom: .3em; }
hr { border: none; text-align: center; margin: 1.2em 0; }
hr::after { content: "* * *"; color: #888; letter-spacing: .5em; }
.device-view { background-color: #0a0e27; color: #7fbcff; font-family: 'Courier New', Courier, monospace;
  font-size: .82em; line-height: 1.35; padding: .9em; margin: 1.1em 0; border-radius: 4px;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; page-break-inside: avoid; break-inside: avoid; }
.device-view p { text-align: left; }
.device-view h3 { color: #a8d1ff; margin-top: 0; }
.device-view table { border-collapse: collapse; margin: .4em auto; width: 100%; }
.device-view th, .device-view td { border: 1px solid #5a78b0; padding: .3em .45em; vertical-align: top; color: #7fbcff; }
.device-view th { background: #16204a; }
table { border-collapse: collapse; }
td, th { padding: .3em .5em; }
svg, img { max-width: 100%; height: auto; display: block; margin: .6em auto; }
.spk { color: var(--spk-lt); }
.device-view .spk { color: var(--spk-dk); }
.title-page { text-align: center; padding-top: 30%; }
.title-page h1 { font-size: 3em; margin: 0 0 .4em; letter-spacing: .12em; }
.title-page .author { font-size: 1.3em; font-style: italic; }
.front p { text-indent: 0; margin-bottom: .7em; text-align: left; }
.decl-label { font-weight: bold; display: block; margin-top: 1em; }
ol.toc { list-style: none; padding: 0; }
ol.toc li { margin: .25em 0; }
ol.toc a { color: inherit; text-decoration: none; }
ol.toc .dl { color: #777; font-size: .85em; margin-left: .6em; }
a { color: #2a4a8a; }
"""

# ---------- print HTML (rendered to PDF by Chrome) ----------
print_sections = "\n".join(
    f'<section class="chapter" id="chapter-{n}">{body}</section>' for n, _, _, body in chapters)
toc_print = "\n".join(
    f'<li><a href="#chapter-{n}">{html.escape(t)}</a><span class="dl">{html.escape(d)}</span></li>'
    for n, t, d, _ in chapters)
(OUT / "build").mkdir(exist_ok=True)
(OUT / "build/snowmoon-print.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{TITLE}</title><style>
@page {{ size: 6in 9in; margin: .75in .7in .8in .7in; }}
html {{ font-size: 10.5pt; }}
{BOOK_CSS}
.chapter, .front, .toc-page {{ break-before: page; }}
.chapter h1 {{ margin-top: 1.2in; }}
.title-page {{ height: 7in; padding-top: 2.2in; }}
.device-view {{ font-size: .78em; }}
p {{ orphans: 2; widows: 2; }}
</style></head><body>
<div class="title-page"><h1>{TITLE.upper()}</h1><p class="author noindent">{AUTHOR}</p></div>
<div class="toc-page"><h2>Contents</h2><ol class="toc">{toc_print}</ol></div>
{print_sections}
<div class="front"><h2>About this book</h2><div class="declaration">{DECL_HTML}</div>{LICENSE_NOTE}</div>
</body></html>""", encoding="utf-8")

# ---------- EPUB 3 ----------
def xhtml_body(fragment):
    """Re-serialize an HTML fragment as well-formed XHTML."""
    s = BeautifulSoup(f"<div id='__w'>{fragment}</div>", "lxml")
    w = s.find(id="__w")
    for c in w.find_all("center"):
        c.name = "div"; c["style"] = (c.get("style", "") + ";text-align:center").lstrip(";")
    for t in w.find_all(True):
        if t.name == "svg":
            t["xmlns"] = "http://www.w3.org/2000/svg"
        elif t.name == "table":  # presentational borders: Kobo's RMSDK honors these even when CSS borders are dropped
            t["border"], t["cellpadding"], t["cellspacing"] = "1", "4", "0"
    out = "".join(str(x) for x in w.contents)
    out = re.sub(r"<(br|hr|img|col|meta|input)([^>]*?)(?<!/)>", r"<\1\2/>", out)
    out = re.sub(r"</(br|hr|img|col)>", "", out)
    out = out.replace("&nbsp;", "&#160;")
    return out

def xpage(title, body, has_svg=False):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="book.css"/></head>
<body>{body}</body></html>"""

uid = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, SOURCE_URL))
now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
files = {}  # name -> (content, props)
files["title.xhtml"] = (xpage(TITLE, f'<section epub:type="titlepage" class="title-page"><h1>{TITLE.upper()}</h1><p class="author noindent">{AUTHOR}</p></section>'), "")

# E-ink: swap inline SVGs for pre-rendered high-contrast grayscale PNGs (see shoot.js)
IMG_DIR = Path(sys.argv[3]) if len(sys.argv) > 3 else None
COLOR = len(sys.argv) > 4 and sys.argv[4] == "color"  # color e-ink edition (Kaleido-class screens)

# ---------- color helpers (OKLab keeps hue while changing lightness) ----------
NAMED = {"red": "#ff0000", "yellow": "#ffff00", "green": "#008000", "blue": "#0000ff", "lightblue": "#add8e6",
         "white": "#ffffff", "black": "#000000", "orange": "#ffa500", "purple": "#800080", "gray": "#808080",
         "grey": "#808080", "pink": "#ffc0cb", "cyan": "#00ffff", "magenta": "#ff00ff", "lime": "#00ff00"}

def _lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def _gam(c): return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055

def rgb_to_oklch(r, g, b):
    r, g, b = _lin(r), _lin(g), _lin(b)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    import math
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360

def oklch_to_hex(L, C, h):
    import math
    for _ in range(40):  # shrink chroma until the color fits in sRGB
        A, B = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
        l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
        m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
        s = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
        rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
               -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
               -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
        if all(-0.001 <= c <= 1.001 for c in rgb):
            break
        C *= 0.92
    return "#" + "".join(f"{round(max(0, min(1, _gam(max(0, c)))) * 255):02x}" for c in rgb)

def parse_color(v):
    """CSS color -> (L, C, h, alpha) in OKLCH, or None."""
    v = v.strip().lower()
    v = NAMED.get(v, v)
    m = re.match(r"oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+)", v)
    if m:
        L = float(m.group(1)) / (100 if m.group(2) else 1)
        return L, float(m.group(3)), float(m.group(4)), 1.0
    m = re.match(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+))?", v)
    if m:
        r, g, b = (float(m.group(i)) / 255 for i in (1, 2, 3))
        return (*rgb_to_oklch(r, g, b), float(m.group(4) or 1))
    m = re.match(r"#([0-9a-f]{3}|[0-9a-f]{6})\b", v)
    if m:
        hx = m.group(1)
        if len(hx) == 3:
            hx = "".join(c * 2 for c in hx)
        return (*rgb_to_oklch(*(int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))), 1.0)
    return None

def ink(v):
    """A color meant for a dark screen -> same hue, dark enough to read on a light page."""
    p = parse_color(v)
    if not p or p[1] < 0.035:  # near-white / gray ink -> plain black
        return "#000"
    L, C, h, _ = p
    return oklch_to_hex(min(L, 0.50), min(max(C * 1.3, 0.09), 0.19), h)

def tint(v):
    """A screen background -> a pale tint of the same hue."""
    p = parse_color(v)
    if not p or p[3] < 0.3 or p[1] < 0.02:  # translucent highlight or neutral -> light gray
        return "#ececec"
    return oklch_to_hex(0.94, min(p[1], 0.035), p[2])
IMG_MANIFEST = json.loads(read(IMG_DIR / "manifest.json")) if IMG_DIR else {}
images = []  # file names to package

def swap_svgs(n, fragment):
    shots = IMG_MANIFEST.get(str(n), [])
    s = BeautifulSoup(f"<div id='__w'>{fragment}</div>", "lxml")
    svgs = [v for v in s.find(id="__w").find_all("svg") if not v.find_parent("svg")]
    assert len(svgs) == len(shots), (n, len(svgs), len(shots))
    for v, shot in zip(svgs, shots):
        if shot.get("frames"):  # animated SVG -> sequence of key-frame sheets
            wrap = s.new_tag("div")
            wrap["class"] = "keyframes"
            for f in shot["frames"]:
                img = s.new_tag("img", src=f"images/{f}", alt="Key frames of animation")
                img["class"] = "eink"
                img["style"] = "width:100%"
                wrap.append(img)
                images.append(f)
            cap = s.new_tag("p")
            cap["class"] = "caption"
            cap.string = shot["caption"]
            wrap.append(cap)
            v.replace_with(wrap)
            continue
        pct = min(100, max(55, round(shot["w"] / 420 * 100)))
        img = s.new_tag("img", src=f"images/{shot['file']}", alt="Illustration")
        img["class"] = "eink"
        img["style"] = f"width:{pct}%"
        v.replace_with(img)
        images.append(shot["file"])
    return s.find(id="__w").decode_contents()

# Screens Kobo can't draw (color emoji, form controls) become screenshots of the EPUB-styled
# screen; pass 1 marks them with data-raster, shoot_screens.js captures them, pass 2 swaps them in.
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-⛿⬀-⯿]")
RASTER = json.loads(read(IMG_DIR / "screens.json")) if IMG_DIR and (IMG_DIR / "screens.json").exists() else {}

def kobo_screens(n, fragment):
    s = BeautifulSoup(f"<div id='__w'>{fragment}</div>", "lxml")
    w = s.find(id="__w")
    # Inline colors were picked for dark screens (pale text, dark fills); Kobo keeps inline backgrounds
    # even under !important rules, so strip them: black ink on white paper everywhere.
    for el in w.select("[style]"):
        if el.find_parent("svg") or el.name == "svg":
            continue
        decls = [d.strip() for d in el["style"].split(";") if ":" in d]
        kept = []
        for d in decls:
            prop, val = (x.strip() for x in d.split(":", 1))
            prop = prop.lower()
            if COLOR:  # keep hues, but as dark ink on pale tints
                if prop == "color":
                    d = f"color:{ink(val)}"
                elif prop in ("background", "background-color"):
                    d = f"background-color:{tint(val)}"
                elif prop == "border-color":
                    d = f"border-color:{ink(val)}"
                elif prop == "--spk-lt":  # speaker color (oklch; Kobo can't read it) -> inline hex
                    kept.append(f"color:{ink(val)}")
                    continue
                elif prop in ("--spk-dk", "--dv-ink"):
                    continue
                kept.append(d)
                continue
            if prop in ("color", "background", "background-color", "--dv-ink"):
                continue
            if prop == "border-color":
                d = "border-color:#000"
            kept.append(d)
        if kept:
            el["style"] = ";".join(kept)
        else:
            del el["style"]
    for cell in w.find_all(["td", "th"]):  # inline ink: wins over any stylesheet on every reader
        st = cell.get("style", "")
        if COLOR and re.search(r"(^|;)\s*color\s*:", st):
            continue
        cell["style"] = (st.rstrip(";") + ";color:#000").lstrip(";")
    screens = [d for d in w.select(".device-view") if not d.find_parent(class_="device-view")
               and (d.find(["input", "select", "textarea", "progress", "meter"]) or EMOJI.search(d.get_text()))]
    shots = RASTER.get(str(n))
    for k, d in enumerate(screens):
        if shots:
            img = s.new_tag("img", src=f"images/{shots[k]['file']}", alt="Device screen")
            img["class"] = "eink screen"
            d.replace_with(img)
            images.append(shots[k]["file"])
        else:
            d["data-raster"] = str(k)
    for btn in w.find_all("button"):  # RMSDK drops button chrome; draw a box instead
        btn.name = "span"
        btn["class"] = "btn"
    return w.decode_contents()

# Symbols missing from Kobo's built-in fonts -> inline glyph images (sym-*.png, 1em box = 160px, band 214px)
SYMBOLS = {"✓": ("check", "check mark"), "→": ("arrow", "arrow"), "≥": ("geq", "greater than or equal")}

def swap_symbols(xhtml):
    def fix_text(m):
        txt = m.group(1)
        for ch, (name, alt) in SYMBOLS.items():
            if ch in txt:
                txt = txt.replace(ch, f'<img class="sym" src="images/sym-{name}.png" alt="{alt}"/>')
                images.append(f"sym-{name}.png")
        return ">" + txt + "<"
    return re.sub(r">([^<]*)<", fix_text, xhtml)

for n, t, _, body in chapters:
    b = xhtml_body(kobo_screens(n, swap_svgs(n, body)) if IMG_DIR else body)
    if IMG_DIR:
        b = swap_symbols(b)
    b = re.sub(r'href="#chapter-(\d+)"', r'href="chapter-\1.xhtml"', b)
    files[f"chapter-{n}.xhtml"] = (xpage(t, f'<section epub:type="chapter" class="chapter">{b}</section>'), "svg" if "<svg" in b else "")
files["about.xhtml"] = (xpage("About this book", f'<section class="front"><h2>About this book</h2>{xhtml_body(DECL_HTML)}{xhtml_body(LICENSE_NOTE)}</section>'), "")
lic = html.escape(read(SRC / "LICENSE.txt"))
files["license.xhtml"] = (xpage("License", f'<section class="front"><h2>GNU General Public License v3</h2><pre style="white-space:pre-wrap;font-size:.7em">{lic}</pre></section>'), "")

EINK_CSS = """
body { margin: 0 .3em; }
/* Device screens: black on white with a solid frame, readable on grayscale e-ink */
.device-view { background: #fff !important; color: #000 !important; border: 2px solid #000;
  border-radius: 0; padding: .7em; font-size: .85em; font-family: 'Courier New', Courier, monospace;
  line-height: 1.35; margin: 1.1em 0; page-break-inside: avoid; }
.device-view p { text-align: left; }
.device-view h3 { margin-top: 0; }
.device-view table { border-collapse: collapse; margin: .4em auto; width: 100%; }
.device-view th, .device-view td { padding: .3em .45em; vertical-align: top; }
.device-view h3, .device-view th, .device-view td, .device-view .spk, .device-view b { color: #000 !important; }
.device-view th { background: #ddd !important; }
.device-view th, .device-view td { border: 1px solid #000 !important; }
.device-view div { border-color: #000 !important; }
.spk { color: inherit; }
img.eink { display: block; margin: .6em auto; max-width: 100%; height: auto; }
table { border-collapse: collapse; border: 1px solid #000; }
th, td { border: 1px solid #000; }
.keyframes img { page-break-inside: avoid; margin: .4em auto; }
img.screen { width: 100%; margin: 1em auto; }
/* No light text anywhere on e-ink: datelines and separators in black / dark gray */
body { color: #000; }
.dateline .txt, .dateline .place, .dateline .date, .dateline.scene-break .txt { color: #000; }
.dateline .sep, .dateline.scene-break::before, hr::after { color: #333; }
img.sym { display: inline; height: 1.34em; width: auto; vertical-align: -0.26em; margin: 0; }
.btn { display: inline-block; border: 1px solid #000; padding: .15em .7em; margin: .2em .2em .2em 0;
  font-family: sans-serif; font-size: .9em; background: #eee; }
.caption { text-indent: 0; text-align: center; font-style: italic; font-size: .85em; margin-top: .4em; }
"""

COLOR_CSS = """
/* Color edition: screens keep a navy frame and pale-blue panel; inline hues carry the colors */
.device-view { border-color: #1d3557; }
.device-view:not([style*="background"]) { background: #f2f6fc !important; }
.device-view th { background: #dbe5f3 !important; }
.device-view th, .device-view td { border: 1px solid #1d3557 !important; }
.device-view h3 { color: #1d3557 !important; }
.btn { background: #e3eaf5; border-color: #1d3557; }
"""
if COLOR:  # let inline hues win in screens and dialogue
    EINK_CSS = EINK_CSS.replace(
        ".device-view h3, .device-view th, .device-view td, .device-view .spk, .device-view b { color: #000 !important; }",
        ".device-view { color: #000; }").replace(".spk { color: inherit; }", "").replace(
        ".device-view { background: #fff !important; color: #000 !important;", ".device-view { color: #000;") + COLOR_CSS
    TITLE_EPUB = f"{TITLE} (Color Edition)"
    uid += "-color"
else:
    TITLE_EPUB = TITLE

nav_items = "\n".join(f'<li><a href="chapter-{n}.xhtml">{html.escape(t)}</a></li>' for n, t, _, _ in chapters)
nav = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><title>Contents</title><link rel="stylesheet" type="text/css" href="book.css"/></head>
<body><nav epub:type="toc" id="toc"><h2>Contents</h2><ol class="toc">
<li><a href="title.xhtml">Title page</a></li>
{nav_items}
<li><a href="about.xhtml">About this book</a></li>
<li><a href="license.xhtml">License</a></li></ol></nav>
<nav epub:type="landmarks" hidden=""><ol><li><a epub:type="bodymatter" href="chapter-1.xhtml">Start</a></li><li><a epub:type="toc" href="nav.xhtml">Contents</a></li></ol></nav>
</body></html>"""

order = ["title.xhtml", "nav.xhtml"] + [f"chapter-{n}.xhtml" for n in range(1, N + 1)] + ["about.xhtml", "license.xhtml"]
manifest = ['<item id="css" href="book.css" media-type="text/css"/>',
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>']
for name, (_, props) in files.items():
    pid = name.replace(".xhtml", "").replace("-", "_")
    p = f' properties="{props}"' if props else ""
    manifest.append(f'<item id="{pid}" href="{name}" media-type="application/xhtml+xml"{p}/>')
for f in sorted(set(images)):
    manifest.append(f'<item id="img_{f[:-4].replace("-", "_")}" href="images/{f}" media-type="image/png"/>')
spine = "\n".join(f'<itemref idref="{x.replace(".xhtml", "").replace("-", "_")}"/>' for x in order)
opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{uid}</dc:identifier><dc:title>{TITLE_EPUB}</dc:title><dc:creator>{AUTHOR}</dc:creator>
<dc:language>en</dc:language><dc:rights>GNU General Public License v3</dc:rights><dc:source>{SOURCE_URL}</dc:source>
<meta property="dcterms:modified">{now}</meta></metadata>
<manifest>{chr(10).join(manifest)}</manifest>
<spine toc="ncx">{spine}</spine></package>"""
ncx_points = "\n".join(
    f'<navPoint id="np{n}" playOrder="{n}"><navLabel><text>{html.escape(t)}</text></navLabel><content src="chapter-{n}.xhtml"/></navPoint>'
    for n, t, _, _ in chapters)
ncx = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{uid}"/></head>
<docTitle><text>{TITLE_EPUB}</text></docTitle><navMap>{ncx_points}</navMap></ncx>"""

epub = OUT / ("snowmoon-color.epub" if COLOR else "snowmoon.epub")
with zipfile.ZipFile(epub, "w") as z:
    z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    def w(name, data):
        z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
    w("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
    w("OEBPS/content.opf", opf); w("OEBPS/toc.ncx", ncx); w("OEBPS/nav.xhtml", nav)
    # Drop the dark-screen rules (light-blue ink on navy) rather than relying on overrides Kobo may ignore
    epub_css = re.sub(r"(?m)^\.device-view[^{]*\{[^}]*\}\n?", "", BOOK_CSS)
    epub_css = epub_css.replace(".spk { color: var(--spk-lt); }", "")
    w("OEBPS/book.css", epub_css + EINK_CSS)
    for f in sorted(set(images)):
        z.write(IMG_DIR / f, f"OEBPS/images/{f}")
    for name, (content, _) in files.items():
        w(f"OEBPS/{name}", content)

print("chapters:", len(chapters))
print("titles:", [c[1] for c in chapters][:3], "...")
