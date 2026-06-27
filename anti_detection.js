/**
 * anti_detection.js — Human-like behavior primitives for browser automation
 *
 * Designed to make Puppeteer/agent-browser automation indistinguishable
 * from real human interaction. Every function introduces natural variance
 * in timing, movement, and interaction patterns.
 *
 * Core principles:
 *  - No fixed delays ever — every wait has a random range
 *  - Simulate mouse movement before clicks
 *  - Type with variable inter-key delays (bursty, human rhythm)
 *  - Intersperse "browsing" activity between automation actions
 *  - Avoid detectable DOM/DevTools signatures
 */

// ──────────────────────────────────────────────
//  NATURAL RANDOM UTILITIES
// ──────────────────────────────────────────────

/**
 * Return a random integer between min and max (inclusive).
 * Uses a truncated normal-like distribution for more natural timing
 * (values near the center are more likely than extremes).
 */
function randomBetween(min, max) {
  // Simple triangular distribution for more natural feel
  const u = Math.random();
  const v = Math.random();
  // Box-Muller gives normal-ish distribution around the midpoint
  const normal = Math.sqrt(-2 * Math.log(u + 0.0001)) * Math.cos(2 * Math.PI * v);
  const mid = (min + max) / 2;
  const range = (max - min) / 2;
  let val = mid + normal * (range / 3); // σ ≈ range/3 so 99.7% within range
  return Math.round(Math.max(min, Math.min(max, val)));
}

/**
 * Sleep for a random duration with normal-ish distribution.
 * @param {number} minMs - Minimum delay in milliseconds
 * @param {number} maxMs - Maximum delay in milliseconds
 */
function sleep(minMs, maxMs) {
  const delay = randomBetween(minMs, maxMs);
  return new Promise(resolve => setTimeout(resolve, delay));
}

/**
 * Occasionally introduce a much longer pause (like a user getting distracted,
 * reading something, or alt-tabbing). ~5-15% chance depending on weight.
 * @param {number} weight - Probability weight (0-1), default 0.08 (8%)
 */
async function occasionalLongPause(weight = 0.08) {
  if (Math.random() < weight) {
    await sleep(4000, 12000);
  }
}

/**
 * Sleep mimicking "think time" – a pause before a user decides what to do next.
 * Varies based on complexity of next action.
 * @param {'simple'|'moderate'|'complex'} actionType
 */
async function thinkTime(actionType = 'moderate') {
  const ranges = {
    simple: [400, 1200],
    moderate: [800, 2500],
    complex: [1500, 4000],
  };
  const [min, max] = ranges[actionType] || ranges.moderate;
  await sleep(min, max);
}

// ──────────────────────────────────────────────
//  HUMAN-LIKE TYPING
// ──────────────────────────────────────────────

/**
 * Type text with human-like characteristics:
 *  - Variable inter-key delay (30-180ms per keystroke)
 *  - Burstiness: first few chars faster, then occasional pauses
 *  - Longer pauses at punctuation marks (. ! ? , —)
 *  - Occasional "mistype" correction pattern (backspace then retype)
 *  - Variable speed between words
 *
 * @param {import('puppeteer-core').Page} page
 * @param {string} text - The full text to type
 * @param {object} [opts]
 * @param {number} [opts.baseSpeed] - Base typing speed multiplier (1 = normal, 0.5 = faster, 2 = slower)
 */
async function humanType(page, text, opts = {}) {
  const baseSpeed = opts.baseSpeed || 1;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    // Determine inter-key delay
    let delay;
    if (i === 0) {
      // First character: a bit of hesitation before starting
      delay = randomBetween(200, 600) * baseSpeed;
    } else if (char === '.' || char === '!' || char === '?' || char === '\n') {
      // Pause at end of sentence/line
      delay = randomBetween(250, 700) * baseSpeed;
      // After the char, a longer pause (user reads what they wrote)
      await page.keyboard.type(char);
      await sleep(300, 900);
      continue;
    } else if (char === ',' || char === ';' || char === '—') {
      delay = randomBetween(120, 350) * baseSpeed;
    } else if (char === ' ') {
      // Slight pause between words
      delay = randomBetween(40, 180) * baseSpeed;
    } else if (i > 0 && text[i - 1] === ' ' && i < text.length - 3) {
      // First char of a word: slightly faster
      delay = randomBetween(30, 100) * baseSpeed;
    } else {
      // Regular character: variable speed
      delay = randomBetween(20, 120) * baseSpeed;
    }

    await page.keyboard.type(char);
    await sleep(delay, delay + randomBetween(10, 60));

    // Occasionally introduce a longer mid-sentence pause (~3-7% of chars)
    if (Math.random() < 0.04) {
      await sleep(400, 1500);
    }
  }

  // Pause after finishing typing (reviewing what was written)
  await sleep(400, 1500);
}

