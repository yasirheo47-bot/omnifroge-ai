import requests, json

BASE = 'https://viddo.ai'
SESSION_TOKEN = 'CiqAykZneKhsNT1S6iRNR75QS6Cj2n2X.g4pzFoA9Mql5aDBC3K+UuqgVTxeoOndb+eTAmGk1GKc='
SESSION_DATA = ('eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwNjozNzo1OC41MjRaIiwidG9rZW4iOiJDaXFBeWtabmVLaHNOVDFTNmlSTlI3NVFTNkNqMm4yWCIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6InNYWFZXQUthbWlJQjdlN001WDgzZG5TclRtcFJ1UXo4IiwiaWQiOiJTOVRQVFN4TWFFdUhKQTNmUzRURmJubHdDZmE3WW1hcyJ9LCJ1c2VyIjp7Im5hbWUiOiJhaHk0OEB0ZW1wZWR1bWFpbC5tZSIsImVtYWlsIjoiYWh5NDhAdGVtcGVkdW1haWwubWUiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpbWFnZSI6bnVsbCwiY3JlYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwidXBkYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwiaWQiOiJzWFhWV0FLYW1pSUI3ZTdNNVg4M2RuU3JUbXBSdVF6OCJ9LCJ1cGRhdGVkQXQiOjE3NzczNTg2MTExMzMsInZlcnNpb24iOiIxIn0sImV4cGlyZXNBdCI6MTc3NzM1ODkxMTEzMywic2lnbmF0dXJlIjoidy1vU3BkNG1UTXhMUl9wNHFNc3FVTVhWbkEzc2R5N1lteWNFb3BsT0VzdyJ9')
COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/json',
    'Referer': 'https://viddo.ai/dashboard',
    'Origin': 'https://viddo.ai',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

# 1. List ALL recent 20 creations to see kling-2-6 attempt
print('=== All recent creations (20) ===')
body = {'types': ['video'], 'keyword': '', 'keywordScope': 'prompt', 'models': [], 'page': 1, 'pageSize': 20}
r = requests.post(BASE + '/api/creation/get-user-creations-for-creations', headers=HEADERS, cookies=COOKIES, json=body, timeout=15)
d = r.json()
lst = d.get('creations', {}).get('list', [])
print(f'count: {len(lst)}')
for c in lst[:8]:
    print(f"  {c.get('created_at','')[:19]} | model={c.get('model_id')} | status={c.get('status_text','')[:40]} | id={c.get('id')}")

# 2. Check credits via the subscription info endpoint
print('\n=== Subscription info ===')
for path in ['/api/subscription/info', '/api/user/subscription', '/api/billing/subscription']:
    r2 = requests.get(BASE + path, headers=HEADERS, cookies=COOKIES, timeout=10)
    if r2.status_code != 404 and r2.status_code != 405:
        try:
            print(f'{path}: {r2.status_code}:', r2.json())
        except:
            if '<html' not in r2.text[:20]:
                print(f'{path}: {r2.status_code}:', r2.text[:200])

# 3. The ultra-minimal body tests
print('\n=== Ultra minimal body tests ===')
test_bodies = [
    {'model': 'kling-2-6', 'prompt': 'wolf'},
    {'model': 'hailuo', 'prompt': 'wolf', 'channel': 'version2', 'aspectRatio': '16:9', 'quality': '720p', 'duration': 5},
    {'model': 'hailuo', 'prompt': 'wolf', 'channel': 'version2', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'freeMode': True},
    {'model': 'nano-banana', 'prompt': 'wolf', 'channel': 'version2', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False},
]
for b in test_bodies:
    r3 = requests.post(BASE + '/api/middle-layer', headers=HEADERS, cookies=COOKIES, json=b, timeout=15)
    print(f"  model={b['model']} → {r3.status_code}: {r3.text[:150]}")
