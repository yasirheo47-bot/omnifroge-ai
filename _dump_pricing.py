import urllib.request, re, json

url = 'https://www.viewmax.io/_next/static/chunks/fe990f7183fe36d4.js'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as r:
    text = r.read().decode('utf-8')

# Dump the full pricing module area - from module 698885 start
# Find where p= is defined (base Sora 2 price)
# Start from where module 698885 content begins
mod_start = text.find('698885,855099')
mod_end = text.find('698885)', mod_start + 100)
# actually module 698885 seems large. Let's just dump from mod start to ~5000 chars in
segment = text[mod_start:mod_start+8000]
print(segment[:8000])
