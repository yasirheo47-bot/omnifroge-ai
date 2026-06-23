"""
Fetch zorqai.com's main JS bundle and search for recoverMyStuckMedia / credit recovery logic.
"""
import requests, re, json

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

# get main page to find JS bundle URLs
r = s.get('https://zorqai.com/', timeout=15)
html = r.text

# find JS files
js_urls = re.findall(r'src="(/assets/[^"]+\.js)"', html)
print(f"Found {len(js_urls)} JS bundles")
for u in js_urls[:5]:
    print(f"  {u}")

# fetch each bundle and search for relevant logic
keywords = [
    'recoverMyStuckMedia', 'provider_failed', 'provider_pending',
    'ingestion_stage', 'credits_refunded', 'stuck', 'recover',
    'still_processing', 'max_attempts', 'maxAttempts',
]

all_matches = {}
for js_path in js_urls:
    url = f'https://zorqai.com{js_path}'
    try:
        jr = s.get(url, timeout=15)
        if not jr.ok:
            continue
        code = jr.text
        matches = []
        for kw in keywords:
            if kw in code:
                # extract context
                idx = code.find(kw)
                while idx != -1:
                    ctx = code[max(0, idx-100):idx+200]
                    matches.append({'kw': kw, 'ctx': ctx})
                    idx = code.find(kw, idx+1)
        if matches:
            all_matches[js_path] = matches
            print(f"\n=== {js_path} ({len(matches)} hits) ===")
            for m in matches[:5]:
                print(f"  [{m['kw']}] ...{m['ctx']}...")
    except Exception as e:
        print(f"  error fetching {js_path}: {e}")
