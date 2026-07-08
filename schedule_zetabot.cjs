/**
 * schedule_zetabot.cjs — Schedule posts on Zetabot AI company page
 *
 * Connects to Chrome on port 9222 (must be running with --remote-debugging-port=9222).
 * Supports text posts + media uploads (slideshow/infographic) with scheduling.
 * Incorporates human-like delays from anti_detection.js to avoid detection.
 *
 * Prerequisites:
 *   1. Chrome running: chrome.exe --remote-debugging-port=9222 --user-data-dir=%TEMP%\chrome-linkedin-bot
 *   2. Logged into LinkedIn on the Zetabot AI company page
 *   3. Node.js installed, puppeteer-core available
 *
 * Usage:
 *   node schedule_zetabot.cjs
 *
 * Reads approved posts from approved_for_publishing.json
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// ── Human-like timing ──
function rand(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
const sleep = (minMs, maxMs) => new Promise(r => setTimeout(r, rand(minMs, maxMs)));

// ── Posts to schedule ──
const approved = JSON.parse(fs.readFileSync(path.join(__dirname, 'approved_for_publishing.json'), 'utf8'));
const BASE = __dirname;
const slideDir = path.join(BASE, 'carousel-routine', 'output', new Date().toISOString().slice(0, 10), 'carousel-branded');

// Infographic full caption (from linkedin_posts_20260708.txt post #4)
const INFOGRAPHIC_TEXT = `The skills recruiters say are hardest to find right now, ranked by shortage severity.

GMAC surveyed corporate recruiters globally and found notable shortages across four categories that staffing firms are struggling to fill.

AI and machine learning capabilities top the list. Sixty seven percent of recruiters reported significant difficulty sourcing candidates with proven AI skills.

Grit and resilience came second at fifty eight percent. Companies want people who have built something through difficult conditions, not candidates who switched jobs every fourteen months chasing title bumps.

Emotional intelligence ranked third at fifty two percent. As AI handles more technical tasks, the premium on human judgment, client relationships, and team leadership is rising faster than anyone predicted.

Managing workers and people leadership closed the list at forty seven percent. Mid level managers who can hold a team together through rapid change are scarce because companies spent the last decade promoting individual contributors without teaching them how to lead.

The staffing firms with the deepest pipelines in these four categories are commanding retainers while everyone else fights over the same LinkedIn job postings.

Which of these four shortage areas is costing your firm the most revenue right now?

Follow for daily staffing insights.`;

// Parse poll from approved text, truncate options to 30 chars (LinkedIn limit)
const pollData = parsePoll(approved[2].text.trim());
pollData.options = pollData.options.map(o => o.length > 30 ? o.slice(0, 27) + '...' : o);
console.log('Poll parsed:');
console.log('  Question:', pollData.question);
console.log('  Options:', pollData.options.join(' | '));
console.log('  Caption preview:', pollData.caption.slice(0, 80) + '...');

// Strip "━━━ CAROUSEL PDF ━━━" header from carousel caption
const carouselText = approved[4].text.trim().replace(/^━+ CAROUSEL PDF ━+\s*/i, '').trim();
console.log('Carousel caption:', carouselText.slice(0, 80) + '...');

// approved array: [0]=INFOGRAPHIC header, [1]=Slide 07, [2]=Poll, [3]=INFOGRAPHIC header(dup), [4]=CAROUSEL caption, [5]=Recruiter laid off, [6]=CEOs fear, [7]=Poll(dup), [8]=Microsoft
const posts = [
  // Day 1 — text posts
  { type: 'text', label: 'Microsoft/Xbox', text: approved[8].text.trim(), date: '07/09/2026', time: '9:00 AM' },
  // Day 1 — poll (with real poll UI, options truncated to 30 chars)
  { type: 'poll',  label: 'Poll',          text: pollData.caption, pollQuestion: pollData.question, pollOptions: pollData.options, date: '07/09/2026', time: '12:00 PM' },
  // Day 1 — carousel slideshow (header stripped)
  { type: 'slideshow', label: 'Carousel', text: carouselText, slides: getSlides(slideDir), date: '07/09/2026', time: '3:00 PM' },
  // Day 1 — infographic (full caption + PNG)
  { type: 'media', label: 'Infographic', text: INFOGRAPHIC_TEXT, file: path.join(BASE, 'linkedin-infographic-20260708.png'), date: '07/09/2026', time: '6:00 PM' },
  // Day 2
  { type: 'text', label: 'CEOs fear AI',   text: approved[6].text.trim(), date: '07/10/2026', time: '9:00 AM' },
  { type: 'text', label: 'Recruiter rehire', text: approved[5].text.trim(), date: '07/10/2026', time: '12:00 PM' },
];

function getSlides(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter(f => /^slide-\d+\.png$/.test(f)).sort().map(f => path.join(dir, f));
}

