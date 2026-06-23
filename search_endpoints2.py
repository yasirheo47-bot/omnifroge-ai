import base64, re, sys

with open('rork', 'rb') as f:
    raw = f.read().decode('utf-8', errors='ignore')

# Correct pattern: <![CDATA[...]]>
cdata_re = re.compile(r'<(request|response)[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', re.DOTALL)

found_endpoints = set()
found_keys = set()
welcome_hits = []
js_bundle_hits = []

for match in cdata_re.finditer(raw):
    tag = match.group(1)
    content = match.group(2).strip()
    
    # try base64 decode
    try:
        decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
    except Exception:
        decoded = content
    
    # edge function calls
    for m in re.finditer(r'functions/v1/(\w+)', decoded):
        found_endpoints.add(m.group(0))
    
    # rpc calls
    for m in re.finditer(r'rest/v1/rpc/(\w+)', decoded):
        found_endpoints.add(m.group(0))
    
    # HS256 JWTs (service role)
    for m in re.finditer(r'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+', decoded):
        found_keys.add(f'HS256 JWT [{tag}]: {m.group(0)}')
    
    # sb_secret keys  
    for m in re.finditer(r'sb_secret_[A-Za-z0-9_\-]+', decoded):
        found_keys.add(m.group(0))
    
    # any long bearer tokens
    for m in re.finditer(r'Bearer (eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)', decoded):
        token = m.group(1)
        # decode header to check alg
        try:
            hdr = json_decode(token.split('.')[0])
            found_keys.add(f'Bearer alg={hdr} [{tag}]: {token[:60]}...')
        except:
            found_keys.add(f'Bearer [{tag}]: {token[:60]}...')
    
    # welcome/coupon/recover keywords
    for kw in ['welcome_credit', 'grant_welcome', 'redeem_coupon', 'coupon', 'recoverMyStuck', 'has_received_welcome', 'welcome_grant']:
        if kw.lower() in decoded.lower():
            idx = decoded.lower().index(kw.lower())
            welcome_hits.append(f'[{tag.upper()}] kw={kw}:\n  {decoded[max(0,idx-80):idx+200]}\n')
    
    # Next.js bundle / NEXT_PUBLIC env vars (might have keys)
    if 'NEXT_PUBLIC_SUPABASE' in decoded or 'supabase' in decoded.lower() and len(decoded) > 50000:
        for m in re.finditer(r'NEXT_PUBLIC_SUPABASE[A-Z_]+=.{5,80}', decoded):
            js_bundle_hits.append(m.group(0))

import json as _json
def json_decode(s):
    s += '=' * (-len(s) % 4)
    return _json.loads(base64.urlsafe_b64decode(s))

print('=== EDGE FUNCTION ENDPOINTS ===')
for ep in sorted(found_endpoints):
    print(' ', ep)

print('\n=== POTENTIAL SERVICE KEYS ===')
for k in found_keys:
    print(' ', k)

print(f'\n=== WELCOME/COUPON HITS ({len(welcome_hits)}) ===')
for h in welcome_hits[:10]:
    print(h)

print(f'\n=== JS BUNDLE ENV VARS ({len(js_bundle_hits)}) ===')
for h in js_bundle_hits[:10]:
    print(' ', h)

print('DONE')
