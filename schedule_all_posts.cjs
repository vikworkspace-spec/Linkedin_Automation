/**
 * schedule_all_posts.cjs — Schedules LinkedIn posts with human-like behavior
 *
 * Uses anti_detection.js for all timing, typing, mouse movement, and
 * browsing patterns. No fixed delays, no injected CSS, no hard exits.
 *
 * Prerequisites: agent-browser running with LinkedIn logged in.
 */

const pup = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const H = require('./anti_detection.js');





// ──────────────────────────────────────────────
//  POST DATA — 11 posts across 3 days
// ──────────────────────────────────────────────










const posts = [
  // ===== DAY 1 =====
  {
    id: 1, type: 'carousel',
    date: '06/27/2026', time: '9:00 AM',
    caption: `Spending weeks building an idea without validation leads to wasted time. Successful founders check demand, supply, and saturation before writing code. Autocomplete searches and shopping trends offer free, reliable indicators of buying intent.

How do you validate a new product idea before building?

Follow @zetabotai for more.`,









    assetPath: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/linkedin-carousel-2026-06-12.pdf',
    title: 'The validation mistake that kills startups'
  },
  {
    id: 2, type: 'infographic',
    date: '06/27/2026', time: '12:00 PM',
    caption: `Mistral is rumored to be raising a new funding round at a twenty billion dollar valuation. This is nearly double its series C valuation from last year. The rapid rise of European AI model developers highlights how fast capital is shifting to compete with US firms.

What is the biggest hurdle for new AI firms raising capital at high valuations?

Follow @zetabotai for more data.`,








    assetPath: '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads/linkedin-infographic.png'
  },
  {
    id: 3, type: 'regular',
    date: '06/27/2026', time: '3:00 PM',
    caption: `A silent crisis is happening across the startup community that nobody discusses on social media feeds. The founders who are actually struggling the most stay completely silent.


They carry the weight of failing metrics, cash runway issues, and operational bottlenecks alone. They cannot share their fears online because their team, their investors, and their competitors are all watching.


Building a closed circle of three peer founders who share no overlap in markets provides a safe release.



How do solo founders build a safe support network that does not compromise their business reputation?

Follow @zetabotai for more insights.`







  },
  {
    id: 4, type: 'poll',
    date: '06/27/2026', time: '6:00 PM',
    caption: `Most businesses copy what everyone else is doing, and very few are willing to step into uncharted territory. Innovation suffers when founders focus entirely on immediate cash pressure.


When teams operate from a stress mindset, they replicate existing models and try to win a price war. Shifting from a transaction focus to an emotional design focus reveals gaps that competitors ignore.





Share a story of how your team breaks out of copycat cycles in the comments.`,



    title: 'What is the biggest barrier to innovation in early stage startups?',
    pollOptionsStr: 'Pure money panic mindset|Slow execution by teams|Fear of competitor copycats|Lack of customer feedback'
  },








  // ===== DAY 2 =====
  {
    id: 5, type: 'regular',
    date: '06/28/2026', time: '9:00 AM',
    caption: `A new video generation tool is targeting regional markets by lowering production costs to a fraction of a cent. Distilled video models are making high quality content accessible for local businesses.

Small business owners struggle to afford expensive commercial video generation. Standard tools cost too much for businesses operating at regional scale.





Will ultra cheap video tools help small local shops compete with national brands?

Follow @zetabotai for more tools.`







  },
  {
    id: 6, type: 'regular',
    date: '06/28/2026', time: '12:00 PM',
    caption: `Major funding rounds are reshaping the technology sector this week. Physical AI, space systems, and model developers are securing billions from public and private investors.



Focus on the largest movements. Mistral is raising three billion euros. Jeff Bezos is backing physical AI with a twelve billion dollar round. SpaceX officially priced its shares for its public market entry.


Which of these massive funding rounds will have the biggest long term impact?`
  },
  {
    id: 7, type: 'regular',
    date: '06/28/2026', time: '3:00 PM',
    caption: `A physical AI company just raised twelve billion dollars to automate heavy engineering tasks. The goal is to build a system that acts as a general engineer for the physical world and medicine design.
















Heavy industries and drug developers can automate designs in weeks instead of years, lowering the cost of physical innovation.



How soon will physical AI systems run manufacturing plants without human supervision?

Follow @zetabotai for more breakdowns.`







  },
  {
    id: 8, type: 'regular',
    date: '06/28/2026', time: '6:00 PM',
    caption: `Generating video content at half a cent per second is a massive advantage for bootstrapped startups. Distilled video models are removing the financial barrier to visual marketing.





Solo founders can run video ad campaigns, test different messages, and find product market fit without software debt.

What is your preferred budget-friendly tool for creating startup marketing videos?

Follow @zetabotai for more advantages.`
    },








  // ===== DAY 3 =====
  {
    id: 9, type: 'regular',
    date: '06/29/2026', time: '9:00 AM',
    caption: `The rise of factory robots that do not specialize in single tasks is shifting manufacturing roles. Reconfigurable machines are changing how physical production is managed.







Will general purpose robots bring manufacturing back to local communities?

Save this post to reference hardware trends.`







  },
  {
    id: 10, type: 'regular',
    date: '06/29/2026', time: '12:00 PM',
    caption: `The upcoming public market listings for massive space and AI firms is a stress test for private valuations. The era of high private markups without public scrutiny is ending.







Will public market listings lower the inflated valuations of private AI firms?

Follow @zetabotai for more takes.`







  },
  {
    id: 11, type: 'regular',
    date: '06/29/2026', time: '3:00 PM',
    caption: `Use this three-step prompt workflow to validate your startup ideas using search autocomplete data:





"Act as a market researcher. Analyze this startup idea: [Insert Idea].
1. Identify 5 autocomplete search terms related to this idea.
2. List 3 niche variations that target a specific audience.
3. Outline the search interest trend for these variations."





Save this prompt to use on your next idea.`


  }
];

  const screenshotDir = '/Users/prithal/3d website/linkedin-automation-routine/slack_downloads';

