import base64, re

with open('rork', 'rb') as f:
    raw = f.read().decode('utf-8', errors='ignore')

keywords = ['service_role', 'servicekey', 'sb_secret', 'service_key', 'admin_key', 
            'recover', 'refund', 'add_credits', 'addcredits', 'credit_refill',
            'update_credits', 'updatecredits']

# search all base64 chunks (both request and response)
for tag in ('request', 'response'):
    chunks = re.findall(rf'<{tag}>([A-Za-z0-9+/=\s]{{100,}})</{tag}>', raw)
    for i, chunk in enumerate(chunks):
        try:
            decoded = base64.b64decode(chunk.strip()).decode('utf-8', errors='ignore')
            for kw in keywords:
                if kw in decoded.lower():
                    print(f'=== {tag.upper()} {i} [{kw}] ===')
                    # find the line containing the keyword
                    for line in decoded.splitlines():
                        if kw in line.lower():
                            print(f'  >> {line[:300]}')
                    break
        except Exception:
            pass

print('SEARCH COMPLETE')
