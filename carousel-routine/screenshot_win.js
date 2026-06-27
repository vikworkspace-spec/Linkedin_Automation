const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const TEMP_DIR = path.join(__dirname, 'temp', 'carousel-branded');
const DATE_STR = new Date().toISOString().slice(0, 10);
const DATE = DATE_STR.replace(/-/g, '');
const OUTPUT_DIR = path.join(__dirname, 'output', DATE_STR, 'carousel-branded');

(async () => {
  // Create output directory
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  // Copy assets if they exist
  const srcAssets = path.join(TEMP_DIR, 'assets');
  const destAssets = path.join(OUTPUT_DIR, 'assets');
  if (fs.existsSync(srcAssets)) {
    fs.cpSync(srcAssets, destAssets, { recursive: true });
  }

  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files', '--disable-web-security'],
    protocolTimeout: 180000
  });

  // Screenshot carousel slides
  for (let i = 1; i <= 7; i++) {
    const slideNum = String(i).padStart(2, '0');
    const slidePath = path.join(TEMP_DIR, `slide-${slideNum}.html`);
    const outPath = path.join(OUTPUT_DIR, `slide-${slideNum}.png`);

    if (!fs.existsSync(slidePath)) {
      console.error(`✗ slide-${slideNum}.html not found at ${slidePath}`);
      continue;
    }

    const page = await browser.newPage();
    await page.setDefaultNavigationTimeout(60000);
    await page.setViewport({ width: 1080, height: 1080 });
    await page.goto(`file://${slidePath}`, { waitUntil: 'networkidle0', timeout: 30000 }).catch(() => 
      page.goto(`file://${slidePath}`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    );
    await new Promise(r => setTimeout(r, 2000));
    try {
      await page.screenshot({ 
        path: outPath, 
        clip: { x: 0, y: 0, width: 1080, height: 1080 }, 
        timeout: 60000 
      });
      console.log(`✓ slide-${slideNum}.png`);
    } catch (e) {
      console.error(`✗ slide-${slideNum}: ${e.message}`);
    }
    await page.close();
  }

  await browser.close();
  console.log('ALL_DONE');
})();
