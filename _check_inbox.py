import requests, json, re

# Try common temp mail API patterns for tempedumaiil.me
email = 'xktest7749'
domain = 'tempedumaiil.me'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0', 'Accept': 'application/json'}

attempts = [
    f'https://{domain}/api/mails/{email}',
    f'https://{domain}/api/email/{email}',
    f'https://{domain}/api/inbox/{email}',
    f'https://{domain}/mail/{email}',
    f'https://{domain}/inbox/{email}@{domain}',
    f'https://api.{domain}/mails/{email}',
    f'https://api.{domain}/inbox?email={email}@{domain}',
    f'https://{domain}/api/messages?email={email}@{domain}',
]

for url in attempts:
    try:
        r = requests.get(url, headers=headers, timeout=8)
        print(f'{r.status_code} {url}')
        if r.status_code == 200 and '<html' not in r.text[:50]:
            print('  ', r.text[:500])
    except Exception as e:
        print(f'ERR {url}: {e}')
