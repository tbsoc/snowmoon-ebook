// Screenshot every top-level SVG in each chapter's body (excluding nav icons) on the device-view background.
const puppeteer = require('puppeteer-core');
const { pathToFileURL } = require('url');
const fs = require('fs');
const [, , srcDir, outDir, mode] = process.argv;
const COLOR = mode === 'color';  // color edition: only chapter 8's vote ring is re-drawn (final colors, white paper)
fs.mkdirSync(outDir, { recursive: true });
(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true,
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 900, height: 1200, deviceScaleFactor: 3 });
  const manifest = {};
  for (let n = 1; n <= 32; n++) {
    if (COLOR && n !== 8) continue;
    await page.goto(pathToFileURL(`${srcDir}/chapter-${n}.html`).href, { waitUntil: 'load' });
    const count = await page.evaluate((n, COLOR) => {
      document.documentElement.classList.remove('dark');
      const svgs = [...document.querySelectorAll('.document-page svg')]
        .filter(s => !s.closest('nav') && !s.parentElement.closest('svg'));
      const NS = 'http://www.w3.org/2000/svg';
      const INK = '#eaf4ff';  // light here -> near-black after eink.py inverts dark-background images
      const LIGHT_BG = { 2: [0, 1], 4: [0], 14: [4] };  // already dark-on-light; eink.py leaves these as-is
      const mk = (tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };
      svgs.forEach((s, i) => {
        s.setAttribute('data-shot', i);
        s.style.background = '#0a0e27';
        if (n === 8 && COLOR) {
          // Same filled/hollow coding, in real green and red on white paper
          const G = '#2e7d32', R = '#c62828', FRAME = '#1d3557';
          s.style.background = '#fff';
          s.querySelector('rect').setAttribute('fill', '#fff');
          s.querySelectorAll('circle').forEach(c => {
            const f = c.getAttribute('fill');
            const highlighted = c.getAttribute('stroke') === '#cef';
            if (f === '#6c6') { c.setAttribute('fill', G); c.setAttribute('stroke', G); }
            if (f === '#f66') { c.setAttribute('fill', '#fff'); c.setAttribute('stroke', R); c.setAttribute('stroke-width', '2.5'); }
            if (highlighted) s.appendChild(mk('circle', { cx: c.getAttribute('cx'), cy: c.getAttribute('cy'), r: 13, fill: 'none', stroke: FRAME, 'stroke-width': 1.5 }));
          });
          s.querySelectorAll('text').forEach(t => t.setAttribute('fill', '#000'));
          s.setAttribute('viewBox', '0 0 200 224'); s.setAttribute('height', '224');
          s.querySelector('rect').setAttribute('height', '224');
          s.appendChild(mk('circle', { cx: 62, cy: 210, r: 6, fill: G, stroke: G }));
          s.appendChild(mk('text', { x: 72, y: 214, 'font-family': 'sans-serif', 'font-size': 12, fill: '#000' })).textContent = 'green';
          s.appendChild(mk('circle', { cx: 118, cy: 210, r: 6, fill: '#fff', stroke: R, 'stroke-width': 2.5 }));
          s.appendChild(mk('text', { x: 128, y: 214, 'font-family': 'sans-serif', 'font-size': 12, fill: '#000' })).textContent = 'red';
          return;
        }
        if (n === 8) {
          // Vote ring: green/red are indistinguishable in grayscale -> filled vs hollow, plus a legend
          s.querySelectorAll('circle').forEach(c => {
            const f = c.getAttribute('fill');
            const highlighted = c.getAttribute('stroke') === '#cef';
            if (f === '#6c6') { c.setAttribute('fill', INK); c.setAttribute('stroke', INK); }
            if (f === '#f66') { c.setAttribute('fill', '#245'); c.setAttribute('stroke', INK); c.setAttribute('stroke-width', '2'); }
            if (highlighted) s.appendChild(mk('circle', { cx: c.getAttribute('cx'), cy: c.getAttribute('cy'), r: 13, fill: 'none', stroke: INK, 'stroke-width': 1.5 }));
          });
          s.setAttribute('viewBox', '0 0 200 224'); s.setAttribute('height', '224');
          s.querySelector('rect').setAttribute('height', '224');
          s.appendChild(mk('circle', { cx: 62, cy: 210, r: 6, fill: INK, stroke: INK }));
          s.appendChild(mk('text', { x: 72, y: 214, 'font-family': 'sans-serif', 'font-size': 12 })).textContent = 'green';
          s.appendChild(mk('circle', { cx: 118, cy: 210, r: 6, fill: '#245', stroke: INK, 'stroke-width': 2 }));
          s.appendChild(mk('text', { x: 128, y: 214, 'font-family': 'sans-serif', 'font-size': 12 })).textContent = 'red';
        }
        if (n === 6 && i === 0) {
          // Keeper cohorts are told apart only by color (orange/teal/blue), which grayscale erases:
          // this year = filled circle, last year = hollow ring, second-last year = filled diamond
          // (color edition keeps each cohort's original hue on top of the shape coding)
          s.querySelectorAll('circle').forEach(c => {
            const f = c.getAttribute('fill');
            const cx = +c.getAttribute('cx'), cy = +c.getAttribute('cy'), r = +c.getAttribute('r');
            if (f === '#fa5') { const k = COLOR ? f : INK; c.setAttribute('fill', k); c.setAttribute('stroke', k); }
            if (f === '#4cb') { c.setAttribute('fill', '#245'); c.setAttribute('stroke', COLOR ? f : INK); c.setAttribute('stroke-width', '1.8'); c.setAttribute('r', r - 0.6); }
            if (f === '#6af') {
              const d = r * 1.55;
              c.replaceWith(mk('rect', { x: cx - d / 2, y: cy - d / 2, width: d, height: d, fill: COLOR ? f : INK,
                transform: `rotate(45 ${cx} ${cy})` }));
            }
          });
        }
        // Shapes filled with the screen's mid-blue vanish once that blue becomes paper white: outline them
        s.querySelectorAll('polygon[fill="#348"]').forEach(p => { p.setAttribute('stroke', INK); p.setAttribute('stroke-width', '2'); });
        if (!(LIGHT_BG[n] || []).includes(i)) {
          // One ink color for all labels, with a halo so they read over any fill
          s.querySelectorAll('text, tspan').forEach(t => {
            t.style.setProperty('fill', INK, 'important');
            t.style.setProperty('stroke', '#0a0e27', 'important');
            t.style.setProperty('stroke-width', '0.22em', 'important');
            t.style.setProperty('stroke-linejoin', 'round', 'important');
            t.style.setProperty('paint-order', 'stroke', 'important');
          });
        }
      });
      return svgs.length;
    }, n, COLOR);
    manifest[n] = [];
    for (let i = 0; i < count; i++) {
      const el = await page.$(`svg[data-shot="${i}"]`);
      const box = await el.boundingBox();
      const file = `ch${n}-${i}.png`;
      await el.screenshot({ path: `${outDir}/${file}` });
      manifest[n].push({ file, w: Math.round(box.width), h: Math.round(box.height) });
    }
  }
  fs.writeFileSync(`${outDir}/manifest.json`, JSON.stringify(manifest, null, 1));
  await browser.close();
})();
