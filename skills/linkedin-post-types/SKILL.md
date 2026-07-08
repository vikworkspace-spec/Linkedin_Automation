---
name: linkedin-post-types
description: Single authoritative reference for generating every LinkedIn post format — Collaborative Article, Poll, Carousel (7-slide branded), Infographic (5 visual formats), and Multi-Image Post. Covers content selection, writing rules, hook rotation, visual format decision tree, design system, and output specs.
allowed-tools: WebSearch, WebFetch, Write, Read, Bash, Browser, ImageGeneration
---

# LinkedIn Post Type Reference

This file defines every post format the pipeline produces, with the rules, structure, and design system for each. An AI agent reading this one file has everything needed to generate any LinkedIn post type.

> **Content doctrine gate applies to every post.** The `content-doctrine.md` file is the north star and overrides any older topic guidance. Every topic must pass its **4-part topic filter (Reach, Stakes, Altitude, Edge)** and avoid its **DROP list** (technical tutorials, tool config, "steal this prompt" tactics, SaaS metrics, indie-hacker build-in-public / MVP / validation / agency tactics, dry news relay). We write for ambitious generalists who want to know where AI is going and how to get ahead, not for founders or engineers chasing tactics.

---

## 1. Universal Writing Rules (Apply to Every Post)

### Voice and Perspective
- Third-person observer voice. The author is a sharp, informed observer reporting on patterns, data, and shifts.
- No "I" statements anywhere.
- "We" is acceptable sparingly, when referring to the community reading the post.

### Human Realism (Human-like imperfections)
- Mimic casual human writing habits: occasionally miss a comma or omit a full stop at the end of a line.
- Incorporate natural, conversational slang or informal transitions where appropriate (e.g., "made cash faster than" instead of "generated revenue quicker than").
- Keep the style informal and conversational, avoiding overly polished, clinical sentence structures.

Good examples of the voice (AI-impact lane, broad audience — not founder tactics):
- "Most people using AI at work right now are making the same quiet mistake."
- "A thread on r/Futurology this week laid out something most people are not ready to hear about their jobs."
- "The people who got ahead with AI this year all did one specific thing differently."

### Post Structure (All Text Posts Must Follow This in Order)

1. **Hook** — 1 or 2 lines. Makes the reader stop scrolling. Grounded in a specific number, surprising finding, or pattern.
2. **Pain point** — Name the specific frustration. Concrete and recognisable, not abstract. Use the language real people use when complaining about this problem.
3. **Actionable value** — What to do about it. Specific enough to apply within 24 hours.
4. **Dream picture** — What changes once someone actually applies this. Make it tangible: more leads, less time wasted, a specific outcome.
5. **Engagement question** — One pointed question that is easy to answer in one sentence. Never "What do you think?" — make it specific.
6. **CTA** — One only. Follow, save, or repost. Never stack more than one.

### Hook Styles — Rotate Each Time

Pick the most fitting style for the topic:

| Style | Formula |
|-------|---------|
| **Curiosity** | "The way most solo entrepreneurs approach [topic] is exactly why they stay stuck at [problem]." |
| **Contrarian** | "Most people teaching [topic] online have never actually done it themselves." |
| **Transformation** | "[Metric] went from [low number] to [high number] in [time period]. Here is what actually moved it." |
| **Question** | "What separates the solo entrepreneurs who [succeed] from the ones still stuck at [problem] three years later?" |
| **Story** | "A founder posted something on Reddit this week about [topic] that reframes the whole conversation." |
| **Listicle** | "Five things nobody mentions before you start [topic]." |

### Banned Vocabulary — Never Use

delve, underscore, vibrant, tapestry, interplay, intricate, garner, pivotal, showcase, foster, align with, landscape (used abstractly), key (as a vague adjective), leverages, encompasses, facilitates, utilized, commenced, subsequent to, prior to, in order to, stands as, serves as, is a testament to, plays a vital role, plays a significant role, plays a crucial role, enduring legacy, lasting impact, indelible mark, it's important to note, it's worth noting, no discussion would be complete without, moreover, furthermore, in addition, setting the stage for, marking a shift, evolving landscape, reflects broader trends, game-changer, supercharge, real results, real strategy, real conversations

