import re

with open('sora2fix_analysis.txt', encoding='utf-8') as f:
    content = f.read()

items = content.split('=' * 60)
results = []
for item in items:
    body_match = re.search(r'REQ BODY: (.+)', item)
    if body_match and body_match.group(1).strip():
        url_match = re.search(r'URL: (.+)', item)
        resp_match = re.search(r'RESP BODY: (.+)', item, re.DOTALL)
        results.append({
            'url': url_match.group(1).strip() if url_match else '?',
            'req': body_match.group(1).strip()[:500],
            'resp': resp_match.group(1).strip()[:300] if resp_match else ''
        })

with open('sora2_key_calls.txt', 'w', encoding='utf-8') as f:
    for r in results:
        f.write(f"URL: {r['url']}\n")
        f.write(f"REQ: {r['req']}\n")
        f.write(f"RESP: {r['resp']}\n")
        f.write('-' * 80 + '\n')

print(f"Found {len(results)} items with request bodies")
