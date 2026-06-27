import os
import json
import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Read OpenRouter API key from .env
openrouter_key = None
env_path = "./.env"
with open(env_path) as f:
    for line in f:
        if line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1]
            break

if not openrouter_key:
    print("Error: OPENROUTER_API_KEY not found in .env")
    exit(1)

system_prompt = """
You are a legal staffing and talent acquisition content generator. Write 3 LinkedIn posts (Posts 1-3) about the week's developments in legal hiring, legal staffing technology, and law firm workforce trends.

Target audience: Law firm managing partners, legal HR directors, chief talent officers, legal operations leaders, and legal staffing agency owners.

BRAND VOICE: Authoritative yet accessible. Speak like a seasoned legal recruiter briefing a managing partner. Confident, data-backed, plain language. Third-person observer voice.

Apply the following style rules strictly:
- Third-person observer voice, no "I" statements.
- Authoritative but conversational tone. Use sentence fragments and casual pivots where they sharpen the point.
- No AI/tech jargon: no LLM, parameters, tokens, inference, fine-tuning, multimodal, API, latency, hallucination, RAG, prompt engineering.
- Every data point must be followed by its practical consequence for law firms (the "so what" rule): how does this reduce time-to-fill, improve retention, lower cost-per-hire, or solve a specific staffing problem?
- No em-dashes anywhere. Use commas, semicolons, or periods.
- 150-300 words for each post.
- Sentence case headings.
- Hook under 120 characters, never start with "I".
- Line break after every 1-2 sentences. White space between blocks.
- No external links in post body ("link in comments" if needed).
- No hashtags or maximum 1 at the very end.
- Every post must end with a specific question (never "what do you think?").
- Avoid banned words: game-changer, disruptive, hustle, grind, crush it, synergy, paradigm shift, thought leader, go viral, revolutionary, groundbreaking, unprecedented, cutting-edge, state-of-the-art, next-generation.

LEGAL STAFFING CONTEXT — use these themes for post content:
- AI-powered legal candidate sourcing and screening tools
- Law firm lateral hiring trends and associate compensation data
- Contract attorney and legal temp staffing market dynamics
- Diversity hiring pipelines and client mandates for law firms
- Legal recruitment technology (ATS platforms, AI matching for legal roles)
- Retention strategies: why mid-level associates leave and what reduces attrition
- The economics of using staffing agencies vs. direct hiring for law firms
- Practice area demand shifts (e.g., litigation surge, regulatory hiring, IP talent shortage)
- How AI tools are changing paralegal and document review staffing needs
- Remote/hybrid legal work and its impact on geographic talent pools

Here are the news items of the week to cover:
- Post 1 (Tool Spotlight): [Pick a real legal staffing or recruiting technology — e.g., a new AI candidate matching platform for legal roles, a legal-specific ATS, or a tool that automates reference checks for attorney placements. If unsure, use: "LegalMatch AI" launched a platform that matches lateral associate candidates to open roles across 500+ firms using practice area experience, bar admissions, and cultural fit scoring, reducing recruiter screening time from 40 hours to 3.]
- Post 2 (Weekly Roundup): 5 updates in legal staffing this week (e.g., Am Law 200 compensation survey results, new legal temp platform launches, diversity hiring mandate updates, legal staffing M&A activity, and major firm layoff or hiring announcements).
- Post 3 (Plain English Breakdown): Break down a specific legal staffing trend — e.g., why contract attorney demand is surging while permanent associate hiring has slowed. Explain the economic forces, what it means for law firm budgets, and one honest caveat about over-reliance on contract staffing.

Structure the output EXACTLY like this:
==================================================
1. POST 1
==================================================
Headline: [Post 1 Headline]

[Post 1 Text]

Tool featured: [Name]
Source: [Source]
Archetype: Tool Spotlight | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words

==================================================
2. POST 2
==================================================
Headline: [Post 2 Headline]

[Post 2 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Weekly Roundup | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words

==================================================
3. POST 3
==================================================
Headline: [Post 3 Headline]

[Post 3 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Plain English Breakdown | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words
"""

prompt = "Write Post 1, Post 2, and Post 3 now. Focus on the legal industry and law firm use of AI. Do not include any intro or outro conversational text, just output the posts formatted exactly as requested."

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openrouter_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "~anthropic/claude-sonnet-latest",
    "max_tokens": 1500,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers=headers,
    method="POST"
)

try:
    print("Calling OpenRouter to generate legal industry AI news posts...")
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        text = resp["choices"][0]["message"]["content"]
        
        # Save to file
        out_path = "./lawfirm_news_posts_today.txt"
        with open(out_path, "w") as f:
            f.write(text)
        print(f"Legal industry AI news posts generated and saved to {out_path}")
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error calling OpenRouter API: {e.code} {e.reason}")
    try:
        print("Response body:", e.read().decode("utf-8"))
    except Exception:
        pass
except Exception as e:
    print(f"Error calling OpenRouter API: {e}")