### Banned LinkedIn-Specific Patterns

- "No X. No Y. Just Z." triple-denial hooks
- "It's not just about X. It's about Y." reframes
- "If you're serious about X, [do this]" closes
- "And here's the kicker"
- "X changed everything"
- "Enter:" followed by a framework name
- "The best part? [short answer]"
- Email sign-off language ("To your success", "To your freedom")

### Banned Contrast Constructions

- "This isn't about X, it's about Y"
- "Not because of X. But because of Y."
- "Rather than X, do Y" (unless substantially expanded)
- "But rather" anywhere
- "Not just X, but also Y"
- "Not only X, but Y"

### Formatting Rules

- No em-dashes anywhere in any post
- Sentence case in all headings and slide labels (not Title Case)
- No bullet lists where flowing prose works better
- Specific numbers over adjectives: "grew 340% in 6 months" not "grew significantly"
- Varied sentence lengths deliberately — mix short punchy sentences with longer ones when the idea needs room
- One idea per paragraph
- Closing line lands on something new, never restates what came before
- No "-ing phrase" analysis tags: "highlighting the importance of", "underscoring its significance"
- No vague attributions like "experts say" or "many believe" without a named source

---

## 2. Collaborative Article

The most substantial post type. A complete thought piece grounded in a real discussion thread (Reddit, news story, or community conversation).

### Topic Selection
- Source: Reddit threads (r/artificial, r/ChatGPT, r/singularity, r/Futurology, r/technology, r/OpenAI)
- Must pass the content doctrine topic filter
- Reframe around AI's impact on work, income, skills, or the future
- Pick meaning and consequence, not mechanics

### Structure
```
━━━ COLLABORATIVE ARTICLE ━━━

[Complete thought piece, 1500 to 2000 characters. Sentence-case subheadings. 
Grounded in the Reddit thread or insight selected. Full 6-part post structure 
embedded as flowing prose — hook opens the piece, pain point follows, 
actionable value forms the body, dream picture closes the main section, 
engagement question precedes the CTA. Write this as a complete article a sharp 
observer in AI/business would be proud to publish under their name.]
```

### Quality Checklist
- [ ] 1500-2000 characters
- [ ] Grounded in a specific source thread
- [ ] 6-part structure embedded as flowing prose
- [ ] Sentence-case subheadings
- [ ] No "I" statements
- [ ] Passes content doctrine topic filter
- [ ] No banned vocabulary or patterns
- [ ] No em-dashes

---

## 3. Poll

A debate-starter designed to surface a genuinely contested question. The goal is high engagement through people wanting to explain their vote.

### Topic Selection
- Sourced from Reddit threads (different thread than the Collaborative Article)
- A future-of-work or AI-age dilemma people genuinely feel and split on
- No obvious right answer
- Not a factual question with a correct answer — must be opinion-based

### Structure
```
━━━ POLL ━━━

[2 to 3 sentence setup caption that establishes the debate without giving away 
a preferred answer]

[Poll question as a single standalone line]

☐ [Option A]
☐ [Option B]
☐ [Option C]
☐ [Option D]

[One short line below that invites people to explain their vote in the comments]
```

### Quality Checklist
- [ ] Setup caption is neutral — does not signal preferred answer
- [ ] 4 options with genuine tension between them
- [ ] No option is obviously wrong or obviously right
- [ ] Question fits in a single line
- [ ] Options are concise (1-5 words each)
- [ ] Passes content doctrine topic filter
- [ ] No banned vocabulary or patterns
- [ ] No em-dashes

---

## 4. Carousel

A 7-slide LinkedIn carousel (1080×1080 per slide) that tells a complete narrative arc. This is the most visually complex format.

### 4A. Format Selection (6 Formats)

