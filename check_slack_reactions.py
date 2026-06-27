import json, os, urllib.request

# Read token
slack_token = None
with open('.env') as f:
    for line in f:
        if line.startswith('SLACK_BOT_TOKEN='):
            slack_token = line.strip().split('=', 1)[1]
            break

if not slack_token:
    print('No token')
    exit(1)

channel = 'C0BDL4V7VT4'

# Fetch recent messages
url = f'https://slack.com/api/conversations.history?channel={channel}&limit=20'
headers = {'Authorization': f'Bearer {slack_token}'}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))

if not data.get('ok'):
    print(f'Error: {data.get("error")}')
    exit(1)

messages = data.get('messages', [])
print(f'Found {len(messages)} recent messages')
print('---')

for idx, msg in enumerate(messages):
    ts = msg.get('ts', '')
    text = msg.get('text', '')[:120]
    reactions = msg.get('reactions', [])
    
    # Determine type
    msg_type = 'TEXT'
    if 'linkedin-infographic' in text or 'INFOGRAPHIC' in text:
        msg_type = 'INFOGRAPHIC_FILE'
    elif 'carousel.pdf' in text or 'CAROUSEL' in text:
        msg_type = 'CAROUSEL_FILE'
    elif 'linkedin_posts' in text and '.txt' in text:
        msg_type = 'TXT_FILE'
    elif 'linkedin_posts' in text and '.pdf' in text:
        msg_type = 'PDF_FILE'
    elif 'Slide' in text and 'of' in text:
        msg_type = 'SLIDE'
    elif '📅' in text:
        msg_type = 'HEADER'
    elif '📰' in text:
        msg_type = 'NEWS_HEADER'
    elif 'file' in msg and msg.get('file'):
        msg_type = 'FILE_UPLOAD'
    
    reaction_str = ''
    if reactions:
        reaction_details = []
        for r in reactions:
            name = r.get('name', '?')
            count = r.get('count', 0)
            reaction_details.append(f'{name}({count})')
        reaction_str = ' | Reactions: ' + ', '.join(reaction_details)
    
    print(f'[{idx}] [{ts[:8]}] {msg_type}: {text[:80].strip()}...{reaction_str}')
