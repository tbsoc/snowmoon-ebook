"""Build guide.html (the spoiler-free reader's guide) from the template and data files.

usage: python build_guide.py <timeline_colors.json> <characters.json> <glossary.json> <out guide.html> [summaries dir]
Missing research files are treated as empty, so the layout can be previewed early.
Entries marked "spoiler_safe": false are dropped. Chapter summaries (summaries_*.json in the
summaries dir) contain spoilers; the page only inserts each one when the reader reveals it.
"""
import json, sys
from pathlib import Path

here = Path(__file__).resolve().parent
tl_path, chars_path, gloss_path, out = (Path(p) for p in sys.argv[1:5])
sum_dir = Path(sys.argv[5]) if len(sys.argv) > 5 else gloss_path.parent


def load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


tl, chars, gloss = load(tl_path), load(chars_path), load(gloss_path)
safe = lambda items: [x for x in items if x.get("spoiler_safe", True)]

data = {
    "timeline": tl["timeline"],
    # dialogue color per character, as used in the original (oklch); learned in speakers.py
    "voices": tl.get("colors", {}),
    "threadBlurbs": {
        "Veridia": "A lush, prosperous democracy that steers behaviour with taxes and subsidies instead of bans, "
                   "and treats privacy as a public good. Gladias's story is set mostly in its capital, Meldan.",
        "Dzego": "A nation that lost a war a century ago and is still pressured by the Arctic Empire. Its people "
                 "coordinate through anonymous networks and secret societies more than through their government. "
                 "Zei's story is set here.",
        "Freetown": "A city in the United Cities, home to economics researcher Jahn, where the book's two "
                    "storylines cross paths.",
    },
    "characters": sorted(safe(chars.get("characters", [])),
                         key=lambda c: (c.get("importance") != "main", c.get("first_chapter", 99))),
    "places": safe(chars.get("places_factions", [])),
    "glossary": sorted(safe(gloss.get("glossary", [])), key=lambda g: g["term"].lower()),
    "themes": gloss.get("themes", []),
    "hooks": gloss.get("opening_hooks", []),
    "summaries": sorted((c for f in sorted(sum_dir.glob("summaries_*.json"))
                         for c in load(f).get("chapters", []) if c.get("summary")),
                        key=lambda c: c["chapter"]),
}

# "</" can't appear inside a <script> block
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
html = (here / "guide_template.html").read_text(encoding="utf-8").replace("/*DATA*/", blob)
out.write_text(html, encoding="utf-8")
print(f"guide: {len(data['characters'])} characters, {len(data['places'])} places, "
      f"{len(data['glossary'])} terms, {len(data['themes'])} themes, {len(data['hooks'])} hooks, "
      f"{len(data['summaries'])} chapter summaries {sorted(c['chapter'] for c in data['summaries'])}")
