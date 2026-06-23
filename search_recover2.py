import base64, re, gzip

with open('rork', 'rb') as f:
    raw = f.read().decode('utf-8', errors='ignore')

# grab all items
items = re.split(r'(?=<item>)', raw)

for item in items:
    if 'recoverMyStuckMedia' not in item:
        continue
    
    url_m = re.search(r'<url><!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    method_m = re.search(r'<method><!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    if not method_m or method_m.group(1).strip() != 'POST':
        continue
    
    print(f'URL: {url_m.group(1) if url_m else "?"}')
    
    req_m = re.search(r'<request[^>]*base64="true"[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    res_m = re.search(r'<response[^>]*base64="true"[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    
    if req_m:
        req_raw = base64.b64decode(req_m.group(1).strip())
        req_text = req_raw.decode('utf-8', errors='ignore')
        # find body (after double CRLF)
        if '\r\n\r\n' in req_text:
            body = req_text.split('\r\n\r\n', 1)[1]
        else:
            body = req_text[-500:]
        print('REQUEST BODY:', repr(body[:500]))
    
    if res_m:
        res_raw = base64.b64decode(res_m.group(1).strip())
        res_text = res_raw.decode('utf-8', errors='ignore')
        
        # try gzip if needed
        if '\r\n\r\n' in res_text:
            headers_part, body_part = res_text.split('\r\n\r\n', 1)
            if 'gzip' in headers_part.lower() or 'Content-Encoding' in headers_part:
                try:
                    # body might be raw gzip bytes - work from raw
                    header_end = res_raw.find(b'\r\n\r\n')
                    raw_body = res_raw[header_end+4:]
                    body_part = gzip.decompress(raw_body).decode('utf-8', errors='ignore')
                except:
                    pass
        else:
            body_part = res_text[-500:]
        
        print('RESPONSE BODY:', repr(body_part[:600]))
    
    print('---')
