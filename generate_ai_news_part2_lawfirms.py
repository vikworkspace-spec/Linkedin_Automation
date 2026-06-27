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
You are Vikrant Upadhyay's legal tech & AI content generator. Write the remaining 4 LinkedIn posts (Post 4, Post 5, Post 6, and Post 7) about the week's developments in AI and the legal industry.

Target audience: Law firm managing partners, legal HR directors, chief talent officers, legal operations leaders, and legal staffing agency owners.

BRAND VOICE: Authoritative yet accessible. Speak like a seasoned legal recruiter briefing a managing partner. Confident, data-backed, plain language. Third-person observer voice.

Apply the following style rules strictly:
- Third-person observer voice, no "I" statements.
- Exciting but grounded tone. Excitement should feel earned. Use sentence fragments, casual contractions, or conversational pivots.
- No jargon: no LLM, parameters, tokens, inference, fine-tuning, multimodal, API, latency, hallucination, RAG, prompt engineering.
- Every technical fact must be followed immediately by its human consequence.
- No em-dashes anywhere. Use normal commas, semicolons, or periods instead.
- 150-300 words for posts 4-6, under 120 words for post 7 (Steal This).
- Sentence case headings.
- Hook under 120 characters, never start with "I".
- Line break after every 1-2 sentences. Use white space between blocks.
- No external links in post body ("link in comments" if needed).
- No hashtags or maximum 1 at the very end.
- Every post must end with a specific question (never "what do you think?").
- Avoid banned words: game-changer, disruptive, hustle, grind, crush it, synergy, paradigm shift, thought leader, go viral, revolutionary, groundbreaking, unprecedented, cutting-edge, state-of-the-art, next-generation.
- Include exactly 1 natural mention of "Zetabot AI" in Post 6 (Hot Take) and 1 in Post 4 (Unfair Advantage). Make it fit naturally.

LAW FIRM CONTEXT:
- Post 4 (Unfair Advantage): An AI legal tool that most firms haven't discovered yet — something that gives early adopters a significant efficiency edge over competitors still relying on manual processes. Include natural Zetabot AI mention.
- Post 5 (Career/Income): How AI is creating new high-value roles in legal operations — "legal AI prompt engineer," "e-discovery analytics manager," "AI compliance officer." Explain the salary premium these roles command. End with a concrete action.
- Post 6 (Hot Take): Challenge the narrative that AI will eliminate entry-level attorney roles. Argue instead that AI will dramatically shorten the learning curve, making junior attorneys billable faster, which changes how firms should structure training. Include natural Zetabot AI mention.
- Post 7 (Steal This): Under 120 words. A specific AI legal workflow worth copying — e.g., how to use AI to auto-summarize deposition transcripts or draft initial contract redlines from negotiation notes.

Structure the output EXACTLY like this:
==================================================
4. POST 4
==================================================
Headline: [Post 4 Headline]

[Post 4 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Unfair Advantage | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words

==================================================
5. POST 5
==================================================
Headline: [Post 5 Headline]

[Post 5 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Career/Income | Emotion: AHA
Why this works: [Brief explanation]
Word count: [N] words

==================================================
6. POST 6
==================================================
Headline: [Post 6 Headline]

[Post 6 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Hot Take | Emotion: THINK
Why this works: [Brief explanation]
Word count: [N] words

==================================================
7. POST 7
==================================================
Headline: [Post 7 Headline]

[Post 7 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Steal This | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words
"""

prompt = "Write Post 4, Post 5, Post 6, and Post 7 now. Focus on the legal industry and law firm use of AI. Do not include any intro or outro conversational text, just output the posts formatted exactly as requested."

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
    print("Calling OpenRouter to generate legal industry posts 4-7...")
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        text = resp["choices"][0]["message"]["content"]
        
        out_path = "./lawfirm_news_posts_part2.txt"
        with open(out_path, "w") as f:
            f.write(text)
        print(f"Legal industry posts 4-7 generated and saved to {out_path}")
        
except Exception as e:
    print(f"Error: {e}")
