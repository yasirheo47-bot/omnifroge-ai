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
print("  JS BUNDLE DEEP SCAN — FETCH CALLS & API ROUTES")
print("=" * 70)
print()

# 1. Fetch main page
print("[1] Fetching main page...")
r = requests.get(BASE, headers=hdrs, timeout=15)
script_urls = re.findall(r'<script src="(/_next/static/[^"]+)"', r.text)
print(f"[+] Found {len(script_urls)} chunks")

# 2. Download all chunks into one big blob
print("[2] Downloading all chunks...")
all_js = ""
for i, script_path in enumerate(script_urls):
    full_url = urljoin(BASE, script_path)
    try:
        chunk_resp = requests.get(full_url, timeout=10)
        if chunk_resp.status_code == 200:
            all_js += chunk_resp.text + "\n"
        print(f"[{i+1}/{len(script_urls)}] Downloaded {script_path.split('/')[-1][:30]}")
    except:
        continue

print(f"[+] Total JS size: {len(all_js)} bytes")
print()

# 3. Extract all fetch() calls with /api/ in them
print("[3] Extracting fetch() calls with /api/ paths...")
fetch_pattern = r'fetch\s*\(\s*["\']([^"\']+)["\']'
fetch_calls = re.findall(fetch_pattern, all_js)
api_fetches = [f for f in fetch_calls if "/api/" in f]

print(f"[+] Found {len(api_fetches)} unique /api/ fetch calls:")
for f in sorted(set(api_fetches)):
    print(f"  {f}")

print()

# 4. Search for specific subscription-related strings
print("[4] Searching for subscription-related strings...")
sub_patterns = [
    r'"/api/account/subscription[^"]*"',
    r'"/api/subscription[^"]*"',
    r'"paymentMethodId"',
    r'"priceId"',
    r'"customerId"',
    r'"subscriptionId"',
    r'"usePurchased"',
    r'"creditsSource"',
]

for pattern in sub_patterns:
    matches = re.findall(pattern, all_js)
    if matches:
        print(f"\n[{pattern}] — {len(matches)} hits:")
        for m in sorted(set(matches))[:5]:
            print(f"  {m}")

print()

# 5. Extract method calls on /api/account
print("[5] Extracting method calls on /api/account...")
method_pattern = r'(method\s*:\s*["\'](?:POST|PUT|PATCH|DELETE)["\'][\s\S]{0,200}?/api/account[^"\']*)'
method_calls = re.findall(method_pattern, all_js)
print(f"[+] Found {len(method_calls)} method calls:")
for m in method_calls[:10]:
    snippet = m.replace("\n", " ")[:150]
    print(f"  ...{snippet}...")

print()
print("[*] Done. Check output for actual API routes.")
