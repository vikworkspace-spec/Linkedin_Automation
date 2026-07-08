// compile_pdf_win.js - Compile carousel PNGs to PDF using system Chrome
const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

(async () => {
  const dateStr = new Date().toISOString().slice(0, 10);
  const pngDir = path.join(__dirname, 'output', dateStr, 'carousel-branded');
  const pdfPath = path.join(pngDir, 'carousel.pdf');

  const pngs = fs.readdirSync(pngDir).filter(f => /^slide-\d+\.png$/.test(f)).sort();
  if (pngs.length === 0) { console.error('No PNGs found'); process.exit(1); }
  console.log(`Found ${pngs.length} PNGs, compiling to PDF...`);

  let html = '<html><body style="margin:0;padding:0;">';
  for (const png of pngs) {
    const fileUrl = `file:///${path.join(pngDir, png).replace(/\\/g, '/')}`;
    html += `<img src="${fileUrl}" style="width:1080px;height:1080px;display:block;page-break-after:always;">`;
  }
  html += '</body></html>';

  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--allow-file-access-from-files']
  });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.pdf({ path: pdfPath, width: '1080px', height: '1080px', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  console.log(`PDF saved: ${pdfPath}`);
  await browser.close();
})();
