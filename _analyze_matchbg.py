import base64, xml.etree.ElementTree as ET, json, gzip

try:
    tree = ET.parse(r'c:\Users\ADMIN\Documents\rork.ak\match_bg')
    root = tree.getroot()
    items = root.findall('.//item')
    print(f'Total items: {len(items)}')
    for i, item in enumerate(items):
        url_el    = item.find('url')
        method_el = item.find('method')
        req_el    = item.find('request')
        resp_el   = item.find('response')
        url    = (url_el.text or '').strip()
        method = (method_el.text or '').strip() if method_el is not None else ''
        if 'viewmax' not in url.lower():
            continue
        print(f'\n{"="*60}')
        print(f'Item {i}  {method}  {url}')
        # request body
        if req_el is not None and req_el.text:
            try:
                raw = base64.b64decode(req_el.text.strip()).decode('utf-8', errors='replace')
                parts = raw.split('\r\n\r\n', 1)
                body = parts[1].strip() if len(parts) > 1 else ''
                if body:
                    try:
                        print('REQUEST BODY:', json.dumps(json.loads(body), indent=2)[:3000])
                    except:
                        print('REQUEST BODY:', body[:1000])
            except Exception as e:
                print(f'req decode err: {e}')
        # response body
        if resp_el is not None and resp_el.text:
            try:
                raw_b = base64.b64decode(resp_el.text.strip())
                raw_s = raw_b.decode('utf-8', errors='replace')
                sep   = b'\r\n\r\n'
                idx   = raw_b.find(sep)
                hdr   = raw_s[:idx] if idx >= 0 else ''
                body_b = raw_b[idx+4:] if idx >= 0 else raw_b
                if 'gzip' in hdr.lower():
                    try:
                        body = gzip.decompress(body_b).decode('utf-8', errors='replace')
                    except:
                        body = raw_s[idx+4:] if idx >= 0 else raw_s
                else:
                    body = body_b.decode('utf-8', errors='replace')
                body = body.strip()
                if body:
                    try:
                        print('RESPONSE BODY:', json.dumps(json.loads(body), indent=2)[:5000])
                    except:
                        print('RESPONSE BODY:', body[:2000])
            except Exception as e:
                print(f'resp decode err: {e}')
except Exception as e:
    print(f'FAILED: {e}')
    with open(r'c:\Users\ADMIN\Documents\rork.ak\match_bg', 'rb') as f:
        print('First 200 bytes:', f.read(200))