Read `./skills/branded-carousel/FORMATS.md` for the full format reference. The six formats:

| Format | When to Use |
|--------|-------------|
| `BRAND_STORY` | Topic features a specific brand/product with imagery |
| `LISTICLE` | Numbered list like "5 ways", "7 tools" |
| `DATA_STORY` | Stats-driven, no specific brand |
| `HOW_THEY_DID_IT` | Marketing case study |
| `HOT_TAKE` | Contrarian opinion, myth-buster |
| `MYSTERY_REVEAL` | Curiosity hook, story-driven |

### 4B. Carousel Hook Style Selection (Mandatory)

Read `./carousel-hook-log.json` before picking a hook style. The log tracks which styles have been used recently.

Apply these rotation rules:
1. The style used in the **last run** is **banned** this run
2. If any style appears **3+ times in the last 7 entries**, it is also banned this run
3. Pick the most fitting non-banned style for the carousel topic
4. After generating the carousel, append an entry to `./carousel-hook-log.json`

#### 10 Carousel Hook Styles

| Style | Description | Example (6-8 words) |
|-------|-------------|---------------------|
| **Bold Claim** | A provocative stat or statement creating immediate tension | "The pricing mistake costing you $50k/year." |
| **Specific Result** | A concrete before-after transformation with hard numbers | "0 to 40% conversion in 90 days." |
| **Mistake Call-Out** | Name the exact mistake the reader is probably making | "5 hiring mistakes killing your startup." |
| **Myth Buster** | Challenge an accepted belief head-on | "Why your morning routine is sabotaging your business." |
| **Curiosity Gap** | Withhold the punchline to force the swipe | "I lost a $500k deal because of one thing." |
| **Number Reveal** | Promise a finite, specific list delivering clear value | "7 marketing blindspots costing you customers." |
| **Before-After** | Show a dramatic contrast between problem and outcome | "From $50k to $500k in 18 months." |
| **Checklist Promise** | Signal immediately actionable, saveable content | "The 10-point checklist for high-converting landing pages." |
| **Framework Authority** | Position a proprietary structured method | "The 3-step framework that doubled our leads." |
| **Relatable Pain** | Agitate a specific pain point the reader feels right now | "Stop doing this on LinkedIn (it kills your reach)." |

#### Carousel Hook Log Format

Each entry in `./carousel-hook-log.json`:
```json
{
  "date": "2026-07-08",
  "hook_style": "Bold Claim",
  "hook_text": "The pricing mistake costing you $50k/year",
  "carousel_topic": "SaaS pricing strategy",
  "carousel_format": "DATA_STORY"
}
```

Keep last 30 entries. Trim older ones on each write.

### 4C. Slide Structure (7 Slides)

```
Slide 1: hook      — Attention-grabbing opener following CAROUSEL_HOOK_STYLE formula, with product preview
Slide 2: intro     — What the product/idea is (with screenshot if applicable)
Slide 3: features  — What you can do / key points (icon list or numbered cards)
Slide 4: proof     — Key stat, data, or how it works (with UI screenshot)
Slide 5: social    — Testimonials, quotes, partner endorsements, or supporting data
Slide 6: honest    — Honest caveat + availability info (builds trust)
Slide 7: cta       — Call to action with branded button
```

### 4D. Slide Content Specification

```
━ CAROUSEL ━

Hook style used: [CAROUSEL_HOOK_STYLE from rotation]

Slide 1 — Hook:
[Hook following the selected carousel hook style. 6 to 8 words max. Creates a 
curiosity gap. Never reveals the answer on this slide.]

Slide 2 — Intro:
[What the topic is. 1 sentence max. Brand name or topic title in large text.]

Slide 3 — Key Points:
[3-5 points, each 1 sentence max. Specific numbers over adjectives.]

Slide 4 — Proof:
[The strongest stat or data point. Large number. 1-2 sentences context.]

Slide 5 — Social Proof / Why It Matters:
[A quote, testimonial, or implication. 1-2 sentences.]

Slide 6 — Honest Take:
[One genuine limitation or caveat. Then what it still does well. Builds trust.]

Slide 7 — CTA:
[Single CTA. "Follow for more posts on [specific topic area]." Nothing else.]

Caption:
[Hook line. What the carousel covers in one sentence. Engagement question. 
CTA to save or repost. 4 lines max total.]
```