// ──────────────────────────────────────────────
//  CORE SCHEDULING LOGIC
// ──────────────────────────────────────────────

(async () => {
  try {

    console.log('🔍 Locating active browser session...');
    const tmpDir = os.tmpdir();



    const chromeDirs = fs.readdirSync(tmpDir).filter(name => name.startsWith('agent-browser-chrome-'));
    if (chromeDirs.length === 0) {
      throw new Error('No agent-browser-chrome directories found. Launch agent-browser with LinkedIn logged in first.');
    }





    const latestDir = chromeDirs
      .map(name => ({ path: path.join(tmpDir, name), mtime: fs.statSync(path.join(tmpDir, name)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime)[0].path;

    const portFile = path.join(latestDir, 'DevToolsActivePort');




    const port = fs.readFileSync(portFile, 'utf8').split('\n')[0].trim();
    console.log(`🔗 Connecting to browser on port ${port}...`);

    const browser = await pup.connect({ browserURL: `http://127.0.0.1:${port}` });
    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('linkedin.com'));

    if (!page) {

      console.error('❌ No LinkedIn page found. Make sure LinkedIn is open in agent-browser.');
      process.exit(1);
    }

    await page.bringToFront();

    await H.randomizeViewport(page);




    // Navigate to feed to start clean
    console.log('📱 Navigating to LinkedIn feed...');
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 20000 })
      .catch(e => console.log('Navigation note:', e.message.substring(0, 60)));






    // Let the page settle and "browse" a bit
    await H.sleep(2000, 4000);
    await H.browseFeed(page);







    console.log(`\n${'='.repeat(56)}`);
    console.log(`  SCHEDULING ${posts.length} POSTS (4/day × 3 days)`);
    console.log(`${'='.repeat(56)}\n`);

    for (let pIdx = 0; pIdx < posts.length; pIdx++) {
      const post = posts[pIdx];
      const isDayBoundary = pIdx > 0 && pIdx % 4 === 0;

      console.log(`\n${'─'.repeat(46)}`);
      console.log(`  Post ${post.id}/${posts.length} (${post.type}) — ${post.date} at ${post.time}`);
      console.log(`${'─'.repeat(46)}`);

      // ── Between batches (day boundaries): longer break ──
      if (isDayBoundary) {
        console.log('  📅 Day boundary — taking a natural break...');
        await H.betweenBatchesActivity(page);
        // "Check notifications"
        await H.humanClick(page, (root) => {
          const btns = Array.from(root.querySelectorAll('a, button, [role="button"]'));
          return btns.find(el => {
            const label = el.getAttribute('aria-label') || '';
            return label.includes('Notifications') || label.includes('notifications');
          });
        }).catch(() => {});
        await H.sleep(2000, 5000);
        // Navigate back to feed
        await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 20000 })
          .catch(() => {});
        await H.sleep(2000, 4000);
      }
















      // ── Between individual posts: browse feed ──
      if (pIdx > 0 && !isDayBoundary) {
        await H.betweenPostsActivity(page);
      }
































      // ── Close any lingering composer ──
      await H.closeComposer(page);
      // Try to close messaging overlays naturally
      const overlayClosed = await H.humanClick(page, (root) => {
        return Array.from(root.querySelectorAll('button, [role="button"]')).find(b => {
          const label = b.getAttribute('aria-label') || '';
          return label.includes('Close') || label.includes('close') || label.includes('Dismiss');
        });
      }).catch(() => false);
      if (overlayClosed) await H.sleep(500, 1200);



      // ── Click "Start a post" ──
      console.log('  ✏️ Opening composer...');
      const startPostClicked = await H.humanClickRetry(page, (root) => {
        return Array.from(root.querySelectorAll('*')).find(
          el => (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || el.getAttribute('aria-label') === 'Start a post') &&
                el.innerText && el.innerText.trim().includes('Start a post')
        );


      }, 15000);




      if (!startPostClicked) {
        throw new Error('Could not find/click "Start a post" button after retries');
      }










      await H.waitForElement(page, '.ql-editor, [contenteditable="true"]', 15000);
      await H.sleep(800, 2000);























































































































      // ── Handle attachments (poll / carousel / infographic) ──
      if (post.type === 'poll') {
        await handlePollAttachment(page, post);
      } else if (post.type === 'carousel') {



























































































        await handleCarouselAttachment(page, post);
      } else if (post.type === 'infographic') {















































        await handleInfographicAttachment(page, post);
      }






      // ── Type the caption ──
      console.log('  📝 Typing caption...');
      await H.waitForElement(page, '.ql-editor, [contenteditable="true"]', 15000);
      const editorEl = await H.getElementShadow(page, '.ql-editor, [contenteditable="true"]');








      if (editorEl) {
        await editorEl.focus();















        // Clear existing content using innerHTML (avoids document.execCommand)
        await page.evaluate(el => {
          el.innerHTML = '<p><br></p>';
        }, editorEl);
        await H.sleep(200, 500);





















        await editorEl.dispose();
      }


      // Type naturally paragraph by paragraph
      await H.humanTypeByParagraph(page, post.caption);




      // Review what was typed
      await H.sleep(800, 2000);

      // ── Open Schedule settings ──
      console.log('  🕐 Opening schedule settings...');
      const scheduleIconClicked = await H.humanClickRetry(page, (root) => {
        const modal = root.querySelector('.share-box, .artdeco-modal, [role="dialog"]');
        const container = modal || root;
        const buttons = Array.from(container.querySelectorAll('button'));
        const postBtn = buttons.find(b => b.innerText && b.innerText.trim() === 'Post');
        if (postBtn && postBtn.previousElementSibling) {
          return postBtn.previousElementSibling;
        }




        return buttons.find(b => {
          const label = b.getAttribute('aria-label') || '';
          return label.includes('Schedule');
        });
      }, 10000);








      if (!scheduleIconClicked) {
        throw new Error('Could not find/click Schedule icon');
      }

      await H.sleep(1000, 2500);


      // ── Set date and time ──
      console.log(`  📅 Setting date: ${post.date}, time: ${post.time}`);
      await fillDateField(page, post.date);
      await H.sleep(500, 1500);
      await fillTimeField(page, post.time);




      await H.sleep(800, 1800);

      // ── Click "Next" ──
      console.log('  ➡️ Clicking Next...');
      const nextClicked = await H.humanClickRetry(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Next'
        );



      }, 10000);


      if (!nextClicked) {
        throw new Error('Could not click Next in schedule modal');
      }
      await H.sleep(1500, 3500);




      // ── Click final "Schedule" button ──
      console.log('  ✅ Clicking Schedule...');
      const scheduleClicked = await H.humanClickRetry(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(
          b => b.innerText && b.innerText.trim() === 'Schedule'
        );





      }, 10000);

      if (!scheduleClicked) {
        throw new Error('Could not find/click final Schedule button');
      }

      // Wait for the composer to close (3-8 seconds, variable)
      console.log('  ⏳ Waiting for confirmation...');
      await H.sleep(3000, 7000);

      // Verify composer closed
      const isClosed = await page.evaluate(() => {
        function findEl(root, sel) {
          if (!root) return null;
          const el = root.querySelector(sel);
          if (el) return el;
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
          let node;

          while ((node = walker.nextNode())) {
            if (node.shadowRoot) {
              const found = findEl(node.shadowRoot, sel);
              if (found) return found;
            }
          }
          return null;
        }

        return !findEl(document.body, '.ql-editor, [contenteditable="true"]');
      });




      if (!isClosed) {
        console.log('  ⚠️ Composer still open, trying to dismiss...');
        await H.closeComposer(page);
      }

      console.log(`  ✅ Post ${post.id} scheduled successfully!`);
    }









    console.log(`\n${'='.repeat(56)}`);
    console.log(`  ✅ ALL ${posts.length} POSTS SCHEDULED`);
    console.log(`${'='.repeat(56)}`);
    console.log('\n  Summary:');
    console.log('  Day 1: Carousel 9AM, Infographic 12PM, Article 3PM, Poll 6PM');
    console.log('  Day 2: AI News × 4 (9AM, 12PM, 3PM, 6PM)');
    console.log('  Day 3: AI News × 3 (9AM, 12PM, 3PM)');

  } catch (err) {

    console.error('\n❌ Error:', err.message);

    // Try to capture an error screenshot if possible
    try {
      const tmpDir = os.tmpdir();












      const chromeDirs = fs.readdirSync(tmpDir).filter(name => name.startsWith('agent-browser-chrome-'));
      if (chromeDirs.length > 0) {
        const latestDir = chromeDirs
          .map(name => ({ path: path.join(tmpDir, name), mtime: fs.statSync(path.join(tmpDir, name)).mtimeMs }))
          .sort((a, b) => b.mtime - a.mtime)[0].path;
        const port = fs.readFileSync(path.join(latestDir, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
        const errBrowser = await pup.connect({ browserURL: `http://127.0.0.1:${port}` });
        const errPage = (await errBrowser.pages()).find(p => p.url().includes('linkedin.com'));
        if (errPage) {


          await errPage.screenshot({ path: path.join(screenshotDir || __dirname, 'error_screenshot.png') });
          console.log('  📸 Error screenshot saved.');
        }
      }



    } catch (_) { /* silent */ }

    process.exit(1);
  }
})();

