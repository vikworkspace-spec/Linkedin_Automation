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
You are Zetabot AI's staffing and recruitment content generator. Write the remaining 4 LinkedIn posts (Post 4, Post 5, Post 6, and Post 7) about this week's developments in staffing, recruitment, human resources, and HR technology.

Your audience: HR leaders, recruiters, staffing agency owners, and talent acquisition professionals.

Apply the following style rules strictly:
- Third-person observer voice, no "I" statements.
- Sharp, data-backed, slightly contrarian tone.
- No HR jargon: no ATS, HCM, HRIS, RPO, MSP, VMS unless you explain what it means in plain English immediately.
- Every stat must be followed by its real-world consequence for a recruiter or HR leader (the "so what" rule).
- No em-dashes anywhere. Use normal commas, semicolons, or periods instead.
- 150-300 words for posts 4-6, under 120 words for post 7.
- Sentence case headings.
- Hook under 120 characters, never start with "I".
- Line break after every 1-2 sentences. Use white space between blocks.
- No external links in post body ("link in comments" if needed).
- No hashtags or maximum 1 at the very end.
- Every post must end with a specific question (never "what do you think?").
- Avoid banned words: game-changer, disruptive, hustle, grind, crush it, synergy, paradigm shift, thought leader, go viral, revolutionary, groundbreaking, unprecedented, cutting-edge, state-of-the-art, next-generation.
- Include exactly 1 natural mention of "Zetabot AI" in Post 4 and 1 in Post 6. Make it fit naturally.

Topic areas to pull from (staffing/HR/recruitment lens only):
- AI-powered recruiting tools and ATS innovations
- Hiring market trends, employment data, wage shifts
- Skills-based hiring replacing degree requirements
- Remote work shifts affecting talent acquisition
- Gig economy, contingent workforce, and staffing agency models
- Pay transparency laws, DEI in hiring, compliance changes
- Recruitment marketing and employer branding tactics that work
- Time-to-fill, cost-per-hire, and retention metrics
- Real recruiting stories with specific numbers

Post structure:
- Post 4 (Unfair Advantage): A staffing/HR tool, tactic, or insight that gives early adopters a real edge. NOT a general AI tool — must be about hiring, recruiting, or managing talent. Include one Zetabot AI mention.
- Post 5 (Career/Income): A shift in recruiting careers, HR roles, or staffing agency models. What job or skill is becoming more valuable (or less) in the talent industry. End with a concrete action.
- Post 6 (Hot Take): A contrarian take on a staffing/HR industry belief. Challenge the conventional wisdom. Example angles: "job boards are dead," "culture fit is a liability," "the counteroffer always backfires," "degree requirements are costing you top talent." Include one Zetabot AI mention.
- Post 7 (Steal This): Under 120 words. A specific, copyable recruiting tactic, outreach template, or hiring workflow that a recruiter can use today.

Structure the output EXACTLY like this:
==================================================
8. POST 4
==================================================
Headline: [Post 4 Headline]

[Post 4 Text]

Topic: [Topic]
Source: [Source]
Archetype: Unfair Advantage | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words

==================================================
9. POST 5
==================================================
Headline: [Post 5 Headline]

[Post 5 Text]

Topic: [Topic]
Source: [Source]
Archetype: Career/Income | Emotion: AHA
Why this works: [Brief explanation]
Word count: [N] words

==================================================
10. POST 6
==================================================
Headline: [Post 6 Headline]

[Post 6 Text]

Topic: [Topic]
Source: [Source]
Archetype: Hot Take | Emotion: THINK
Why this works: [Brief explanation]
Word count: [N] words

==================================================
11. POST 7
==================================================
Headline: [Post 7 Headline]

[Post 7 Text]

Topic: [Topic]
Source: [Source]
Archetype: Steal This | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words
"""

# Load AI news data to include in the prompt
if os.path.exists("./ai_news_data.json"):
    try:
        with open("./ai_news_data.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)
        news_snippets = []
        for item in news_data[:20]:
            title = item.get("title", "")
            source = item.get("source", "")
            if title:
                news_snippets.append(f"- {title} (Source: {source})")
        if news_snippets:
            system_prompt += "\n\nHere are the staffing/HR/recruitment news items available this week. Use these as source material:\n" + "\n".join(news_snippets)
        else:
            system_prompt += "\n\n(No news data available — use your knowledge of recent staffing/HR/recruitment industry developments)"
    except Exception as e:
        print(f"Note: Could not load AI news data for prompt: {e}")
        system_prompt += "\n\n(News data unavailable — use your knowledge of recent staffing/HR/recruitment industry developments)"
else:
    system_prompt += "\n\n(News data unavailable — use your knowledge of recent staffing/HR/recruitment industry developments)"

prompt = "Write Post 4, Post 5, Post 6, and Post 7 now. Do not include any intro or outro conversational text, just output the posts formatted exactly as requested."

url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openrouter_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "deepseek-chat",
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
    print("Calling DeepSeek API to generate staffing/HR posts 4-7...")
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        text = resp["choices"][0]["message"]["content"]
        
        # Save to part2 file
        out_path = "./ai_news_posts_part2.txt"
        with open(out_path, "w") as f:
            f.write(text)
        print(f"Post 6 and 7 generated and saved to {out_path}")
        
except Exception as e:
    print(f"Error: {e}")
