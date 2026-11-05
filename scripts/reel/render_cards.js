// Renders every cards/*.html (1920x1080) to cards/*.png. Files named overlay-*.html are rendered
// with a transparent background (for compositing over video); the rest are full-frame cards.
// NODE_PATH=<node_modules with puppeteer-core and @sparticuz/chromium> node scripts/reel/render_cards.js <cards_dir>
const fs = require('fs');
const path = require('path');
const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');
(async () => {
  const dir = path.resolve(process.argv[2]);
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.html')).sort();
  const browser = await puppeteer.launch({ args: chromium.args, executablePath: await chromium.executablePath(), headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  for (const f of files) {
    await page.goto('file://' + path.join(dir, f), { waitUntil: 'networkidle0' });
    await page.evaluate(() => document.fonts.ready);
    const out = path.join(dir, f.replace(/\.html$/, '.png'));
    await page.screenshot({ path: out, omitBackground: f.startsWith('overlay-') });
    console.log('rendered', path.basename(out));
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