### 4E. Writing Rules for Carousel Slides

- No em-dashes anywhere
- Lowercase starts and skipped periods allowed (human voice)
- Maximum 2 sentences per slide (prefer 1)
- Italic serif emphasis on one word per headline (Instrument Serif)
- Real image visible on minimum 4 of 7 slides
- Hook headline: ≤35 characters
- Point headline: ≤40 characters
- Body text: 1 sentence maximum per slide, ≤90 characters
- Supporting card description: ≤50 characters
- CTA subtext: ≤80 characters
- The "squint test": blur your eyes — you should see one dominant visual element per slide

### 4F. Design System

**Color Palette:**
- Base background: `#F8F7F3` (cream)
- Text: `#111111` (nearly black)
- Accent: Randomly selected from curated palette OR featured product's brand color

**Curated Premium Palette:**
- `Claude Salmon`: `#D9785B`
- `OpenAI Mint`: `#10A37F`
- `Linear Purple`: `#5E6AD2`
- `Figma Azure`: `#00C4CC`
- `Vercel Blue`: `#0070F3`
- `Notion Red`: `#E16259`
- `Anthropic Peach`: `#D4A574`

**Typography:**
- Sans: `Plus Jakarta Sans` (500, 600, 700, 800, 900)
- Serif italic: `Instrument Serif` (italic 400) for emphasis words
- Numbers: 160-200px for big stats, tight letter-spacing (-8px)
- Headlines: 65-85px, tight letter-spacing (-2px to -3px)

**Universal Elements (every slide):**
- Top bar: star icon + header label (left), "founders wing / 2026" italic (right)
- Slide number badge: 44px circle in accent color, top right
- Brand color accent on: star icon, slide badge, italic emphasis words, divider lines
- Footer: bottom-left body text, "SWIPE →" right
- Google Fonts: Include `Plus Jakarta Sans` + `Instrument Serif` via CDN

### 4G. Image Sourcing

Before writing any HTML, source minimum 4 valid images >10KB:

- OG image / press kit from source URL
- Product screenshots from source website
- Unsplash Source: `https://source.unsplash.com/1080x1080/?[theme-keyword]`
- Brand logos: `https://logo.clearbit.com/[brand].com`
- Screenshots via Puppeteer: use `capture_source.js` script

### 4H. PDF Generation Rule

The carousel PDF must always be built FROM the rendered PNGs, never from HTML. The PNGs are the source of truth. Use `render-pdf.js` which combines PNGs into a multi-page PDF. Never use `page.pdf()` on HTML — that produces broken/tiny PDFs.

---

## 5. Infographic

A single 1080×1080 PNG data visualisation. Five distinct visual formats, selected by the shape of the data.

### 5A. Format Decision Tree

Apply this decision tree before generating any infographic HTML:

```
1. Is the data a RANKED LIST with 6-10 items (percentages, dollar amounts, counts)?
   YES → RANKED_BARS
   NO  → continue

2. Is the data a PARTS-OF-A-WHOLE breakdown (market share, allocation, distribution)?
   YES → DONUT_BREAKDOWN
   NO  → continue

3. Is the data a CHANGE_OVER_TIME (year-over-year, growth curve, trend)?
   YES → TIMELINE_SHIFT
   NO  → continue

4. Is the data a HEAD-TO-HEAD comparison (A vs B with multiple dimensions)?
   YES → COMPARISON_SPLIT
   NO  → continue

5. Is the data a SINGLE BIG STAT with supporting context (one hero number)?
   YES → HERO_NUMBER
   NO  → default to RANKED_BARS
```

