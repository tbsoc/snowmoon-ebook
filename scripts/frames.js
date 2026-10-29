const puppeteer = require('puppeteer-core');
const { pathToFileURL } = require('url');
const [, , file, outDir, times] = process.argv;
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const p = await b.newPage();
  await p.setViewport({ width: 900, height: 1200, deviceScaleFactor: 3 });
  await p.goto(pathToFileURL(file).href, { waitUntil: 'load' });
  const idx = await p.evaluate(() => {
    const svgs = [...document.querySelectorAll('.document-page svg')].filter(s => !s.closest('nav') && !s.parentElement.closest('svg'));
    const i = svgs.findIndex(s => s.querySelector('animate'));
    svgs[i].setAttribute('id', 'anim'); svgs[i].style.background = '#0a0e27';
    return i;
  });
  console.log('index', idx);
  for (const t of times.split(',').map(Number)) {
    await p.evaluate(t => { const s = document.getElementById('anim'); s.pauseAnimations(); s.setCurrentTime(t); }, t);
    await (await p.$('#anim')).screenshot({ path: `${outDir}/t${t.toFixed(2)}.png` });
  }
  await b.close();
})();
