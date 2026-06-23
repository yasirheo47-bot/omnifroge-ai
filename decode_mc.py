import base64, xml.etree.ElementTree as ET, json

tree = ET.parse(r'c:\Users\ADMIN\Documents\rork.ak\motioncontrol')
root = tree.getroot()
items = root.findall('.//item')
print(f'Total items: {len(items)}')
for i, item in enumerate(items):
    url_el = item.find('url')
    method_el = item.find('method')
    req_el = item.find('request')
    resp_el = item.find('response')
    if url_el is None:
        continue
    url = url_el.text or ''
    method = method_el.text if method_el is not None else ''
    print(f'\n=== Item {i} ===')
    print(f'URL: {url}')
    print(f'Method: {method}')
    if req_el is not None:
        try:
            raw = base64.b64decode(req_el.text).decode('utf-8', errors='replace')
            parts = raw.split('\r\n\r\n', 1)
            if len(parts) > 1:
                body = parts[1][:3000]
                print(f'Request body:\n{body}')
            else:
                print(f'Request headers only:\n{raw[:500]}')
        except Exception as e:
            print(f'Req decode error: {e}')
    if resp_el is not None:
        try:
            raw = base64.b64decode(resp_el.text).decode('utf-8', errors='replace')
            parts = raw.split('\r\n\r\n', 1)
            if len(parts) > 1:
                body = parts[1][:3000]
                print(f'Response body:\n{body}')
        except Exception as e:
            print(f'Resp decode error: {e}')
