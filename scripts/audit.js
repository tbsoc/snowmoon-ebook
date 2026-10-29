// Flag any rendered text in the EPUB chapters that is light or sits on a dark background.
const puppeteer = require('puppeteer-core');
const { pathToFileURL } = require('url');
const [, , oebps] = process.argv;
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const p = await b.newPage();
  await p.setViewport({ width: 536, height: 900 });
  let total = 0;
  for (let n = 1; n <= 32; n++) {
    await p.goto(pathToFileURL(`${oebps}/chapter-${n}.xhtml`).href, { waitUntil: 'load' });
    const flags = await p.evaluate(() => {
      const lum = c => {
        const m = c.match(/[\d.]+/g); if (!m) return null;
        const [r, g, bl, a = 1] = m.map(Number);
        if (a === 0) return null;
        return (0.2126 * r + 0.7152 * g + 0.0722 * bl) / 255;
      };
      const bgOf = el => {
        for (let e = el; e; e = e.parentElement) {
          const l = lum(getComputedStyle(e).backgroundColor);
          if (l !== null) return l;
        }
        return 1;
      };
      const out = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const t = walker.currentNode;
        if (!t.textContent.trim()) continue;
        const el = t.parentElement;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const fg = lum(cs.color), bg = bgOf(el);
        if (fg === null) continue;
        if (fg > 0.45 || bg < 0.6 || Math.abs(bg - fg) < 0.5)
          out.push({ tag: el.tagName, cls: el.className, color: cs.color, bg: bg.toFixed(2), sample: t.textContent.trim().length + ' chars' });
      }
      return out;
    });
    if (flags.length) { total += flags.length; console.log(`ch${n}`, JSON.stringify(flags.slice(0, 6))); }
  }
  console.log('total flagged text nodes:', total);
  await b.close();
})();
