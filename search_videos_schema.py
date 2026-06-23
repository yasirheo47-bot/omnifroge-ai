import base64, re, gzip, json

with open('rork', 'rb') as f:
    raw = f.read().decode('utf-8', errors='ignore')

items = re.split(r'(?=<item>)', raw)

for item in items:
    if 'generated_videos' not in item and 'model_medias' not in item:
        continue
    
    url_m = re.search(r'<url><!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    method_m = re.search(r'<method><!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    if not url_m or not method_m:
        continue
    
    url = url_m.group(1)
    method = method_m.group(1).strip()
    
    # only responses with actual data
    res_m = re.search(r'<response[^>]*base64="true"[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', item, re.DOTALL)
    if not res_m:
        continue
    
    res_raw = base64.b64decode(res_m.group(1).strip())
    res_text = res_raw.decode('utf-8', errors='ignore')
    
    if '\r\n\r\n' in res_text:
        headers_part, body_part = res_text.split('\r\n\r\n', 1)
        if 'gzip' in headers_part.lower():
            try:
                header_end = res_raw.find(b'\r\n\r\n')
                raw_body = res_raw[header_end+4:]
                body_part = gzip.decompress(raw_body).decode('utf-8', errors='ignore')
            except:
                pass
    else:
        body_part = res_text[-2000:]
    
    if not body_part.strip() or body_part.strip() in ('[]', '{}', ''):
        continue
    
    print(f'\n=== {method} {url[:100]} ===')
    # try to pretty print JSON
    try:
        data = json.loads(body_part)
        if isinstance(data, list) and data:
            print('COLUMNS:', list(data[0].keys()))
            print('FIRST ROW:', json.dumps(data[0], indent=2)[:1000])
        else:
            print(json.dumps(data, indent=2)[:600])
    except:
        print(body_part[:600])

print('\nDONE')
