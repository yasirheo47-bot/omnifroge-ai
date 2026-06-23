"""
Deep analysis of viddo.io Burp XML export.
Extracts: all unique hosts, endpoints, auth tokens, API keys, request/response bodies.
"""
import base64, re, sys
from xml.etree import ElementTree as ET

FILE = 'viddo.io'
out  = []

def dec(b64_text):
    try:
        return base64.b64decode(b64_text).decode('utf-8', errors='replace')
    except Exception:
        return ''

def pr(*a):
    s = ' '.join(str(x) for x in a)
    out.append(s)
    print(s)

pr("=== VIDDO.IO BURP XML DEEP ANALYSIS ===\n")

# Parse incrementally due to 229MB size
context = ET.iterparse(FILE, events=('end',))

items_seen = 0
viddo_items = []
all_hosts = set()
all_paths = set()
tokens = {}
api_keys = {}
endpoints = {}

for event, elem in context:
    if elem.tag != 'item':
        continue
    items_seen += 1
    
    host  = (elem.findtext('host') or '').strip()
    url   = (elem.findtext('url') or '').strip()
    path  = (elem.findtext('path') or '').strip()
    meth  = (elem.findtext('method') or '').strip()
    stat  = (elem.findtext('status') or '').strip()
    mime  = (elem.findtext('mimetype') or '').strip()
    
    req_el  = elem.find('request')
    resp_el = elem.find('response')
    
    req_raw  = ''
    resp_raw = ''
    
    if req_el is not None and req_el.text:
        if req_el.get('base64') == 'true':
            req_raw = dec(req_el.text)
        else:
            req_raw = req_el.text or ''
    
    if resp_el is not None and resp_el.text:
        if resp_el.get('base64') == 'true':
            resp_raw = dec(resp_el.text)
        else:
            resp_raw = resp_el.text or ''
    
    all_hosts.add(host)
    
    # Only focus on viddo.ai / its backend
    is_viddo = 'viddo' in host or 'viddo' in url
    
    if is_viddo:
        all_paths.add(f"{meth} {path}")
        viddo_items.append({
            'url': url, 'host': host, 'path': path, 'method': meth,
            'status': stat, 'mime': mime,
            'req': req_raw[:4000], 'resp': resp_raw[:4000],
        })
    
    # Extract auth tokens from ALL requests
    for header_pattern in [
        r'[Aa]uthorization:\s*([Bb]earer\s+[\w\-\.]+)',
        r'[Aa]uthorization:\s*([\w\-\.]{100,})',
        r'x-api-key:\s*([\w\-\.]+)',
        r'[Aa]pi[_-][Kk]ey:\s*([\w\-\.]+)',
    ]:
        for m in re.finditer(header_pattern, req_raw):
            val = m.group(1)
            if len(val) > 20:
                tokens[val[:80]] = url
    
    # Extract API keys from response bodies
    for kp in [
        r'"token"\s*:\s*"([^"]{20,})"',
        r'"access_token"\s*:\s*"([^"]{20,})"',
        r'"jwt"\s*:\s*"([^"]{20,})"',
        r'"api_?key"\s*:\s*"([^"]{20,})"',
        r'"key"\s*:\s*"([^"]{20,})"',
        r'"auth"\s*:\s*"([^"]{20,})"',
    ]:
        for m in re.finditer(kp, resp_raw):
            val = m.group(1)
            api_keys[val[:80]] = url
    
    # Track response endpoints
    key = f"{meth} {path}"
    if is_viddo and key not in endpoints:
        endpoints[key] = {'status': stat, 'url': url, 'resp_preview': resp_raw[:500]}
    
    elem.clear()

pr(f"\nTotal items: {items_seen}")
pr(f"Viddo-specific items: {len(viddo_items)}")
pr(f"\n=== ALL HOSTS ===")
for h in sorted(all_hosts):
    pr(f"  {h}")

pr(f"\n=== VIDDO ENDPOINTS ({len(all_paths)}) ===")
for p in sorted(all_paths):
    pr(f"  {p}")

pr(f"\n=== ENDPOINTS WITH RESPONSES ===")
for k, v in sorted(endpoints.items()):
    pr(f"\n[{k}] status={v['status']}")
    pr(f"  URL: {v['url']}")
    pr(f"  RESP: {v['resp_preview'][:300]}")

pr(f"\n=== AUTH TOKENS FOUND ({len(tokens)}) ===")
for t, u in list(tokens.items())[:20]:
    pr(f"  {t[:80]}")
    pr(f"    from: {u}")

pr(f"\n=== API KEYS IN RESPONSES ({len(api_keys)}) ===")
for k, u in list(api_keys.items())[:20]:
    pr(f"  {k[:80]}")
    pr(f"    from: {u}")

pr(f"\n=== FULL VIDDO REQUEST/RESPONSE DUMP ===")
for item in viddo_items:
    pr(f"\n{'='*60}")
    pr(f"[{item['method']}] {item['url']} status={item['status']}")
    pr(f"--- REQUEST ---")
    pr(item['req'][:2000])
    pr(f"--- RESPONSE ---")
    pr(item['resp'][:2000])

with open('_viddo_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
pr(f"\n\nSaved to _viddo_analysis.txt")