### 5B. Format Deduplication Rules

If this infographic is part of a daily routine, check `./infographic-run-log.json`:

1. Any dataset whose subject overlaps >50% with a topic in the last 14 entries is disqualified.
2. Tally format counts in the last 5 entries. The format used most recently (last entry) is banned this run. If one format appears 3+ times in the last 5 runs, also ban it.
3. If the naturally-selected format is banned, pick the next-best format that fits the data shape.

### 5C. Shared Design System (All Formats)

**Default Palette (Warm Cream):**
- Background: `#F5EFE8`
- Accent primary: `#E63946` (coral red)
- Accent secondary: `#1A1A1A` (ink)
- Soft accent: `#C5392E` (deep coral)
- Tertiary: `#E8A33D` (mustard)
- Text body: `#1A1A1A`
- Text muted: `#5A5A5A`

**Alt Palette (Dark Mode, for hot-take data):**
- Background: `#1A1A1A`
- Accent: `#E63946`
- Text body: `#F5EFE8`
- Soft: `#2A2A2A`

**Typography:**
- Sans: Inter (400, 500, 600, 700, 800, 900)
- Serif italic: Instrument Serif (italic 400) for accent words and rank numerals
- Mono: rarely, only for source attribution lines

**Universal Elements (every infographic):**
- Top bar: dot + uppercase kicker (left), italic serif date or brand (right)
- Title: 64-72px, sentence case, one italic serif accent word in coral
- Subtitle: 18-22px, soft muted text, max 2 sentences
- Footer: 1px divider, source attribution left, `@zetabotai` right
- 1080 × 1080 canvas
- No em-dashes anywhere
- Stats are bold sans, never serif
- Source line is plain mono or sans, never bold

### 5D. Format 1 — RANKED_BARS

**Use for:** Ranked lists of 6-10 categories.

**Layout:**
- Title block top (≈220px high)
- 10 rows of horizontal bars filling middle
- Footer with source

**Visual Recipe:**
- Italic serif numeral rank (01, 02, etc.) at left
- Category label in bold sans
- Bar with rounded ends, three color tiers (top 3 = coral, middle = soft coral, bottom = ink/dark)
- Value at far right in bold sans
- Bars are proportional to max value (scale max to 100%)

**Color Scheme:**
- Category 1 (first type): `#D4A843` (warm gold)
- Category 2 (second type): `#6BA368` (muted green)
- Category 3 (third type, if applicable): `#6B6BB5` (slate blue)

**Legacy alternative (simpler color scheme):**
- White background (`#FFFFFF`)
- Bold title in sentence case, ≈28px, near the top
- Italic subtitle directly below, ≈16px, grey (`#555555`)
- Legend row: small coloured squares with category labels, centred
- Horizontal bar chart with alternating row backgrounds (`#F9F9F9` and `#FFFFFF`)
- Value circles on far right, ≈38px diameter, coloured, number inside in white
- Small data source credit at bottom left in ≈11px grey text

### 5E. Format 2 — DONUT_BREAKDOWN

**Use for:** Parts-of-a-whole breakdowns (market share, time allocation, budget split).

**Layout:**
- Title block top
- Donut chart center-left (≈500px diameter)
- Legend with percentages and labels right side
- Bottom: one italic serif takeaway sentence
- Footer

**Visual Recipe:**
- Donut built with conic-gradient or SVG circles
- 5-7 segments max (combine smaller into "Other")
- Top segment in coral, second in deep coral, third in mustard, others in ink shades
- Center of donut: total or hero number
- Legend rows: color dot + label + bold percentage

### 5F. Format 3 — TIMELINE_SHIFT

**Use for:** Change over time (year-over-year, growth curve, adoption trend).

**Layout:**
- Title block top
- Two-or-three large bars or columns showing each time point
- Big arrow or "+X%" callout between them
- Bottom: 2-sentence story behind the shift
- Footer

