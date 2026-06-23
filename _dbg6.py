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

def test(label, body):
    r = requests.post(BASE + '/api/middle-layer', headers=HEADERS, cookies=COOKIES, json=body, timeout=15)
    print(f'  [{label}] {r.status_code}: {r.text[:200]}')

# kling-2-6 with different qualities/aspects
for q in ['720p', '1080p', 'standard', 'high', 'pro']:
    test(f'kling-2-6 quality={q}', {'model': 'kling-2-6', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': q, 'duration': 5, 'webSearch': False})

# kling-2-6 with no quality
test('kling-2-6 no quality', {'model': 'kling-2-6', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'duration': 5})

# kling-2-6 with duration=10
test('kling-2-6 dur=10', {'model': 'kling-2-6', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 10})

# try kling-1-6 (older?)
test('kling-1-6', {'model': 'kling-1-6', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5})

# try kling (no version)
test('kling', {'model': 'kling', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5})

# seedance-2-0 just to confirm it still 400s for video models
test('seedance-2-0', {'model': 'seedance-2-0', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False})

# wan2-5
test('wan2-5', {'model': 'wan2-5', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False})

# wan-2-1
test('wan-2-1', {'model': 'wan-2-1', 'channel': 'version2', 'prompt': 'wolf', 'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False})

# nano-banana-2 (video-capable variant?)
test('nano-banana-2 no quality', {'model': 'nano-banana-2', 'channel': 'version2', 'prompt': 'wolf'})
test('nano-banana-pro no quality', {'model': 'nano-banana-pro', 'channel': 'version2', 'prompt': 'wolf'})

# image models
test('midjourney', {'model': 'midjourney', 'channel': 'version2', 'prompt': 'wolf'})
test('text-to-image', {'model': 'text-to-image', 'channel': 'version2', 'prompt': 'wolf'})
