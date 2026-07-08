import json, urllib.request, urllib.parse, ssl, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

token = None
with open(".env") as f:
    for line in f:
        if line.startswith("SLACK_BOT_TOKEN="):
            token = line.strip().split("=", 1)[1]
            break

channel = "C0BDL4V7VT4"

def slack_api(method, params=None):
    url = f"https://slack.com/api/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, context=ctx) as res:
        return json.loads(res.read().decode("utf-8"))

# Get messages from last 3 hours
oldest = str(int(time.time() - 10800))
history = slack_api("conversations.history", {"channel": channel, "oldest": oldest, "limit": 50})

if not history.get("ok"):
    print(f"Error: {history.get('error')}")
    exit(1)

messages = history.get("messages", [])
print(f"Found {len(messages)} messages in last 3 hours")
print()

approved = []
for msg in messages:
    text = (msg.get("text", "") or "")[:100].replace("\n", " ")
    ts = msg.get("ts", "")
    reactions = msg.get("reactions", [])

    has_approve = any(r["name"] in ("white_check_mark", "heavy_check_mark") for r in reactions)
    has_reject = any(r["name"] in ("x", "heavy_multiplication_x") for r in reactions)

    if has_approve or has_reject:
        status = "APPROVED" if has_approve else "REJECTED"
        print(f"{status}  | {ts} | {text}")
        if has_approve:
            approved.append({"ts": ts, "text": msg.get("text", "")})
    else:
        # Only show first 60 chars for pending
        short = text[:60]
        print(f"PENDING | {ts} | {short}")

print()
print(f"APPROVED: {len(approved)} posts ready for LinkedIn")
print(f"TOTAL: {len(messages)} messages scanned")

# Save approved posts to file for scheduling
if approved:
    with open("approved_for_publishing.json", "w") as f:
        json.dump(approved, f, indent=2)
    print("Saved to approved_for_publishing.json")
else:
    print("No approved posts found. React with ✅ in Slack to approve posts.")
