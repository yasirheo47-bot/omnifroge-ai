import requests
import re
from urllib.parse import urljoin

BASE = "https://www.viewmax.io"
TOKEN = "d9QuNKM5ffxCJGIchmsMR7dcePrKv1ot.B%2B0dRzWctIaEopGDEVaAb%2BRedimLfHQ%2FJbPsj%2FAu%2F5I%3D"

hdrs = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"__Secure-better-auth.session_token={TOKEN}"
}

print("=" * 70)
print("  JS BUNDLE EXTRACTION — SUBSCRIPTION BYPASS HUNTING")
print("=" * 70)
print()

# 1. Fetch main page to get script tags
print("[1] Fetching main page for script tags...")
r = requests.get(BASE, headers=hdrs, timeout=15)
if r.status_code != 200:
    print(f"[!] Main page returned {r.status_code}")
    exit(1)

# Extract all <script src="/_next/static/chunks/..."> URLs
script_pattern = r'<script src="(/_next/static/[^"]+)"'
script_urls = re.findall(script_pattern, r.text)
print(f"[+] Found {len(script_urls)} Next.js script chunks")

# 2. Download each chunk and search for API routes + field names
api_keywords = [
    "/api/account",
    "/api/subscription",
    "upgrade",
    "reactivate",
    "resume",
    "cancel",
    "paymentMethodId",
    "coupon",
    "trial",
    "priceId",
    "subscriptionId",
    "customerId",
    "usePurchased",
    "creditsSource",
]

hits = []
for i, script_path in enumerate(script_urls):
    full_url = urljoin(BASE, script_path)
    try:
        chunk_resp = requests.get(full_url, timeout=10)
        if chunk_resp.status_code != 200:
            continue
        
        chunk_js = chunk_resp.text
        
        # Search for any API keyword
        for kw in api_keywords:
            if kw in chunk_js:
                # Extract surrounding context (50 chars before/after)
                for match in re.finditer(re.escape(kw), chunk_js):
                    start = max(0, match.start() - 100)
                    end = min(len(chunk_js), match.end() + 100)
                    snippet = chunk_js[start:end].replace("\n", " ")
                    hits.append({
                        "chunk": script_path.split("/")[-1],
                        "keyword": kw,
                        "snippet": snippet
                    })
        
        print(f"[{i+1}/{len(script_urls)}] Scanned {script_path.split('/')[-1]}")
    except:
        continue

print()
print("=" * 70)
print(f"  RESULTS: {len(hits)} hits")
print("=" * 70)
print()

# Group by keyword
from collections import defaultdict
by_kw = defaultdict(list)
for hit in hits:
    by_kw[hit["keyword"]].append(hit)

for kw in sorted(by_kw.keys()):
    print(f"\n[{kw}] — {len(by_kw[kw])} hits")
    for hit in by_kw[kw][:3]:  # Show first 3 per keyword
        print(f"  Chunk: {hit['chunk']}")
        print(f"  ...{hit['snippet']}...")
        print()

print("\n[*] Done. Check output for actual field names and API calls.")