// ── Poll parsing ──
function parsePoll(fullText) {
  const lines = fullText.split('\n');
  let questionIdx = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().endsWith('?')) { questionIdx = i; break; }
  }
  const optionIdxs = [];
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().startsWith('[ ]')) optionIdxs.push(i);
  }
  const question = questionIdx >= 0 ? lines[questionIdx].trim() : '';
  const options = optionIdxs.map(i => lines[i].replace(/^\[\s*\]\s*/, '').trim());
  let captionEnd = questionIdx >= 0 ? questionIdx : (optionIdxs.length > 0 ? optionIdxs[0] : lines.length);
  let afterOptionsStart = optionIdxs.length > 0 ? optionIdxs[optionIdxs.length - 1] + 1 : captionEnd;
  const captionBefore = lines.slice(0, captionEnd).join('\n').trim();
  const captionAfter = lines.slice(afterOptionsStart).join('\n').trim();
  const caption = [captionBefore, captionAfter].filter(Boolean).join('\n\n');
  return { question, options, caption };
}

// ── Poll attachment handler ──
async function handlePollAttachment(page, pollData) {
  console.log('  Creating poll...');
  // Click "More" button first to reveal "Create a poll"
  await sleep(500, 1200);
  await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(
      x => (x.getAttribute('aria-label') && x.getAttribute('aria-label').includes('More')) ||
           (x.innerText && x.innerText.includes('More'))
    );
    if (b) b.click();
  });
  await sleep(800, 1800);
  // Click "Create a poll"
  const pollClicked = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(
      x => (x.getAttribute('aria-label') && x.getAttribute('aria-label').includes('Create a poll')) ||
           (x.innerText && x.innerText.includes('Create a poll'))
    );
    if (b) { b.click(); return true; }
    return false;
  });
  if (!pollClicked) { console.log('  ERROR: Could not find "Create a poll" button'); return false; }
  await sleep(1000, 2500);
  // Fill poll question
  await page.evaluate((q) => {
    const sel = 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"], textarea[aria-label*="poll"], textarea[aria-label*="question"]';
    const el = document.querySelector(sel);
    if (el) { el.focus(); el.value = q; el.dispatchEvent(new Event('input', {bubbles:true})); }
  }, pollData.question);
  await sleep(500, 1000);
  // Fill poll options
  for (let oIdx = 0; oIdx < pollData.options.length; oIdx++) {
    await sleep(300, 800);
    if (oIdx >= 2) {
      await page.evaluate(() => {
        const b = [...document.querySelectorAll('button')].find(x => x.innerText && x.innerText.includes('Add option'));
        if (b) b.click();
      });
      await sleep(800, 1500);
    }
    const inputs = await getPollInputs(page);
    if (inputs.length <= oIdx) {
      console.log(`  ERROR: Could not find poll option input ${oIdx + 1}`);
      continue;
    }
    await inputs[oIdx].focus();
    await inputs[oIdx].type(pollData.options[oIdx], { delay: 30 });
    if (inputs[oIdx].dispose) await inputs[oIdx].dispose();
  }
  await sleep(500, 1200);
  // Click "Done" on poll creator
  console.log('  Finalizing poll...');
  await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => {
      const txt = x.innerText ? x.innerText.trim() : '';
      return txt === 'Done' && !x.disabled;
    });
    if (b) b.click();
  });
  await sleep(1000, 2500);
  return true;
}

// ── Get poll option inputs (handles shadow DOM) ──
async function getPollInputs(page) {
  const inputsHandle = await page.evaluateHandle(() => {
    function findInputs(root) {
      let found = [];
      const els = root.querySelectorAll('input[id*="poll-option"]');
      for (const el of els) found.push(el);
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.shadowRoot) found = found.concat(findInputs(node.shadowRoot));
      }
      return found;
    }
    return findInputs(document.body);
  });
  const properties = await inputsHandle.getProperties();
  const inputs = [];
  for (const property of properties.values()) {
    const el = property.asElement();
    if (el) inputs.push(el);
  }
  return inputs;
}

// ── Helpers ──
async function dismissAll(page) {
  // Close any open modals with variable retries
  for (let i = 0; i < 3; i++) {
    await page.keyboard.press('Escape');
    await sleep(400, 900);
  }
}

async function typeHuman(page, text) {
  // Type paragraph by paragraph with natural pauses
  // Target ONLY the post composer .ql-editor, not comment sections
  const lines = text.split('\n').filter(l => l.trim());
  for (let i = 0; i < lines.length; i++) {
    await page.evaluate((txt) => {
      // Find .ql-editor inside post creation area (not comment sections)
      // Post composer is inside a dialog/modal or share creation container
      const ed = document.querySelector('[role="dialog"] .ql-editor') ||
                 document.querySelector('.share-creation-state__container .ql-editor') ||
                 document.querySelector('.creator-share-preview .ql-editor') ||
                 document.querySelector('.article-editor .ql-editor');
      if (!ed) return;
      ed.focus();
      const p = document.createElement('p');
      p.textContent = txt;
      ed.appendChild(p);
      ed.dispatchEvent(new Event('input', { bubbles: true }));
    }, lines[i]);
    await sleep(200, 500);
    if (Math.random() < 0.1) await sleep(800, 2500);
  }
}

