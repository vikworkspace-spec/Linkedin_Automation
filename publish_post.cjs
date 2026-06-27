/**
 * publish_post.cjs — Schedule a LinkedIn post via Chrome CDP
 *
 * Full flow:
 *   1. Connect to Chrome on port 9222
 *   2. Find LinkedIn feed tab
 *   3. Click "Start a post" (mouse.click for React)
 *   4. Wait for editor, type text
 *   5. Click "Schedule post" (element.click via evaluate)
 *   6. Set time, click "Next", then "Schedule"
 *
 * Usage: node publish_post.cjs <file_path> [date] [time]
 *   date: MM/DD/YYYY (default: tomorrow)
 *   time: HH:MM AM/PM (default: 9:00 AM)
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');

function rand(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
const sleep = (min, max) => new Promise(r => setTimeout(r, rand(min || 50, max || 150)));

function getTomorrowDate() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return `${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getDate()).padStart(2,'0')}/${d.getFullYear()}`;
}

// ── Shadow DOM helpers ──

async function waitShadow(page, sel, timeout = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const found = await page.evaluate(s => {
      function f(r) { if (!r) return false; if (r.querySelector(s)) return true; const w = document.createTreeWalker(r, NodeFilter.SHOW_ELEMENT, null, false); let n; while ((n = w.nextNode())) { if (n.shadowRoot && f(n.shadowRoot)) return true; } return false; }
      return f(document.body);
    }, sel);
    if (found) return true;
    await sleep(100, 300);
  }
  return false;
}

// Mouse click by text (works with React on main DOM but not always in shadow)
async function mouseClickByText(page, text, timeout = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const coords = await page.evaluate(t => {
      function f(r) {
        if (!r) return null;
        for (const el of r.querySelectorAll('*')) {
          if ((el.innerText||'').trim() === t && ['BUTTON','SPAN','DIV','A'].includes(el.tagName) && el.offsetWidth > 0) {
            const rect = el.getBoundingClientRect();
            return { x: rect.x + rect.width/2, y: rect.y + rect.height/2 };
          }
        }
        const w = document.createTreeWalker(r, NodeFilter.SHOW_ELEMENT, null, false);
        let n;
        while ((n = w.nextNode())) { if (n.shadowRoot) { const res = f(n.shadowRoot); if (res) return res; } }
        return null;
      }
      return f(document.body);
    }, text);
    if (coords) { await page.mouse.click(coords.x, coords.y); return true; }
    await sleep(200, 500);
  }
  return false;
}

// Click an element in the shadow DOM by aria-label (using element.click())
async function shadowClickByAria(page, label, timeout = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const clicked = await page.evaluate(l => {
      function f(r) {
        if (!r) return false;
        for (const el of r.querySelectorAll('*')) {
          if (el.getAttribute('aria-label') === l && el.offsetWidth > 0) {
            el.click();
            return true;
          }
        }
        const w = document.createTreeWalker(r, NodeFilter.SHOW_ELEMENT, null, false);
        let n;
        while ((n = w.nextNode())) { if (n.shadowRoot && f(n.shadowRoot)) return true; }
        return false;
      }
      return f(document.body);
    }, label);
    if (clicked) return true;
    await sleep(200, 500);
  }
  return false;
}

// Click a button in shadow DOM by exact text (using element.click())
async function shadowClickByText(page, text, timeout = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const clicked = await page.evaluate(t => {
      function f(r) {
        if (!r) return false;
        for (const el of r.querySelectorAll('*')) {
          if ((el.innerText||'').trim() === t && ['BUTTON','SPAN','DIV','A'].includes(el.tagName) && el.offsetWidth > 0) {
            el.click();
            return true;
          }
        }
        const w = document.createTreeWalker(r, NodeFilter.SHOW_ELEMENT, null, false);
        let n;
        while ((n = w.nextNode())) { if (n.shadowRoot && f(n.shadowRoot)) return true; }
        return false;
      }
      return f(document.body);
    }, text);
    if (clicked) return true;
    await sleep(200, 500);
  }
  return false;
}

// Set a value on an input in shadow DOM by ID
async function shadowSetValue(page, id, value) {
  return page.evaluate(({id: i, value: v}) => {
    const io = document.getElementById('interop-outlet');
    if (!io || !io.shadowRoot) return false;
    const inp = io.shadowRoot.getElementById(i);
    if (!inp) return false;
    inp.focus();
    inp.value = '';
    inp.dispatchEvent(new Event('input', {bubbles: true}));
    inp.value = v;
    inp.dispatchEvent(new Event('input', {bubbles: true}));
    inp.dispatchEvent(new Event('change', {bubbles: true}));
    return true;
  }, {id, value});
}

// ── Main ──

async function main() {
  const filePath = process.argv[2];
  let targetDate = process.argv[3] || getTomorrowDate();
  let targetTime = process.argv[4] || '9:00 AM';

  if (!filePath) { console.error("Usage: node publish_post.cjs <file_path> [date] [time]"); process.exit(1); }
  const text = fs.readFileSync(filePath, 'utf8');

  console.log(`Connecting to Chrome port 9222...`);
  console.log(`Target schedule: ${targetDate} at ${targetTime}`);

  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' });
  const pages = await browser.pages();
  const page = pages.find(p => p.url().includes('linkedin.com/feed'));
  if (!page) { console.error("No LinkedIn feed tab"); process.exit(1); }

  await page.bringToFront();
  await page.setViewport({ width: 1280, height: 1200 });
  await sleep(1000, 2000);

  // Step 1: Click "Start a post"
  console.log("Clicking 'Start a post'...");
  if (!await mouseClickByText(page, "Start a post", 15000)) {
    console.error("Could not click Start a post");
    process.exit(1);
  }

  // Step 2: Wait for editor
  console.log("Waiting for editor...");
  if (!await waitShadow(page, '.ql-editor, [contenteditable="true"]', 20000)) {
    console.error("Editor did not open");
    process.exit(1);
  }
  await sleep(500, 1000);

  // Step 3: Focus and clear editor
  console.log("Focusing editor...");
  await page.evaluate(() => {
    function f(r) {
      if (!r) return false;
      const e = r.querySelector('.ql-editor, [contenteditable="true"]');
      if (e) { e.focus(); e.innerHTML = '<p><br></p>'; return true; }
      const w = document.createTreeWalker(r, NodeFilter.SHOW_ELEMENT, null, false);
      let n;
      while ((n = w.nextNode())) { if (n.shadowRoot && f(n.shadowRoot)) return true; }
      return false;
    }
    f(document.body);
  });
  await sleep(200, 400);

  // Step 4: Type text
  console.log("Typing text...");
  const paras = text.split('\n').filter(p => p.trim().length > 0);
  for (let i = 0; i < paras.length; i++) {
    await page.keyboard.type(paras[i], { delay: 5 });
    if (i < paras.length - 1) {
      await page.keyboard.press('Enter');
      await page.keyboard.press('Enter');
      await sleep(30, 100);
    }
  }
  await sleep(500, 1000);

  // Step 5: Click "Schedule post" (aria-label)
  console.log("Clicking 'Schedule post'...");
  if (!await shadowClickByAria(page, "Schedule post", 10000)) {
    console.error("Could not find Schedule post button");
    process.exit(1);
  }
  await sleep(1000, 2000);

  // Step 6: Set date
  console.log(`Setting date to ${targetDate}...`);
  if (await shadowSetValue(page, 'share-post__scheduled-date', targetDate)) {
    console.log("  Date set!");
  } else {
    console.log("  Date field not found (may already be set)");
  }
  await sleep(500, 1000);

  // Step 7: Set time
  console.log(`Setting time to ${targetTime}...`);
  if (await shadowSetValue(page, 'share-post__scheduled-time', targetTime)) {
    console.log("  Time set!");
  } else {
    console.log("  Time field not found");
  }
  await sleep(500, 1000);

  // Step 8: Click "Next"
  console.log("Clicking 'Next'...");
  if (!await shadowClickByText(page, "Next", 10000)) {
    console.error("Could not find Next button");
    process.exit(1);
  }
  await sleep(1000, 2000);

  // Step 9: Click "Schedule"
  console.log("Clicking 'Schedule'...");
  if (!await shadowClickByText(page, "Schedule", 10000)) {
    console.error("Could not find Schedule button");
    process.exit(1);
  }

  // Step 10: Wait for confirmation
  await sleep(2000, 4000);

  const stillOpen = await waitShadow(page, '.ql-editor, [contenteditable="true"]', 3000);
  console.log(stillOpen ? "Composer still open" : "Post scheduled successfully!");

  console.log("Done!");
  process.exit(0);
}

main().catch(err => { console.error("Fatal:", err.message); process.exit(1); });
