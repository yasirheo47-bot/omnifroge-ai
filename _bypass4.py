"""
Find credit cost per model from JS bundles.
Also try: testMode, debugMode, stagingMode, betaMode, sponsorMode.
Check if 2 credits is enough for seedance-2-0 at minimum settings.
"""
import requests, json, re

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

# ── 1. Scan ALL JS chunks for credit cost tables ──
print('=== Scanning JS for credit costs ===')
r_home = requests.get(BASE, headers={**H, 'Accept': 'text/html'}, timeout=10)
chunks = list(set(re.findall(r'/_next/static/[^\s"\']+\.js', r_home.text)))

credit_cost_found = False
for chunk in chunks:
    try:
        rc = requests.get(BASE + chunk, headers=H, timeout=15)
        content = rc.text

        # Look for credit cost tables or model cost maps
        cost_hits = re.findall(r'.{0,100}(?:seedance|credit.{0,10}cost|cost.{0,10}credit|credits.{0,5}model|model.{0,5}credit).{0,200}', content, re.I)
        webhook_hits = re.findall(r'.{0,50}(?:whsec|webhook.secret|WEBHOOK_SECRET).{0,100}', content, re.I)
        mode_hits = re.findall(r'.{0,30}(?:testMode|debugMode|stagingMode|betaMode|sponsorMode|proMode|vipMode).{0,100}', content, re.I)

        if cost_hits:
            print(f'\n[COST] chunk: {chunk}')
            for h2 in cost_hits[:3]:
                print(f'  {h2[:200]}')
            credit_cost_found = True

        if webhook_hits:
            print(f'\n[WEBHOOK] chunk: {chunk}')
            for h2 in webhook_hits[:2]:
                print(f'  {h2}')

        if mode_hits:
            print(f'\n[MODE FLAGS] chunk: {chunk}')
            for h2 in mode_hits[:3]:
                print(f'  {h2[:200]}')

    except Exception as e:
        pass

if not credit_cost_found:
    print('No credit cost tables found in JS (probably server-side config)')

# ── 2. Try all mode flags ──
print('\n=== Mode flag variants ===')
BASE_BODY = {
    'model': 'seedance-2-0', 'channel': 'version2',
    'prompt': 'wolf in snow', 'aspectRatio': '16:9',
    'quality': '480p', 'duration': 5, 'webSearch': False,
}
mode_flags = [
    'testMode', 'debugMode', 'stagingMode', 'betaMode', 'sponsorMode',
    'proMode', 'vipMode', 'previewMode', 'demoMode', 'trialMode',
    'gifMode', 'giftMode', 'rewardMode', 'promoMode', 'campaignMode',
    'affiliateMode', 'partnerMode', 'influencerMode', 'creatorMode',
    'unlimitedMode', 'infiniteMode', 'noChargeMode', 'zeroCostMode',
    'freeTrial', 'freeTrialMode', 'isTrial', 'isDemo', 'isTest',
    'isBeta', 'isFree', 'isSponsor', 'isPartner', 'isAffiliate',
    'isInfluencer', 'isCreator', 'isVip', 'isPro', 'isAdmin',
]
for flag in mode_flags:
    body = {**BASE_BODY, flag: True}
    r = requests.post(BASE + '/api/middle-layer', headers=H, cookies=COOKIES, json=body, timeout=12)
    if r.status_code != 402:
        print(f'  *** [{flag}] {r.status_code}: {r.text[:200]}')

print('  (only non-402 results shown above)')

# ── 3. Check pricing page for credit cost info ──
print('\n=== Pricing page credit info ===')
rp = requests.get(BASE + '/price', headers={**H, 'Accept': 'text/html'}, timeout=15)
# Look for seedance and credit numbers near it
content = rp.text
# Find credit costs table
costs = re.findall(r'.{0,50}(?:seedance|Seedance).{0,200}', content)
for c in costs[:3]:
    print(f'  {c[:200]}')

# ── 4. Check the pricing API ──
print('\n=== Pricing API ===')
for path in ['/api/price', '/api/pricing', '/api/models', '/api/models/pricing',
             '/api/generation/cost', '/api/credit-cost']:
    rapi = requests.get(BASE + path, headers=H, cookies=COOKIES, timeout=8)
    if rapi.status_code not in (404, 405) and '<html' not in rapi.text[:20]:
        print(f'  {path}: {rapi.status_code}: {rapi.text[:300]}')

print('\nDone.')