**Visual Recipe:**
- Each time point gets a vertical bar with the year as italic serif label on top
- First year in ink/dark, latest year in coral (the "winner" color)
- Italic serif arrow "→" or "+X%" between bars
- Stat callouts at the top of each bar

### 5G. Format 4 — COMPARISON_SPLIT

**Use for:** A vs B comparisons across multiple dimensions.

**Layout:**
- Title block top with "vs" centered
- Two-column split, full bleed left and right
- Left column = one option (ink/dark)
- Right column = other option (coral)
- 3-4 comparison rows stacked vertically
- Footer

**Visual Recipe:**
- Each row has a small label on a center divider, then the value on each side
- Coral side wins by visual weight (bigger number, bolder)
- Title says "A vs B" with italic serif "vs"

### 5H. Format 5 — HERO_NUMBER

**Use for:** A single huge stat with 3-4 supporting mini-stats.

**Layout:**
- Top kicker
- Massive number filling center (300px+)
- One-line italic serif sentence below
- 3-4 mini-stat boxes at bottom in a row
- Footer

**Visual Recipe:**
- Background can be cream or full-bleed coral
- The big number is the only thing that matters
- Mini-stats are small (40-50px values, 14px labels)
- Each mini-stat sits in a soft-tinted card

### 5I. HTML Generation Rules

For any format, the generated HTML must:
- Have zero external dependencies (no Google Fonts, no CDN, no images) — OR include Google Fonts `<link>` tags in the `<head>` if fonts are needed
- Use a system font stack as fallback: `-apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif`
- Be designed at 1080×1080px for LinkedIn square format
- Render as a clean, professional data visualisation
- Bars/charts must be accurate — proportional to actual values
- Be directly screenshottable without cropping

**Output:**
- Save HTML to `./linkedin-infographic.html`
- Screenshot at 1080×1080 → `./linkedin-infographic-{YYYYMMDD}.png`

### 5J. Infographic Output Format
```
━━━ INFOGRAPHIC ━━━

Topic: [The dataset subject]
Format: [RANKED_BARS / DONUT_BREAKDOWN / TIMELINE_SHIFT / COMPARISON_SPLIT / HERO_NUMBER]

Data source: [URL of the dataset source]

Caption:
[Hook line making the stat feel urgent or surprising]
[Context — what this means for the reader's work or income]
[Engagement question]
[CTA — save or repost]

[Full HTML inline here, plus Write to ./linkedin-infographic.html]
```

---

## 6. Multi-Image Post

A single image (sourced from Reddit or WebSearch) with a caption that adds insight beyond what the image shows.

### Image Sourcing
Scan all fetched Reddit content for high-quality images:
- `url_overridden_by_dest` field
- `preview.images[0].source.url` field
- `thumbnail` field

Prioritise:
- Charts, graphs, data visualisations, ranked lists
- Screenshots of tools, dashboards, or growth stats
- Infographics with clear data
- Comparison visuals or before/after results

If no strong image is found on Reddit, use WebSearch to find one recent, shareable visual from a credible source (Statista, a16z, Forbes, etc.).

### Output Format
```
━━━ MULTI-IMAGE POST ━━━

Image: [Direct URL to the image]

Caption:
[Hook line that makes the image worth stopping for]
[2 to 3 sentences that add genuine insight beyond what the image shows on its 
own — context, implication, or what this means for the audience]
[Engagement question]
[Single CTA]
```

### Quality Checklist
- [ ] Image is valid, high-resolution, and relevant
- [ ] Image URL is direct (not a page URL)
- [ ] Caption adds context — does not just describe what's visible
- [ ] 6-part structure embedded naturally
- [ ] No banned vocabulary or patterns
- [ ] No em-dashes

---

## 7. Image & Asset Sourcing Reference

### Reddit Image Extraction
When fetching Reddit posts, extract images from these fields in priority order:
1. `url_overridden_by_dest` — direct image URL if present
2. `preview.images[0].source.url` — Reddit-hosted preview (replace `&` with `&`)
3. `thumbnail` — small thumbnail (last resort)

