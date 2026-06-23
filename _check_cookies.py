import json

h = json.load(open('onlyvideogenpart.har', encoding='utf-8'))

# find cookies sent on any viewmax request
for e in h['log']['entries']:
    url = e['request']['url']
    if 'viewmax.io' not in url:
        continue
    for hdr in e['request']['headers']:
        if hdr['name'].lower() == 'cookie':
            print(f"URL: {url[:80]}")
            print(f"COOKIE: {hdr['value'][:400]}")
            print()
            break
