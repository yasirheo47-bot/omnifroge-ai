import base64, re

with open('rork', 'rb') as f:
    raw = f.read().decode('utf-8', errors='ignore')

cdata_re = re.compile(r'<(request|response)[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', re.DOTALL)

# also grab URLs
url_re = re.compile(r'<url><!\[CDATA\[(.*?)\]\]>', re.DOTALL)
urls = url_re.findall(raw)

print('=== ALL UNIQUE URLS/PATHS (supabase + zorqai api) ===')
seen = set()
for u in urls:
    if ('supabase' in u or 'zorqai' in u or 'functions' in u) and u not in seen:
        seen.add(u)
        print(' ', u)

print('\n=== recoverMyStuckMedia REQUEST+RESPONSE ===')
items = re.split(r'<item>', raw)
for item in items:
    if 'recoverMyStuckMedia' not in item:
        continue
    # extract request
    req_m = re.search(r'<request[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    res_m = re.search(r'<response[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    
    if req_m:
        try:
            req = base64.b64decode(req_m.group(1).strip()).decode('utf-8', errors='ignore')
        except:
            req = req_m.group(1)
        print('REQUEST:')
        print(req[:800])
        print()
    
    if res_m:
        try:
            res = base64.b64decode(res_m.group(1).strip()).decode('utf-8', errors='ignore')
        except:
            res = res_m.group(1)
        print('RESPONSE:')
        print(res[:800])
        print()

print('DONE')
