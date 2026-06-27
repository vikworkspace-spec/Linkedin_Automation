import json, urllib.request

with open('.env') as f:
    for line in f:
        if line.startswith('SLACK_BOT_TOKEN='):
            t = line.strip().split('=', 1)[1]
            break

headers = {'Authorization': f'Bearer {t}'}

# Try files.list to find recent file uploads
url = 'https://slack.com/api/files.list?count=20'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))

if data.get('ok'):
    files = data.get('files', [])
    print(f'Found {len(files)} files')
    print()
    for f in files:
        name = f.get('name', '?')
        ts = f.get('timestamp', '?')
        
        # Get file share info
        shares = f.get('shares', {})
        # Check public shares
        for ch_type in ['public', 'private']:
            if ch_type in shares:
                for ch_id, share_list in shares[ch_type].items():
                    for share in share_list:
                        msg_ts = share.get('ts')
                        if msg_ts:
                            react_url = f'https://slack.com/api/reactions.get?channel={ch_id}&timestamp={msg_ts}&full=true'
                            req2 = urllib.request.Request(react_url, headers=headers)
                            with urllib.request.urlopen(req2) as res2:
                                react_data = json.loads(res2.read().decode('utf-8'))
                            if react_data.get('ok'):
                                rxs = react_data.get('message', {}).get('reactions', [])
                                r_str = ''
                                if rxs:
                                    parts = [f"{r.get('name','?')}({r.get('count',0)})" for r in rxs]
                                    r_str = ' | Reactions: ' + ', '.join(parts)
                                print(f'  {name} | ts={msg_ts[:8]}{r_str}')
                            break
                    break
                break
else:
    print(f'files.list failed: {data.get("error")}')
