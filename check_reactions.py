import json, os, urllib.request

slack_token = None
with open('.env') as f:
    for line in f:
        if line.startswith('SLACK_BOT_TOKEN='):
            slack_token = line.strip().split('=', 1)[1]
            break

headers = {'Authorization': f'Bearer {slack_token}'}

# Try channels.history (legacy)
url = 'https://slack.com/api/channels.history?channel=C0BDL4V7VT4&count=15'
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf-8'))
    if data.get('ok'):
        messages = data.get('messages', [])
        print(f'Found {len(messages)} messages via channels.history')
        print()
        for idx, msg in enumerate(messages):
            ts = msg.get('ts', '')
            text = msg.get('text', '')[:100]
            reactions = msg.get('reactions', [])
            r_str = ''
            if reactions:
                parts = []
                for r in reactions:
                    name = r.get('name', '?')
                    count = r.get('count', 0)
                    parts.append(f'{name}({count})')
                r_str = ' | REACTIONS: ' + ', '.join(parts)
            print(f'  [{idx}] ts={ts[:8]} {text[:60].strip()}...{r_str}')
    else:
        print(f'channels.history failed: {data.get("error")}')
except Exception as e:
    print(f'Error with channels.history: {e}')
