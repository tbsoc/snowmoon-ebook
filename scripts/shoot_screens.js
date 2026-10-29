// Screenshot EPUB-styled device screens marked data-raster (pass-1 build) at e-reader width.
const puppeteer = require('puppeteer-core');
const { pathToFileURL } = require('url');
const fs = require('fs');
const [, , oebps, outDir] = process.argv;
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const p = await b.newPage();
  await p.setViewport({ width: 536, height: 900, deviceScaleFactor: 3 });
  const manifest = {};
  for (let n = 1; n <= 32; n++) {
    await p.goto(pathToFileURL(`${oebps}/chapter-${n}.xhtml`).href, { waitUntil: 'load' });
    const count = await p.$$eval('[data-raster]', els => els.length);
    if (!count) continue;
    manifest[n] = [];
    for (let k = 0; k < count; k++) {
      const el = await p.$(`[data-raster="${k}"]`);
      await el.evaluate(e => { e.style.margin = '0'; });
      const file = `screen-ch${n}-${k}.png`;
      await el.screenshot({ path: `${outDir}/${file}` });
      manifest[n].push({ file });
    }
  }
  fs.writeFileSync(`${outDir}/screens.json`, JSON.stringify(manifest, null, 1));
  await b.close();
})();