### Direct Image URLs
- **Unsplash Source:** `https://source.unsplash.com/1080x1080/?[theme-keyword]`
- **Clearbit Logo API:** `https://logo.clearbit.com/[brand-domain].com`
- **Favicon fallback:** `https://[company.com]/favicon.ico`

### Brand Color Extraction
When a brand/product is featured, extract brand colors from:
1. Brand Color Reference table (see branded-carousel SKILL.md)
2. Source website HTML: look for CSS variables like `--color-brand`, `--primary`
3. Hero element inline styles on the source page

Common brand colors reference:
| Company | Primary | Secondary |
|---------|---------|-----------|
| Anthropic | `#D4A574` | `#C4836A` |
| OpenAI | `#10A37F` | `#1A7F64` |
| Google | `#4285F4` | `#EA4335` |
| Meta | `#0668E1` | `#1877F2` |
| Microsoft | `#00A4EF` | `#7FBA00` |
| Perplexity | `#20808D` | `#1B6B75` |
| Midjourney | `#000000` | `#FFFFFF` |
| Canva | `#00C4CB` | `#7D2AE8` |
| Adobe | `#FF0000` | `#2C2C2C` |
| Stability AI | `#7C3AED` | `#A855F7` |
| Nvidia | `#76B900` | `#1A1A1A` |

---

## 8. Quality Checklist (Apply to Every Post)

For every post generated, verify:
- [ ] Topic passes content doctrine filter (Reach, Stakes, Altitude, Edge)
- [ ] Topic is NOT on the DROP list
- [ ] No banned vocabulary words used
- [ ] No banned LinkedIn patterns used
- [ ] No banned contrast constructions used
- [ ] No em-dashes anywhere
- [ ] No "I" statements (third-person observer voice)
- [ ] Sentence case in headings and slide labels
- [ ] Specific numbers over adjectives
- [ ] 6-part structure present: Hook → Pain → Value → Dream → Question → CTA
- [ ] Engagement question is specific (not "What do you think?")
- [ ] Single CTA only (follow, save, or repost — not stacked)
- [ ] Closing line lands on something new, doesn't restate

For the batch-level check (when generating multiple posts):
- [ ] No two posts share the same source thread or Reddit link
- [ ] No two posts share the same subject matter angle
- [ ] Each post uses only its assigned topic

---

## 9. Output Format Reference

All posts in a batch are written to a date-stamped file. The canonical delimiters:

```
━━━ COLLABORATIVE ARTICLE ━━━

[Full post text]

━━━ POLL ━━━

[Setup caption]

[Question]
☐ Option A
☐ Option B
☐ Option C
☐ Option D

[Comment invite]

━━━ CAROUSEL ━━━

Hook style used: [STYLE]

Slide 1:
[Hook text]

Slide 2:
[Content]

... (7 slides total)

Caption:
[Caption text]

━━━ MULTI-IMAGE POST ━━━

Image: [URL]

Caption:
[Caption text]

━━━ INFOGRAPHIC ━━━

Topic: [Topic]
Format: [FORMAT]

Caption:
[Caption text]
```

---

## 10. Run-Log Management

### Infographic Run-Log (`./infographic-run-log.json`)
```json
{
  "date": "2026-07-08",
  "topic": "AI adoption by industry 2026",
  "format": "RANKED_BARS",
  "generated_at": "2026-07-08T14:30:00Z"
}
```
- Keep last 30 entries
- Use for deduplication (banned topics = last 14, banned formats = last 5)

### Carousel Hook Log (`./carousel-hook-log.json`)
```json
{
  "date": "2026-07-08",
  "hook_style": "Bold Claim",
  "hook_text": "The pricing mistake costing you $50k/year",
  "carousel_topic": "SaaS pricing strategy",
  "carousel_format": "DATA_STORY"
}
```
- Keep last 30 entries
- Last style = banned. Any style appearing 3+ times in last 7 = banned.