// ──────────────────────────────────────────────
//  ATTACHMENT HANDLERS
// ──────────────────────────────────────────────

async function handlePollAttachment(page, post) {
  console.log('  📊 Setting up poll...');

  // Click "More" button first (if visible)
  await H.thinkTime('simple');
  const moreClicked = await H.humanClick(page, (root) => {
    return Array.from(root.querySelectorAll('button')).find(
      b => (b.getAttribute('aria-label') && b.getAttribute('aria-label').includes('More')) ||
           (b.innerText && b.innerText.includes('More'))
    );
  });
  if (moreClicked) await H.sleep(800, 1800);

  // Click "Create a poll"
  await H.thinkTime('moderate');
  const pollClicked = await H.humanClickRetry(page, (root) => {
    return Array.from(root.querySelectorAll('button')).find(
      b => (b.getAttribute('aria-label') && b.getAttribute('aria-label').includes('Create a poll')) ||
           (b.innerText && b.innerText.includes('Create a poll'))
    );
  }, 10000);

  if (!pollClicked) throw new Error('Could not find/click "Create a poll" button');
  await H.sleep(1000, 2500);

  // Fill the poll question
  await H.waitForElement(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]', 10000);
  const questionEl = await H.getElementShadow(page, 'textarea.polls-detour__question-field, textarea[placeholder*="commute"], textarea[id*="question"]');
  if (questionEl) {
    await questionEl.focus();
    await H.humanType(page, post.title);
    await questionEl.dispose();
  }

  const options = post.pollOptionsStr.split('|').map(o => o.trim());

  // Fill option inputs
  for (let oIdx = 0; oIdx < options.length; oIdx++) {
    await H.sleep(300, 800);

    if (oIdx >= 2) {
      // Click "Add option" for 3rd and 4th options
      await H.humanClick(page, (root) => {
        return Array.from(root.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Add option'));
      });
      await H.sleep(800, 1500);
    }

    // Find the poll option inputs
    const inputs = await getPollInputs(page);
    if (inputs.length <= oIdx) {
      throw new Error(`Could not find poll option input ${oIdx + 1}`);
    }

    await inputs[oIdx].focus();
    await H.humanType(page, options[oIdx]);
    await inputs[oIdx].dispose();
  }

  await H.sleep(500, 1200);

  // Click "Done" on poll creator
  console.log('  ✅ Finalizing poll...');
  const doneClicked = await H.humanClickRetry(page, (root) => {
    return Array.from(root.querySelectorAll('button')).find(b => {
      const txt = b.innerText ? b.innerText.trim() : '';
      const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0 ||
                        (b.ownerDocument && window.getComputedStyle(b).display !== 'none');
      const isDisabled = b.hasAttribute('disabled') || b.disabled;
      return txt === 'Done' && isVisible && !isDisabled;
    });
  }, 12000);

  if (!doneClicked) throw new Error('Could not click Done on Poll creator');
  await H.sleep(1000, 2500);
}

async function handleCarouselAttachment(page, post) {
  console.log('  📄 Uploading carousel document...');

  // Click "Add a document" (may need to expand More first)
  await H.thinkTime('moderate');
  let docClicked = await H.humanClick(page, (root) => {
    const btns = Array.from(root.querySelectorAll('button'));
    return btns.find(b =>
      (b.getAttribute('aria-label') && b.getAttribute('aria-label').includes('Add a document')) ||
      (b.innerText && b.innerText.includes('Add a document'))
    );
  });

  if (!docClicked) {
    // Try expanding More first
    await H.humanClick(page, (root) => {
      return Array.from(root.querySelectorAll('button')).find(
        b => (b.getAttribute('aria-label') && b.getAttribute('aria-label').includes('More')) ||
             (b.innerText && b.innerText.includes('More'))
      );
    });
    await H.sleep(800, 1800);

    docClicked = await H.humanClick(page, (root) => {
      const btns = Array.from(root.querySelectorAll('button'));
      return btns.find(b =>
        (b.getAttribute('aria-label') && b.getAttribute('aria-label').includes('Add a document')) ||
        (b.innerText && b.innerText.includes('Add a document'))
      );
    });
  }

  if (!docClicked) throw new Error('Could not find "Add a document" button');
  await H.sleep(1500, 3000);

  // Upload file via file input
  const fileInputHandle = await page.evaluateHandle(() => {
    function findFileInput(root) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.tagName === 'INPUT' && node.type === 'file') return node;
        if (node.shadowRoot) {
          const found = findFileInput(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return findFileInput(document.body);
  });

  const fileInput = fileInputHandle.asElement();
  if (!fileInput) throw new Error('Could not find file input element');
  await fileInput.uploadFile(post.assetPath);
  await fileInput.dispose();

  console.log('  📎 File uploaded, waiting for processing...');
  await H.sleep(3000, 6000);

  // Type document title
  await H.waitForElement(page, 'input.document-title-form__title-input, input[placeholder*="title to your document"]', 10000);
  const titleInput = await H.getElementShadow(page, 'input.document-title-form__title-input, input[placeholder*="title to your document"]');
  if (titleInput) {
    await titleInput.focus();
    await H.humanType(page, post.title);
    await titleInput.dispose();
  }

  await H.sleep(500, 1500);

  // Click "Done"
  console.log('  ✅ Finalizing document upload...');
  const doneClicked = await H.humanClickRetry(page, (root) => {
    return Array.from(root.querySelectorAll('button')).find(b => {
      const txt = b.innerText ? b.innerText.trim() : '';
      const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0 ||
                        window.getComputedStyle(b).display !== 'none';
      const isDisabled = b.hasAttribute('disabled') || b.disabled;
      return txt === 'Done' && isVisible && !isDisabled;
    });
  }, 12000);

  if (!doneClicked) throw new Error('Could not click Done on document uploader');
  await H.sleep(1500, 3500);
}

async function handleInfographicAttachment(page, post) {
  console.log('  🖼️ Uploading infographic image...');

  // Click "Add media" / "Photo"
  await H.thinkTime('moderate');
  const mediaClicked = await H.humanClick(page, (root) => {
    const btns = Array.from(root.querySelectorAll('button'));
    return btns.find(b =>
      (b.getAttribute('aria-label') && (b.getAttribute('aria-label').includes('Add media') || b.getAttribute('aria-label').includes('Photo'))) ||
      (b.innerText && (b.innerText.includes('Add media') || b.innerText.includes('Photo')))
    );
  });

  if (!mediaClicked) throw new Error('Could not find image upload button');
  await H.sleep(1500, 3000);

  // Upload file
  const fileInputHandle = await page.evaluateHandle(() => {
    function findFileInput(root) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.tagName === 'INPUT' && node.type === 'file') return node;
        if (node.shadowRoot) {
          const found = findFileInput(node.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    return findFileInput(document.body);
  });

  const fileInput = fileInputHandle.asElement();
  if (!fileInput) throw new Error('Could not find file input element');
  await fileInput.uploadFile(post.assetPath);
  await fileInput.dispose();

  console.log('  📎 Image uploaded, waiting for processing...');
  await H.sleep(3000, 6000);

  // Click "Next" or "Done" in image editor
  console.log('  ✅ Finalizing image...');
  const nextClicked = await H.humanClickRetry(page, (root) => {
    return Array.from(root.querySelectorAll('button')).find(b => {
      const txt = b.innerText ? b.innerText.trim() : '';
      const isMatch = txt === 'Next' || txt === 'Done';
      const isVisible = b.offsetWidth > 0 || b.offsetHeight > 0 ||
                        window.getComputedStyle(b).display !== 'none';
      const isDisabled = b.hasAttribute('disabled') || b.disabled;
      return isMatch && isVisible && !isDisabled;
    });
  }, 12000);

  if (!nextClicked) throw new Error('Could not click Next/Done in image editor');
  await H.sleep(1500, 3500);
}

// ──────────────────────────────────────────────
//  FIELD FILLING HELPERS
// ──────────────────────────────────────────────

async function fillDateField(page, dateValue) {
  const selector = 'input[placeholder*="Date"], input[aria-label*="date"], input[id*="date"]';
  const el = await H.getElementShadow(page, selector);
  if (!el) throw new Error('Could not find date field');

  await el.focus();
  await H.sleep(200, 500);
  await page.keyboard.press('Backspace');
  await H.sleep(200, 500);
  await H.sleep(300, 800);
  await H.humanType(page, dateValue);

  // Confirm date selection
  await page.keyboard.press('Enter');
  await H.sleep(200, 500);
  await page.keyboard.press('Escape');
  await H.sleep(200, 500);
  await page.keyboard.press('Tab');
  await el.dispose();
  await H.sleep(500, 1500);
}

async function fillTimeField(page, timeValue) {
  const selector = 'input[placeholder*="Time"], input[aria-label*="time"], input[id*="time"], input[role="combobox"]';
  const el = await H.getElementShadow(page, selector);
  if (!el) throw new Error('Could not find time field');

  await el.focus();
  await H.sleep(200, 500);
  await page.keyboard.press('Backspace');
  await H.sleep(200, 500);

  // Strip leading zero for combobox compatibility
  const normalizedTime = timeValue.startsWith('0') ? timeValue.substring(1) : timeValue;
  await H.humanType(page, normalizedTime);

  await H.sleep(1000, 2500);

  // Select from dropdown
  await page.keyboard.press('ArrowDown');
  await H.sleep(300, 800);
  await page.keyboard.press('Enter');
  await el.dispose();
  await H.sleep(500, 1500);
}

// ──────────────────────────────────────────────
//  POLL INPUT HELPER
// ──────────────────────────────────────────────

async function getPollInputs(page) {
  const inputsHandle = await page.evaluateHandle(() => {
    function findInputs(root) {
      let found = [];
      const els = root.querySelectorAll('input[id*="poll-option"]');
      for (const el of els) found.push(el);
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.shadowRoot) {
          found = found.concat(findInputs(node.shadowRoot));
        }
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
