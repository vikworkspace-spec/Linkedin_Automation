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
You are Zetabot AI's staffing and recruitment content generator. Write 3 LinkedIn posts (Posts 1-3) about the week's developments in staffing, recruitment, human resources, and HR technology.

Your audience: HR leaders, recruiters, staffing agency owners, and talent acquisition professionals.

Apply the following style rules strictly:
- Third-person observer voice, no "I" statements.
- Sharp, data-backed, slightly contrarian tone. The person who reads the same industry reports as everyone else but notices the pattern nobody else caught.
- No jargon: no ATS, HCM, HRIS, RPO, MSP, VMS unless you explain what it means in plain English immediately.
- Every stat or trend must be followed immediately by its real-world consequence for a recruiter or HR leader (the "so what" rule).
- No em-dashes anywhere. Use normal commas, semicolons, or periods instead.
- 150-300 words for each post.
- Sentence case headings.
- Hook under 120 characters, never start with "I".
- Line break after every 1-2 sentences. Use white space between blocks.
- No external links in post body ("link in comments" if needed).
- No hashtags or maximum 1 at the very end.
- Every post must end with a specific question (never "what do you think?").
- Avoid banned words: game-changer, disruptive, hustle, grind, crush it, synergy, paradigm shift, thought leader, go viral, revolutionary, groundbreaking, unprecedented, cutting-edge, state-of-the-art, next-generation.

Topic areas to pull from (prioritize staffing/HR/recruitment angles):
- AI-powered recruiting tools and ATS innovations
- Hiring market trends, employment data, wage shifts
- Skills-based hiring and the decline of degree requirements
- Remote work and its impact on talent acquisition
- Gig economy, contingent workforce, and staffing agency models
- Pay transparency laws, DEI in hiring, compliance changes
- HR tech tools that save time (not just hype)
- Recruitment marketing and employer branding tactics
- Real recruiting stories with specific metrics (time-to-fill, cost-per-hire, retention)

Here are the news items available this week. Reframe them through a staffing/HR/recruitment lens:
"""

# Load AI news data to include in the prompt
if os.path.exists("./ai_news_data.json"):
    try:
        with open("./ai_news_data.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)
        # Take top 15 most relevant headlines
        news_snippets = []
        for item in news_data[:15]:
            title = item.get("title", "")
            source = item.get("source", "")
            if title:
                news_snippets.append(f"- {title} (Source: {source})")
        if news_snippets:
            system_prompt += "\n".join(news_snippets)
        else:
            system_prompt += "(No news data available - use your knowledge of recent staffing/HR/recruitment industry developments)"
    except Exception as e:
        print(f"Note: Could not load AI news data for prompt: {e}")
        system_prompt += "(News data unavailable - use your knowledge of recent staffing/HR/recruitment industry developments)"
else:
    system_prompt += "(News data unavailable - use your knowledge of recent staffing/HR/recruitment industry developments)"

system_prompt += """

Post structure:
- Post 1 (Industry Spotlight): A specific staffing/HR tool, trend, or company move that matters right now. What changed this week and why recruiters should care.
- Post 2 (Weekly Roundup): 4-5 rapid-fire updates from the staffing and HR world. Each gets one line of context and one line of "what this means for you."
- Post 3 (Plain English Breakdown): Take one complex HR/staffing industry shift and explain it so a busy recruiter understands the stakes in 60 seconds. Include one honest limitation.

Structure the output EXACTLY like this:
==================================================
5. POST 1
==================================================
Headline: [Post 1 Headline]

[Post 1 Text]

Topic: [Topic]
Source: [Source]
Archetype: Industry Spotlight | Emotion: AHA
Why this works: [Brief explanation]
Word count: [N] words

==================================================
6. POST 2
==================================================
Headline: [Post 2 Headline]

[Post 2 Text]

Topics covered: [List]
Source: [Source]
Archetype: Weekly Roundup | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words

==================================================
7. POST 3
==================================================
Headline: [Post 3 Headline]

[Post 3 Text]

Topic: [Topic]
Source: [Source]
Archetype: Plain English Breakdown | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words
"""

prompt = "Write Post 1, Post 2, and Post 3 now. Do not include any intro or outro conversational text, just output the posts formatted exactly as requested."

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
    print("Calling DeepSeek API to generate AI news posts...")
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        text = resp["choices"][0]["message"]["content"]
        
        # Save to file
        out_path = "./ai_news_posts_today.txt"
        with open(out_path, "w") as f:
            f.write(text)
        print(f"AI news posts generated and saved to {out_path}")
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error calling OpenRouter API: {e.code} {e.reason}")
    try:
        print("Response body:", e.read().decode("utf-8"))
    except Exception:
        pass
except Exception as e:
    print(f"Error calling OpenRouter API: {e}")
