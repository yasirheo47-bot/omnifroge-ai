import base64, re, gzip, json

with open('rork', 'rb') as f:
    raw = f.read().decode('utf-8', errors='ignore')

items = re.split(r'(?=<item>)', raw)

for item in items:
    if 'generateSeedanceVideo' not in item and 'generateKlingVideo' not in item and 'generateSora2Video' not in item:
        continue
    method_m = re.search(r'<method><!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    if not method_m or method_m.group(1).strip() != 'POST':
        continue

    url_m = re.search(r'<url><!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    req_m = re.search(r'<request[^>]*base64="true"[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    res_m = re.search(r'<response[^>]*base64="true"[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)

    print(f'\n=== {url_m.group(1) if url_m else "?"} ===')

    if req_m:
        req = base64.b64decode(req_m.group(1).strip()).decode('utf-8', errors='ignore')
        if '\r\n\r\n' in req:
            body = req.split('\r\n\r\n', 1)[1]
            try: print('REQUEST BODY:', json.dumps(json.loads(body), indent=2)[:600])
            except: print('REQUEST BODY:', body[:400])

    if res_m:
        res_raw = base64.b64decode(res_m.group(1).strip())
        res_text = res_raw.decode('utf-8', errors='ignore')
        if '\r\n\r\n' in res_text:
            hdr, body = res_text.split('\r\n\r\n', 1)
            if 'gzip' in hdr.lower():
                try:
                    body = gzip.decompress(res_raw[res_raw.find(b'\r\n\r\n')+4:]).decode('utf-8', errors='ignore')
                except: pass
        else:
            body = res_text[-400:]
        try: print('RESPONSE:', json.dumps(json.loads(body), indent=2)[:600])
        except: print('RESPONSE:', body[:400])
    break  # just first one
