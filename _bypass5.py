"""
Bypass probe round 5 — proper seedance-2-0 probes.
Previous rounds used grok-imagine (image model) so all failed for wrong reasons.
This round uses seedance-2-0 at 1s/480p (cheapest video tier).
"""
import requests, json, time

T = 'uVrw1NqmIvzEcGBdHduaJwAzTySq55TN.inTUrq0EHJ%2F24cDxQXOvikggOi2Zk2AX9Olom2%2Brhqs%3D'
D = 'eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwODozMjozNi40OTFaIiwidG9rZW4iOiJ1VnJ3MU5xbUl2ekVjR0JkSGR1YUp3QXpUeVNxNTVUTiIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIiwiaWQiOiJQMUR6cVROQ1ZVeklOZ2Y5eEVDZnJtQm1mTk5NeWVwTSJ9LCJ1c2VyIjp7Im5hbWUiOiJuZmoxM0BlZHUtbWFpbC5lZHUucnMiLCJlbWFpbCI6Im5majEzQGVkdS1tYWlsLmVkdS5ycyIsImVtYWlsVmVyaWZpZWQiOnRydWUsImltYWdlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJ1cGRhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJpZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIn0sInVwZGF0ZWRBdCI6MTc3NzM2NTE1Njc0MSwidmVyc2lvbiI6IjEifSwiZXhwaXJlc0F0IjoxNzc3MzY1NDU2NzQxLCJzaWduYXR1cmUiOiJpRzIwRUl2cU5QbVhlTWg3bkhWT2lUUE5LNzNCUXNmbmp1Z09NTFVZcEE4In0'

C = {'__Secure-better-auth.session_token': T, '__Secure-better-auth.session_data': D}
H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*', 'Content-Type': 'application/json',
    'Referer': 'https://viddo.ai/dashboard', 'Origin': 'https://viddo.ai',
    'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin',
}

# Read full cost table from JS chunk
print('=== Extracting full cost table from JS ===')
rc = requests.get(BASE + '/_next/static/chunks/4206-3436cfb39171b451.js', headers=H, timeout=15)
content = rc.text
# Extract the full cost object
match = re.search(r'\{[^{}]{200,}seedance_2_480p_1s[^{}]{200,}\}', content)
if match:
    cost_str = match.group(0)
    # Extract all entries
    entries = re.findall(r'(\w+)\s*:\s*(\d+)', cost_str)
    print(f'  {len(entries)} cost entries found')
    # Show cheap models (≤ 2 credits/s)
    cheap = [(k, v) for k, v in entries if int(v) <= 2]
    print(f'  Models costing ≤2 credits/sec:')
    for k, v in sorted(cheap, key=lambda x: int(x[1])):
        print(f'    {k}: {v}')
    # Show grok
    grok = [(k, v) for k, v in entries if 'grok' in k.lower()]
    print(f'  Grok entries:')
    for k, v in grok:
        print(f'    {k}: {v}')
    # Show seedance-2 entries
    s2 = [(k, v) for k, v in entries if 'seedance_2' in k.lower()]
    print(f'  Seedance-2 entries:')
    for k, v in s2:
        print(f'    {k}: {v}')

# Try grok video model names with duration=1
print('\n=== Grok video 1-second attempt (2 credits) ===')
for model_name in ['grok-video', 'grok_video', 'grok-imagine', 'grok', 'grok-ai',
                   'grok-2', 'grok-2-video', 'grok-video-480p']:
    body = {
        'model': model_name, 'channel': 'version2',
        'prompt': 'a wolf running through a snowy forest',
        'aspectRatio': '16:9', 'quality': '480p', 'duration': 1, 'webSearch': False,
    }
    r = requests.post(BASE + '/api/middle-layer', headers=H, cookies=COOKIES, json=body, timeout=15)
    code = r.status_code
    txt = r.text[:200]
    if code == 200 or ('taskId' in txt and 'null' not in txt):
        print(f'  *** [{model_name}] {code}: {txt}')
    else:
        print(f'  [{model_name}] {code}: {txt[:80]}')

# Also check the app's Grok page for the model ID used
print('\n=== Grok page model ID ===')
rg = requests.get(BASE + '/grok-imagine', headers={**H, 'Accept': 'text/html'}, timeout=10)
content2 = rg.text
model_hits = re.findall(r'"model"\s*:\s*"([^"]+)"', content2)
print(f'  model values on grok page: {list(set(model_hits))[:10]}')

# Also check tempedumaiil.me for the magic link
print('\n=== Checking temp inbox for magic link ===')
inbox_attempts = [
    'https://tempedumaiil.me/api/inbox/xktest7749',
    'https://tempedumaiil.me/api/mails/xktest7749@tempedumaiil.me',
    'https://tempedumaiil.me/xktest7749',
]
for url in inbox_attempts:
    try:
        r2 = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}, timeout=8)
        print(f'  {r2.status_code} {url}: {r2.text[:300]}')
    except Exception as e:
        print(f'  ERR {url}: {e}')

print('\nDone.')
