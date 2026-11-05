// Renders scripts/one-sheet/one-sheet.html to files/misc/arvind-karunakaran-speaker-one-sheet.pdf
// (US Letter, one page) and a PNG preview next to the source (preview is not published).
//
// Needs puppeteer-core and @sparticuz/chromium on NODE_PATH:
//   npm install @sparticuz/chromium@131 puppeteer-core@23   (in any scratch folder)
//   NODE_PATH=<that folder>/node_modules node scripts/one-sheet/render.js
const path = require('path');
const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');

const here = __dirname;
const root = path.resolve(here, '..', '..');
const src = 'file://' + path.join(here, 'one-sheet.html');
const pdfOut = path.join(root, 'files', 'misc', 'arvind-karunakaran-speaker-one-sheet.pdf');
const pngOut = path.join(here, 'preview.png');

(async () => {
  const browser = await puppeteer.launch({
    args: chromium.args,
    executablePath: await chromium.executablePath(),
    headless: true,
    defaultViewport: { width: 816, height: 1056, deviceScaleFactor: 2 },
  });
  const page = await browser.newPage();
  await page.goto(src, { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  // Fail loudly if the content no longer fits on one page.
  const overflow = await page.evaluate(() => {
    const s = document.querySelector('.sheet');
    const body = document.querySelector('.body');
    const foot = document.querySelector('.foot');
    const last = body.lastElementChild.getBoundingClientRect().bottom;
    return { gap: foot.getBoundingClientRect().top - last, scroll: s.scrollHeight - s.clientHeight };
  });
  console.log('space above footer (px):', Math.round(overflow.gap), ' overflow (px):', overflow.scroll);
  await page.screenshot({ path: pngOut });
  await page.pdf({ path: pdfOut, width: '8.5in', height: '11in', printBackground: true, pageRanges: '1' });
  await browser.close();
  console.log('wrote', pdfOut);
  if (overflow.gap < 6 || overflow.scroll > 0) { console.error('ERROR: content does not fit on one page'); process.exit(1); }
})().catch((e) => { console.error(e); process.exit(1); });