/**
 * Type text paragraph-by-paragraph with natural pauses between paragraphs.
 * More realistic than typing the entire blob at once.
 */
async function humanTypeByParagraph(page, text) {
  const paragraphs = text.split('\n').filter(p => p.trim().length > 0);
  for (let i = 0; i < paragraphs.length; i++) {
    await humanType(page, paragraphs[i]);
    if (i < paragraphs.length - 1) {
      await page.keyboard.press('Enter');
      await page.keyboard.press('Enter');
      await sleep(300, 1000); // Pause between paragraphs
    }
  }
}

// ──────────────────────────────────────────────
//  HUMAN MOUSE MOVEMENT
// ──────────────────────────────────────────────

/**
 * Simulate a natural mouse movement from current cursor position to
 * the center of a target element. Uses a bezier-like curve with
 * slight overshoot for realism.
 *
 * @param {import('puppeteer-core').Page} page
 * @param {import('puppeteer-core').ElementHandle} element
 * @param {object} [opts]
 * @param {number} [opts.steps] - Number of movement steps (default: random 15-30)
 */
async function humanMouseMove(page, element, opts = {}) {
  const steps = opts.steps || randomBetween(12, 28);
  const box = await element.boundingBox();
  if (!box) return;

  const targetX = box.x + box.width / 2 + randomBetween(-5, 5);
  const targetY = box.y + box.height / 2 + randomBetween(-5, 5);

  // Get current mouse position (or start from a reasonable default)
  const startPos = await page.evaluate(() => {
    // Some browsers expose this; fallback to a random corner position
    return { x: window.mouseX || randomBetween(0, 400), y: window.mouseY || randomBetween(0, 300) };
  });

  const startX = startPos.x;
  const startY = startPos.y;

  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    // Quadratic bezier with slight randomness
    const cp1x = startX + (targetX - startX) * 0.3 + randomBetween(-30, 30);
    const cp1y = startY + (targetY - startY) * 0.2 + randomBetween(-20, 20);
    const cp2x = startX + (targetX - startX) * 0.7 + randomBetween(-30, 30);
    const cp2y = startY + (targetY - startY) * 0.8 + randomBetween(-20, 20);

    const mt = 1 - t;
    const x = mt * mt * mt * startX + 3 * mt * mt * t * cp1x + 3 * mt * t * t * cp2x + t * t * t * targetX;
    const y = mt * mt * mt * startY + 3 * mt * mt * t * cp1y + 3 * mt * t * t * cp2y + t * t * t * targetY;

    await page.mouse.move(x, y);
    // Variable delay between movement steps (faster in middle, slower at start/end)
    const stepDelay = (i < 3 || i > steps - 3) ? randomBetween(15, 40) : randomBetween(5, 20);
    await new Promise(r => setTimeout(r, stepDelay));
  }
}

/**
 * Move mouse to a random position on the page (like a user idly moving cursor).
 */
async function randomMouseMovement(page) {
  const viewport = page.viewport() || { width: 1280, height: 1200 };
  const x = randomBetween(50, viewport.width - 50);
  const y = randomBetween(50, viewport.height - 50);
  const steps = randomBetween(8, 18);
  for (let i = 0; i < steps; i++) {
    const progress = (i + 1) / steps;
    const cx = 50 + (x - 50) * progress + randomBetween(-20, 20);
    const cy = 50 + (y - 50) * progress + randomBetween(-20, 20);
    await page.mouse.move(cx, cy);
    await new Promise(r => setTimeout(r, randomBetween(10, 30)));
  }
}

/**
 * Click an element like a human: move mouse to it, pause, click.
 * Falls back gracefully if element isn't found.
 *
 * @param {import('puppeteer-core').Page} page
 * @param {Function} finderFn - Function to locate element (receives root node)
 * @param {object} [opts]
 * @param {boolean} [opts.doubleClick] - Whether to double-click
 */
