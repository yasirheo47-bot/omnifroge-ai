import base64, re

with open('rork', 'rb') as f:
    raw = f.read().decode('utf-8', errors='ignore')

keywords = [
    'welcome', 'coupon', 'recover', 'refund', 'stuck',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',  # HS256 JWT (service role format)
    'functions/v1/', 'edge', 'rpc',
    'grant', 'reward', 'bonus', 'promo',
]

found_endpoints = set()
found_keys = set()

for tag in ('request', 'response'):
    chunks = re.findall(rf'<{tag}>([A-Za-z0-9+/=\s]{{100,}})</{tag}>', raw)
    for i, chunk in enumerate(chunks):
        try:
            decoded = base64.b64decode(chunk.strip()).decode('utf-8', errors='ignore')
            
            # find edge function calls
            for m in re.finditer(r'functions/v1/(\w+)', decoded):
                found_endpoints.add(m.group(0))
            
            # find rpc calls
            for m in re.finditer(r'rest/v1/rpc/(\w+)', decoded):
                found_endpoints.add(m.group(0))
            
            # find HS256 JWTs (service role)
            for m in re.finditer(r'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+', decoded):
                found_keys.add(f'HS256_JWT_{tag}_{i}: {m.group(0)[:80]}...')
            
            # find sb_secret or service keys
            for m in re.finditer(r'sb_secret_[A-Za-z0-9_]+', decoded):
                found_keys.add(m.group(0))
            
            # welcome/coupon hits
            for kw in ['welcome_credit', 'grant_welcome', 'redeem', 'coupon', 'recoverMyStuck']:
                if kw.lower() in decoded.lower():
                    print(f'[{tag.upper()} {i}] keyword={kw}')
                    idx = decoded.lower().index(kw.lower())
                    print(f'  context: {decoded[max(0,idx-100):idx+200]}')
                    print()
        except Exception:
            pass

print('\n=== ALL EDGE FUNCTION ENDPOINTS ===')
for ep in sorted(found_endpoints):
    print(' ', ep)

print('\n=== POTENTIAL SERVICE KEYS ===')
for k in found_keys:
    print(' ', k)

print('\nDONE')
