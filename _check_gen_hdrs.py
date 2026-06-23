import json
h=json.load(open('onlyvideogenpart.har',encoding='utf-8'))
e=[x for x in h['log']['entries'] if 'viewmax.io/api/video-generation/generate' in x['request']['url']]
entry=e[0]['request']
print("=== HEADERS ===")
for hdr in entry['headers']:
    print(f'{hdr["name"]}: {hdr["value"][:200]}')
print("\n=== BODY ===")
print(entry.get('postData',{}).get('text',''))
