import requests, json

BASE = 'https://viddo.ai'
SESSION_TOKEN = 'CiqAykZneKhsNT1S6iRNR75QS6Cj2n2X.g4pzFoA9Mql5aDBC3K+UuqgVTxeoOndb+eTAmGk1GKc='
SESSION_DATA = ('eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwNjozNzo1OC41MjRaIiwidG9rZW4iOiJDaXFBeWtabmVLaHNOVDFTNmlSTlI3NVFTNkNqMm4yWCIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6InNYWFZXQUthbWlJQjdlN001WDgzZG5TclRtcFJ1UXo4IiwiaWQiOiJTOVRQVFN4TWFFdUhKQTNmUzRURmJubHdDZmE3WW1hcyJ9LCJ1c2VyIjp7Im5hbWUiOiJhaHk0OEB0ZW1wZWR1bWFpbC5tZSIsImVtYWlsIjoiYWh5NDhAdGVtcGVkdW1haWwubWUiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpbWFnZSI6bnVsbCwiY3JlYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwidXBkYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwiaWQiOiJzWFhWV0FLYW1pSUI3ZTdNNVg4M2RuU3JUbXBSdVF6OCJ9LCJ1cGRhdGVkQXQiOjE3NzczNTg2MTExMzMsInZlcnNpb24iOiIxIn0sImV4cGlyZXNBdCI6MTc3NzM1ODkxMTEzMywic2lnbmF0dXJlIjoidy1vU3BkNG1UTXhMUl9wNHFNc3FVTVhWbkEzc2R5N1lteWNFb3BsT0VzdyJ9')
COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}

def post(headers, body, label):
    print(f'\n=== {label} ===')
    r = requests.post(BASE + '/api/middle-layer', headers=headers, cookies=COOKIES, json=body, timeout=30)
    print(f'  {r.status_code}:', r.text[:400])

BASE_BODY = {'model': 'kling-2-6', 'channel': 'version2', 'prompt': 'wolf in snow', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'freeMode': True}

# Test 1: Full browser-like headers
full_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/json',
    'Referer': 'https://viddo.ai/dashboard',
    'Origin': 'https://viddo.ai',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'trailers',
}
post(full_headers, BASE_BODY, 'Full browser headers')

# Test 2: Add Next.js specific headers
next_headers = dict(full_headers)
next_headers['Next-Url'] = '/dashboard'
next_headers['Next-Router-State-Tree'] = '%5B%22%22%2C%7B%7D%2Cnull%2Cnull%2Ctrue%5D'
post(next_headers, BASE_BODY, 'With Next.js headers')

# Test 3: minimal body - remove empty string key
clean_body = {'model': 'kling-2-6', 'channel': 'version2', 'prompt': 'wolf in snow', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False, 'freeMode': True}
post(full_headers, clean_body, 'Clean body no empty key')

# Test 4: different channel
body4 = dict(clean_body)
body4['channel'] = 'version1'
post(full_headers, body4, 'channel=version1')

# Test 5: no channel field
body5 = {k: v for k, v in clean_body.items() if k != 'channel'}
post(full_headers, body5, 'No channel field')

# Test 6: Add generationType
body6 = dict(clean_body)
body6['generationType'] = 'text'
post(full_headers, body6, 'With generationType=text')

# Test 7: check user credits/plan first
print('\n=== Credits check ===')
r2 = requests.get(BASE + '/api/user/credits', headers=full_headers, cookies=COOKIES, timeout=10)
print(f'  {r2.status_code}:', r2.text[:400])
r3 = requests.get(BASE + '/api/user/plan', headers=full_headers, cookies=COOKIES, timeout=10)
print(f'  plan: {r3.status_code}:', r3.text[:400])
