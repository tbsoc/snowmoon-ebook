"""Speaker labels for the black-and-white EPUB.

Snowmoon gives each character one dialogue color (span.spk with --spk-lt) and often leaves lines
untagged, so on grayscale screens multi-speaker exchanges lose their cue. This module learns which
color belongs to which character from lines the author does tag ("Gladias said"), then marks only
the lines where color was doing the work: untagged lines in exchanges with 3+ speakers, and the
spots in two-person exchanges where one speaker talks twice in a row. Anything it can't resolve
confidently stays unlabeled.
"""
import re
from collections import Counter, defaultdict
from bs4 import BeautifulSoup

VERBS = (r"said|says|asked|asks|replied|shouted|whispered|answered|added|continued|explained|exclaimed|"
         r"muttered|called|yelled|told|responded|interjected|wrote|typed|sighed|laughed|insisted|agreed|"
         r"protested|repeated|snapped|murmured|began|cried|joked|admitted|declared|demanded|suggested|"
         r"countered|pointed out|chimed in|cut in|went on|retorted|noted|observed|offered|remarked")
VERB_RE = re.compile(rf"\b({VERBS})\b", re.I)
NOT_NAMES = {"He", "She", "They", "It", "We", "You", "I", "The", "A", "An", "His", "Her", "Their", "But",
             "And", "Then", "When", "After", "Before", "As", "So", "Yes", "No", "Well", "Oh", "Okay", "This",
             "That", "There", "What", "Why", "How", "Who", "Just", "Even", "Still", "Now", "Here"}
NAME_VERB = re.compile(rf"\b([A-Z][a-z]{{2,}})\s+(?:{VERBS})\b")
VERB_NAME = re.compile(rf"\b(?:{VERBS})\s+([A-Z][a-z]{{2,}})\b")


def _key(span):
    m = re.search(r"--spk-lt:\s*([^;]+)", span.get("style", ""))
    return m.group(1).strip() if m else None


def _outside_text(p):
    """Text of the paragraph that is not inside a dialogue span (narration, tags)."""
    parts = []
    for c in p.children:
        if getattr(c, "name", None) == "span" and "spk" in (c.get("class") or []):
            continue
        parts.append(c.get_text() if hasattr(c, "get_text") else str(c))
    return "".join(parts)


def _dialogue_paras(wrapper):
    """Top-level paragraphs in reading order: (p, speaker key or None, outside text)."""
    out = []
    for p in wrapper.find_all("p", recursive=False):
        spans = p.find_all("span", class_="spk", recursive=False)
        keys = {_key(s) for s in spans} - {None}
        key = keys.pop() if len(keys) == 1 else None
        out.append((p, key if spans else None, _outside_text(p), bool(spans)))
    return out


GENERIC = re.compile(r"\b(?:another|a|an|one|other|each|every|some)\s+$", re.I)


def _tagged_names(text):
    """Names in speech tags ("Zei said", "asked Seila"); skips generic roles ("another Keeper replied")."""
    names = set()
    for rx in (NAME_VERB, VERB_NAME):
        for m in rx.finditer(text):
            name = m.group(1)
            if name in NOT_NAMES:
                continue
            if rx is NAME_VERB and GENERIC.search(text[:m.start(1)]):
                continue
            names.add(name)
    return names


def collect(chapters_html):
    """Gather evidence: which names the author's speech tags attach to each color, per chapter."""
    ev = {"per_ch": defaultdict(lambda: defaultdict(Counter)), "book": defaultdict(Counter),
          "keys": {}, "text": {}, "tagged": []}
    for n, body in chapters_html.items():
        w = BeautifulSoup(f"<div id='__w'>{body}</div>", "lxml").find(id="__w")
        paras = _dialogue_paras(w)
        ev["keys"][n] = {k for _, k, _, _ in paras if k}
        ev["text"][n] = w.get_text(" ")
        for p, key, outside, is_dlg in paras:
            if not key:
                continue
            names = _tagged_names(outside)
            if len(names) == 1:
                name = names.pop()
                ev["per_ch"][n][key][name] += 1
                ev["book"][key][name] += 1
                ev["tagged"].append((n, key, name))
    return ev


def decide(n, ev):
    """Confident {color key: name} for chapter n. A color is skipped whenever it is ambiguous there."""
    text = ev["text"][n]
    # colors are reused for different characters in different storylines, so a name only counts
    # in chapters where that character actually appears
    present = lambda name: len(re.findall(rf"\b{re.escape(name)}\b", text)) >= 2
    m = {}
    for key in ev["keys"][n]:
        ch, bk = ev["per_ch"][n][key], ev["book"][key]
        rivals = {nm for nm in bk if present(nm)}  # every character tied to this color who appears here
        if len(rivals) > 1 or len(ch) > 1:
            continue  # two characters here share this color: color can't tell them apart
        if ch:
            name, c = ch.most_common(1)[0]
            if c >= 2 or (bk and bk.most_common(1)[0][0] == name):
                m[key] = name
            continue
        if bk:
            name, c = bk.most_common(1)[0]
            if sum(bk.values()) >= 3 and c / sum(bk.values()) >= 0.9 and present(name):
                m[key] = name
    return m


def learn(chapters_html):
    """chapters_html: {n: body html}. Returns {n: {color key: name}} for confident matches."""
    ev = collect(chapters_html)
    return {n: decide(n, ev) for n in chapters_html}


def validate(chapters_html):
    """Leave-one-out on lines the author tagged: hide each tag, predict its speaker from color alone."""
    ev = collect(chapters_html)
    res = Counter()
    wrong = []
    for n, key, name in ev["tagged"]:
        ev["per_ch"][n][key][name] -= 1
        ev["book"][key][name] -= 1
        for cnt in (ev["per_ch"][n][key], ev["book"][key]):
            if cnt[name] <= 0:
                del cnt[name]
        pred = decide(n, ev).get(key)
        ev["per_ch"][n][key][name] += 1
        ev["book"][key][name] += 1
        if pred is None:
            res["no label"] += 1
        elif pred == name:
            res["correct"] += 1
        else:
            res["wrong"] += 1
            wrong.append((n, name, pred))
    return res, wrong


def label(body, cmap):
    """Insert speaker labels into a chapter body. Returns (html, stats)."""
    w = BeautifulSoup(f"<div id='__w'>{body}</div>", "lxml").find(id="__w")
    soup = w
    while soup.parent is not None:
        soup = soup.parent
    stats = Counter()
    run = []

    def flush():
        speakers = [k for _, k, _ in run]
        many = len(set(speakers)) >= 3
        after_repeat = False
        for i, (p, key, bare) in enumerate(run):
            repeat = i > 0 and speakers[i - 1] == key
            needs = bare and (many or repeat or after_repeat)
            after_repeat = repeat
            if not needs:
                continue
            name = cmap.get(key)
            if not name:
                stats["unresolved"] += 1
                continue
            tag = soup.new_tag("span")
            tag["class"] = "who"
            tag.string = name
            p.insert(0, " ")
            p.insert(0, tag)
            stats["labeled"] += 1
        run.clear()

    for p, key, outside, is_dlg in _dialogue_paras(w):
        if not is_dlg:
            if p.get_text(strip=True):
                flush()
            continue
        if not key:  # mixed-speaker paragraph: leave as written
            flush()
            continue
        bare = not (VERB_RE.search(outside) or _tagged_names(outside))
        run.append((p, key, bare))
    flush()
    return w.decode_contents(), stats
