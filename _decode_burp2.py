import base64
import xml.etree.ElementTree as ET
import urllib.parse
import json

tree = ET.parse(r'C:\Users\ADMIN\Documents\rork.ak\seedancevliewmaxbypass')
items = tree.findall('item')
print(f'Total items: {len(items)}\n')

# decode helper
def dec(el):
    if el is None: return b''
    txt = (el.text or '').strip()
    if not txt: return b''
    if el.get('base64','false') == 'true':
        try: return base64.b64decode(txt)
        except: return txt.encode()
    return txt.encode()

def body(raw: bytes) -> bytes:
    sep = b'\r\n\r\n'
    idx = raw.find(sep)
    return raw[idx+4:] if idx != -1 else raw

def headers_block(raw: bytes) -> str:
    sep = b'\r\n\r\n'
    idx = raw.find(sep)
    return raw[:idx].decode('utf-8','replace') if idx != -1 else ''

interesting = []

for i, item in enumerate(items):
    url    = item.findtext('url','').strip()
    method = item.findtext('method','').strip()
    status = item.findtext('status','').strip()
    
    req_raw  = dec(item.find('request'))
    resp_raw = dec(item.find('response'))
    
    req_body  = body(req_raw).decode('utf-8','replace')
    resp_body = body(resp_raw).decode('utf-8','replace')
    req_hdrs  = headers_block(req_raw)
    
    print(f'[{i:03d}] {method} {status} {url[:90]}')
    
    # flag anything that smells like detection / verification / human check
    keywords = ['captcha','recaptcha','turnstile','challenge','verify','human',
                'bot','fingerprint','cf-','__cf','perimeterx','datadome',
                'arcaptcha','hcaptcha','kasada','akamai','incapsula',
                'generate','seedance','video-generation','subscription','plan','upgrade']
    hit_kw = [k for k in keywords if k in url.lower() or k in resp_body.lower()[:500]]
    if hit_kw:
        print(f'  *** KEYWORDS: {hit_kw}')
        if resp_body.strip():
            try:
                parsed = json.loads(resp_body)
                print(f'  RESP JSON: {json.dumps(parsed, indent=2)[:600]}')
            except:
                print(f'  RESP: {resp_body[:400]}')
        interesting.append(i)
    print()
