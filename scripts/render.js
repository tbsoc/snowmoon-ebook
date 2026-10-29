const puppeteer = require('puppeteer-core');
const { pathToFileURL } = require('url');
const [, , input, output] = process.argv;
(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  const page = await browser.newPage();
  await page.goto(pathToFileURL(input).href, { waitUntil: 'load' });
  await page.pdf({
    path: output,
    preferCSSPageSize: true,
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;text-align:center;font-family:Georgia,serif;font-size:8pt;color:#777"><span class="pageNumber"></span></div>',
    outline: true,
    tagged: true,
  });
  await browser.close();
})();
