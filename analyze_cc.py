import json

items = json.load(open('cc_extracted.json', encoding='utf-8'))
out = []

for it in items:
    url = it['url']
    if '/references' in url and it['method'] in ('GET', 'POST'):
        out.append("=" * 60)
        out.append(f"{it['method']} {url}")
        out.append("--- REQUEST ---")
        out.append(it['request'][:3000])
        out.append("--- RESPONSE ---")
        out.append(it['response'][:5000])
        out.append("")

# Also show generate calls with references
for it in items:
    url = it['url']
    if '/generate' in url and 'reference' in (it['request'] + it['response']).lower():
        out.append("=" * 60)
        out.append(f"GENERATE CALL: {it['method']} {url}")
        out.append("--- REQUEST ---")
        out.append(it['request'][:3000])
        out.append("--- RESPONSE ---")
        out.append(it['response'][:3000])
        out.append("")

with open('cc_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Written cc_analysis.txt ({len(out)} lines)")
