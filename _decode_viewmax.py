import base64, re

with open(r'c:\Users\ADMIN\Documents\rork.ak\seedancevliewmaxbypass', 'r') as f:
    content = f.read()

items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)

for item in items:
    url_m = re.search(r'<url><!\[CDATA\[(.*?)\]\]>', item)
    method_m = re.search(r'<method><!\[CDATA\[(.*?)\]\]>', item)
    req_m = re.search(r'<request base64="true"><!\[CDATA\[(.*?)\]\]>', item)
    resp_m = re.search(r'<response base64="true"><!\[CDATA\[(.*?)\]\]>', item)

    if url_m:
        url = url_m.group(1)
        if 'video-generation/generate' in url or 'video-generation/status' in url or 'r2/upload' in url:
            print('='*80)
            print('URL:', url)
            if method_m:
                print('METHOD:', method_m.group(1))
            if req_m:
                try:
                    decoded = base64.b64decode(req_m.group(1)).decode('utf-8', errors='replace')
                    parts = decoded.split('\r\n\r\n', 1)
                    body = parts[1][:3000] if len(parts) > 1 else decoded[:1000]
                    print('REQUEST BODY:', body)
                except Exception as e:
                    print('REQ DECODE ERR:', e)
            if resp_m:
                try:
                    decoded = base64.b64decode(resp_m.group(1)).decode('utf-8', errors='replace')
                    parts = decoded.split('\r\n\r\n', 1)
                    body = parts[1][:3000] if len(parts) > 1 else decoded[:1000]
                    print('RESPONSE BODY:', body)
                except Exception as e:
                    print('RESP DECODE ERR:', e)
            print()