async function schedulePost(page, date, time) {
  await sleep(500, 1500); // Think time before scheduling
  
  // Click "Schedule post"
  await page.evaluate(() => {
    const btns = [...document.querySelectorAll('button')];
    const btn = btns.find(b => b.getAttribute('aria-label') === 'Schedule post' && !b.disabled);
    if (btn) btn.click();
  });
  await sleep(2000, 3500);
  
  // Set date
  await page.evaluate((d) => {
    const inp = document.querySelector('#share-post__scheduled-date');
    if (inp) { inp.value = d; inp.dispatchEvent(new Event('input', {bubbles:true})); }
  }, date);
  await sleep(300, 800);
  
  // Set time
  await page.evaluate((t) => {
    const inp = document.querySelector('#share-post__scheduled-time');
    if (inp) { inp.value = t; inp.dispatchEvent(new Event('input', {bubbles:true})); }
  }, time);
  await sleep(600, 1500);
  
  // Confirm: click Next then Schedule
  for (const btnText of ['Next', 'Schedule']) {
    await page.evaluate((txt) => {
      const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === txt && !x.disabled);
      if (b) b.click();
    }, btnText);
    await sleep(1500, 3500);
  }
}

// ── Main ──
(async () => {
  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' });
  const pages = await browser.pages();
  const page = pages.find(p => p.url().includes('linkedin.com/company/129764337'));
  if (!page) { console.log('ERROR: Zetabot AI page not found in Chrome tabs'); process.exit(1); }

  for (const post of posts) {
    console.log(`\n=== ${post.label} (${post.type}) ===`);
    console.log(`  Schedule: ${post.date} at ${post.time}`);

    await dismissAll(page);
    await sleep(1000, 2500); // Natural gap between posts

    if (post.type !== 'text') {
      // Already posted text posts — skip if this is text
    }

    // Click "Start a post" — robust selector matching other scripts
    const startClicked = await page.evaluate(() => {
      const el = [...document.querySelectorAll('*')].find(
        x => (x.tagName === 'BUTTON' || x.getAttribute('role') === 'button' || x.getAttribute('aria-label') === 'Start a post') &&
              x.innerText && x.innerText.trim().includes('Start a post')
      );
      if (el) { el.click(); return true; }
      return false;
    });
    if (!startClicked) { console.log('  ERROR: Could not find "Start a post" button'); continue; }
    console.log('  Clicked Start a post');
    await sleep(3000, 5000);

    // Handle slideshow
    if (post.type === 'slideshow' && post.slides && post.slides.length > 0) {
      // Click Add media
      await page.evaluate(() => {
        const b = [...document.querySelectorAll('button')].find(x => x.getAttribute('aria-label') === 'Add media');
        if (b) b.click();
      });
      await sleep(2000, 3000);
      
      // Upload all slides
      const fi = await page.$('input[type="file"]');
      if (fi) {
        await fi.uploadFile(...post.slides);
        console.log(`  Uploaded ${post.slides.length} slides`);
        
        // Wait for Next button
        for (let i = 0; i < 30; i++) {
          const ok = await page.evaluate(() => {
            const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Next');
            return b && !b.disabled;
          });
          if (ok) break;
          await sleep(1000, 2000);
        }
        
        // Click Next
        await page.evaluate(() => {
          const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Next' && !x.disabled);
          if (b) b.click();
        });
        await sleep(2000, 4000);
      }
    }

    // Handle poll
    if (post.type === 'poll') {
      const pollOk = await handlePollAttachment(page, { question: post.pollQuestion, options: post.pollOptions });
      if (!pollOk) { console.log('  Skipping poll post due to poll setup failure'); continue; }
    }

    // Handle single media
    if (post.type === 'media' && post.file) {
      await page.evaluate(() => {
        const b = [...document.querySelectorAll('button')].find(x => x.getAttribute('aria-label') === 'Add media');
        if (b) b.click();
      });
      await sleep(1500, 3000);
      
      const fi = await page.$('input[type="file"]');
      if (fi) {
        await fi.uploadFile(post.file);
        console.log('  Uploaded media');
        for (let i = 0; i < 20; i++) {
          const ok = await page.evaluate(() => {
            const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Next');
            return b && !b.disabled;
          });
          if (ok) break;
          await sleep(1000, 2000);
        }
        await page.evaluate(() => {
          const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Next' && !x.disabled);
          if (b) b.click();
        });
        await sleep(2000, 4000);
      }
    }

    // Type caption
    await typeHuman(page, post.text);
    console.log('  Typed caption');
    await sleep(1500, 3000); // Review before scheduling

    // Schedule
    await schedulePost(page, post.date, post.time);
    console.log(`  Scheduled for ${post.date} ${post.time}`);
  }

  console.log('\n=== ALL DONE ===');
  await browser.disconnect();
})();