async function humanClick(page, finderFn, opts = {}) {
  // Small random delay before starting to look (user's eyes find the button)
  await thinkTime('simple');

  // First, find the element using the same shadow-DOM-traversal pattern
  // but with random retry intervals instead of fixed polling
  let element = null;
  const maxAttempts = 3;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const handle = await page.evaluateHandle((finder) => {
      const fn = new Function('return ' + finder)();
      function findInShadow(root) {
        if (!root) return null;
        const res = fn(root);
        if (res) return res;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
        let node;
        while ((node = walker.nextNode())) {
          if (node.shadowRoot) {
            const found = findInShadow(node.shadowRoot);
            if (found) return found;
          }
        }
        return null;
      }
      return findInShadow(document.body);
    }, finderFn.toString());

    element = handle.asElement();
    if (element) break;
    if (attempt < maxAttempts - 1) {
      await sleep(400, 1200); // Variable retry interval
    }
  }

  if (!element) return false;

  // Move mouse to element
  await humanMouseMove(page, element);

  // Brief hover pause
  await sleep(100, 400);

  // Click using human-like sequence
  try {
    await page.evaluate(el => {
      el.focus();
      el.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
    }, element);
    await sleep(100, 300);

    if (opts.doubleClick) {
      await page.mouse.click(
        (await element.boundingBox()).x + (await element.boundingBox()).width / 2,
        (await element.boundingBox()).y + (await element.boundingBox()).height / 2,
        { clickCount: 2 }
      );
    } else {
      await element.click();
    }
  } catch (err) {
    // Fallback: dispatch events directly
    await page.evaluate(el => {
      const rect = el.getBoundingClientRect();
      const x = rect.left + rect.width / 2;
      const y = rect.top + rect.height / 2;
      el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
      el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
      el.focus();
      el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
      el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
      el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
    }, element);
  }

  await element.dispose();
  return true;
}

/**
 * Try to click an element, retrying with variable intervals.
 */
async function humanClickRetry(page, finderFn, timeoutMs = 12000, opts = {}) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    const clicked = await humanClick(page, finderFn, opts);
    if (clicked) return true;
    await sleep(800, 2000);
  }
  return false;
}

// ──────────────────────────────────────────────
//  VIEWPORT & SCROLL BEHAVIOR
// ──────────────────────────────────────────────

/**
 * Set viewport with slight randomization to avoid perfect consistency.
 */
async function randomizeViewport(page) {
  const baseWidth = 1280;
  const baseHeight = 1200;
  const width = baseWidth + randomBetween(-20, 20);
  const height = baseHeight + randomBetween(-30, 30);
  await page.setViewport({ width, height });
}

/**
 * Scroll down the page naturally — in small bursts with pauses,
 * occasionally stopping to "read."
 */
async function humanScroll(page, distancePx = null) {
  const maxScroll = distancePx || randomBetween(300, 1500);
  let scrolled = 0;
  while (scrolled < maxScroll) {
    const scrollAmount = randomBetween(80, 350);
    await page.evaluate((amount) => {
      window.scrollBy({ top: amount, behavior: 'smooth' });
    }, scrollAmount);
    scrolled += scrollAmount;
    // Pause between scroll bursts
    await sleep(400, 1800);
    // Occasionally stop to "read" (longer pause)
    if (Math.random() < 0.25) {
      await sleep(2000, 5000);
    }
  }
}

/**
 * Simulate a user browsing the feed between posts.
 * Scrolls, pauses to "read" posts, maybe hovers over links.
 */
async function browseFeed(page) {
  const scrollDistance = randomBetween(800, 3000);
  await humanScroll(page, scrollDistance);
  // Pause to "read"
  await sleep(2000, 6000);
  // Maybe scroll back up a bit (user scanning)
  const scrollUp = randomBetween(100, 500);
  await page.evaluate((amount) => {
    window.scrollBy({ top: -amount, behavior: 'smooth' });
  }, scrollUp);
  await sleep(500, 1500);
}

// ──────────────────────────────────────────────
//  NATURAL WAITING & TIMING
// ──────────────────────────────────────────────

