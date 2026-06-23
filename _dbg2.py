import requests, json

BASE = 'https://viddo.ai'
SESSION_TOKEN = 'CiqAykZneKhsNT1S6iRNR75QS6Cj2n2X.g4pzFoA9Mql5aDBC3K+UuqgVTxeoOndb+eTAmGk1GKc='
SESSION_DATA = ('eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwNjozNzo1OC41MjRaIiwidG9rZW4iOiJDaXFBeWtabmVLaHNOVDFTNmlSTlI3NVFTNkNqMm4yWCIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6InNYWFZXQUthbWlJQjdlN001WDgzZG5TclRtcFJ1UXo4IiwiaWQiOiJTOVRQVFN4TWFFdUhKQTNmUzRURmJubHdDZmE3WW1hcyJ9LCJ1c2VyIjp7Im5hbWUiOiJhaHk0OEB0ZW1wZWR1bWFpbC5tZSIsImVtYWlsIjoiYWh5NDhAdGVtcGVkdW1haWwubWUiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpbWFnZSI6bnVsbCwiY3JlYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwidXBkYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwiaWQiOiJzWFhWV0FLYW1pSUI3ZTdNNVg4M2RuU3JUbXBSdVF6OCJ9LCJ1cGRhdGVkQXQiOjE3NzczNTg2MTExMzMsInZlcnNpb24iOiIxIn0sImV4cGlyZXNBdCI6MTc3NzM1ODkxMTEzMywic2lnbmF0dXJlIjoidy1vU3BkNG1UTXhMUl9wNHFNc3FVTVhWbkEzc2R5N1lteWNFb3BsT0VzdyJ9')
COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Content-Type': 'application/json',
    'Origin': 'https://viddo.ai',
    'Referer': 'https://viddo.ai/',
}

# 1. Check session
print('=== 1. Session check ===')
r = requests.get(BASE + '/api/auth/get-session', headers=HEADERS, cookies=COOKIES, timeout=10)
print(f'  {r.status_code}:', r.text[:300])

# 2. Try without freeMode
print('\n=== 2. No freeMode flag ===')
body = {'model': 'kling-2-6', 'channel': 'version2', 'prompt': 'wolf in snow', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False}
r = requests.post(BASE + '/api/middle-layer', headers=HEADERS, cookies=COOKIES, json=body, timeout=30)
print(f'  {r.status_code}:', r.text[:500])

# 3. Try with quality=720p (maybe 480p is invalid now)
print('\n=== 3. quality=720p ===')
body2 = {'model': 'kling-2-6', 'channel': 'version2', 'prompt': 'wolf in snow', 'aspectRatio': '16:9', 'quality': '720p', 'duration': 5, 'webSearch': False, 'freeMode': True}
r = requests.post(BASE + '/api/middle-layer', headers=HEADERS, cookies=COOKIES, json=body2, timeout=30)
print(f'  {r.status_code}:', r.text[:500])

# 4. Try sora2 (was working before)
print('\n=== 4. sora2 ===')
body3 = {'model': 'sora2', 'channel': 'version2', 'prompt': 'wolf in snow', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'freeMode': True, '': []}
r = requests.post(BASE + '/api/middle-layer', headers=HEADERS, cookies=COOKIES, json=body3, timeout=30)
print(f'  {r.status_code}:', r.text[:500])