/**
 * Wait for a DOM element to appear, with natural polling jitter
 * instead of fixed interval polling.
 */
async function waitForElement(page, selector, timeoutMs = 15000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    const el = await getElementShadow(page, selector);
    if (el) {
      await el.dispose();
      return true;
    }
    // Random polling interval (200-900ms) instead of fixed 500ms
    await sleep(200, 900);
  }
  throw new Error(`Timeout (${timeoutMs}ms) waiting for selector: ${selector}`);
}

// Shadow DOM helper (shared, but with variable polling)
async function getElementShadow(page, selector) {
  const handle = await page.evaluateHandle((sel) => {
    function findEl(root) {
      if (!root) return null;
      const el = root.querySelector(sel);
      if (el) return el;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.shadowRoot) {
          const found = findEl(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return findEl(document.body);
  }, selector);
  return handle.asElement();
}

// ──────────────────────────────────────────────
//  SESSION MANAGEMENT
// ──────────────────────────────────────────────

/**
 * Between scheduling posts, perform "human" activities:
 *  - Browse the feed
 *  - Random mouse movements
 *  - Variable-length pauses
 *  - Occasional longer breaks (like the user stepped away)
 */
async function betweenPostsActivity(page) {
  // 60% chance of scrolling the feed
  if (Math.random() < 0.6) {
    await browseFeed(page);
  } else {
    await randomMouseMovement(page);
    await sleep(1500, 4000);
  }

  // 15% chance of a "break" (user alt-tabbed, got coffee, etc.)
  if (Math.random() < 0.15) {
    await sleep(8000, 25000);
  }
}

/**
 * Between batches of posts (e.g., between days), take a longer break.
 */
async function betweenBatchesActivity(page) {
  await browseFeed(page);
  await sleep(5000, 12000);
  // Check notifications area (user behavior)
  await randomMouseMovement(page);
  await sleep(2000, 5000);
}

// ──────────────────────────────────────────────
//  SAFER ERROR HANDLING
// ──────────────────────────────────────────────

/**
 * Close the composer modal gracefully (like a human — click dismiss/close).
 * Avoids injecting CSS to hide overlays.
 */
async function closeComposer(page) {
  // Try clicking the "Dismiss" button (X icon) in the composer
  const clicked = await humanClick(page, (root) => {
    return Array.from(root.querySelectorAll('button')).find(b => {
      const label = b.getAttribute('aria-label') || '';
      const txt = b.innerText || '';
      return label.includes('Dismiss') || txt.includes('Dismiss') || label.toLowerCase() === 'close';
    });
  });

  if (clicked) {
    await sleep(500, 1500);
    // If a "Discard" confirmation appears (unsaved changes), click it
    await humanClick(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(b => {
        const txt = b.innerText ? b.innerText.trim() : '';
        return txt === 'Discard';
      });
    });
    await sleep(500, 1500);
  }
}

/**
 * Attempt to gracefully handle messaging overlays by clicking their close button
 * instead of injecting CSS to remove them.
 */
async function closeMessagingOverlays(page) {
  // Try to close message overlays by clicking their close buttons
  const closed = await humanClick(page, (root) => {
    return Array.from(root.querySelectorAll('button, [role="button"]')).find(b => {
      const label = b.getAttribute('aria-label') || '';
      const txt = b.innerText || '';
      return (label.includes('Close') || label.includes('close') || txt.includes('Close')) &&
             (label.includes('message') || label.includes('Message') ||
              b.closest && (b.closest('[class*="msg-overlay"]') || b.closest('[class*="msg"]')));
    });
  });
  if (closed) {
    await sleep(300, 800);
  }
}

// ──────────────────────────────────────────────
//  EXPORTS
// ──────────────────────────────────────────────

module.exports = {
  // Timing
  sleep,
  randomBetween,
  occasionalLongPause,
  thinkTime,

  // Typing
  humanType,
  humanTypeByParagraph,

  // Mouse
  humanMouseMove,
  randomMouseMovement,
  humanClick,
  humanClickRetry,

  // Viewport & Scroll
  randomizeViewport,
  humanScroll,
  browseFeed,

  // Waiting
  waitForElement,
  getElementShadow,

  // Session
  betweenPostsActivity,
  betweenBatchesActivity,

  // Overlays
  closeComposer,
  closeMessagingOverlays,
};
