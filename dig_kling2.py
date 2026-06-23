"""
Extract actual API base URLs from app.klingai.com JS bundle:
- Look for axios baseURL, fetch base URLs, __CDN_DISPATCH__
- Find auth cookie name, token storage
- Find the real backend API host
"""
import asyncio, aiohttp, re, json

APP = "https://app.klingai.com"
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
}

async def main():
    async with aiohttp.ClientSession() as s:

        # Get main HTML to find CDN_DISPATCH
        async with s.get(APP + "/", headers={**HDR, "Accept": "text/html,*/*"},
                          timeout=aiohttp.ClientTimeout(total=15)) as r:
            html = await r.text()

        # Extract CDN_DISPATCH
        cdn_match = re.search(r'window\.__CDN_DISPATCH__\s*=\s*(\{[^<]+\})', html)
        if cdn_match:
            print("CDN_DISPATCH:")
            try:
                cdn = json.loads(cdn_match.group(1))
                for k, v in cdn.items():
                    print(f"  {k}: {v}")
            except:
                print(f"  raw: {cdn_match.group(1)[:300]}")

        # Load the 2MB main bundle
        js_url = "https://s15-kling.klingai.com/kos/s101/nlav112918/kling-web/assets/js/index-DmZd8wtW.js"
        print(f"\nLoading JS bundle...")
        async with s.get(js_url, headers=HDR, timeout=aiohttp.ClientTimeout(total=60)) as r:
            js = await r.text()
        print(f"Bundle size: {len(js)} chars")

        # ── Find base URLs ───────────────────────────────────────────────
        print("\n=== BASE URLS / API HOSTS ===")
        base_urls = re.findall(r'baseURL\s*[:=]\s*["`\']([^"`\']{10,80})["`\']', js)
        print(f"baseURL entries: {set(base_urls)}")

        # https:// URLs
        https_urls = re.findall(r'["`\']https://([a-zA-Z0-9\-\.]+\.klingai\.com[^"`\']{0,60})["`\']', js)
        unique_hosts = set()
        for u in https_urls:
            host = u.split('/')[0]
            unique_hosts.add(host)
        print(f"\nklingai.com hosts in JS: {unique_hosts}")

        # All external https hosts
        all_hosts = set(re.findall(r'https://([a-zA-Z0-9\-\.]{4,50})\.[a-z]{2,6}/', js))
        print(f"\nAll external HTTPS hosts (>3 occurrences):")
        host_count = {}
        for h in re.findall(r'https://([a-zA-Z0-9\-\.]{4,80})/api', js):
            host_count[h] = host_count.get(h, 0) + 1
        for h, c in sorted(host_count.items(), key=lambda x: -x[1]):
            if c >= 2:
                print(f"  {h}: {c} hits")

        # ── Find auth mechanism ─────────────────────────────────────────
        print("\n=== AUTH MECHANISM ===")

        # Cookie names
        cookie_refs = re.findall(r'(?:cookie|Cookie)[^;]{0,30}["`\']([a-zA-Z_\-\.]{3,50})["`\']', js)
        print(f"Cookie names: {set(cookie_refs)}")

        # Token/session header names
        header_refs = re.findall(r'["\']([Xx]-[a-zA-Z\-]{3,40})["\']', js)
        print(f"Custom headers: {set(header_refs)}")

        # localStorage keys
        storage_refs = re.findall(r'localStorage\.(?:get|set)Item\(["\']([^"\']{3,50})["\']', js)
        print(f"localStorage keys: {set(storage_refs)}")

        # ── Find /api/* paths with full context ─────────────────────────
        print("\n=== API ENDPOINT CONTEXTS (10 each) ===")

        for pattern, label in [
            (r'.{0,50}/api/user/[a-zA-Z/]{3,50}.{0,50}', 'user'),
            (r'.{0,50}/api/task[a-zA-Z/]{3,50}.{0,50}', 'task'),
            (r'.{0,50}/api/video[a-zA-Z/]{3,50}.{0,50}', 'video'),
            (r'.{0,50}login[^a-zA-Z].{0,80}', 'login'),
            (r'.{0,50}register[^a-zA-Z].{0,80}', 'register'),
            (r'.{0,50}signin[^a-zA-Z].{0,80}', 'signin'),
            (r'.{0,50}email.{0,10}code.{0,50}', 'email-code'),
        ]:
            matches = re.findall(pattern, js)
            # filter to interesting ones
            interesting = [m for m in matches if 'klingai' in m.lower() or '/api/' in m]
            if interesting:
                print(f"\n{label} ({len(interesting)} matches):")
                for m in list(set(interesting))[:8]:
                    print(f"  {m.strip()[:120]}")

        # ── Find klingai full API URLs ───────────────────────────────────
        print("\n=== FULL KLING API URLS ===")
        full_urls = re.findall(r'["`\']https?://[a-zA-Z0-9\-\.]*klingai[a-zA-Z0-9\-\.]*[^"`\']{0,80}["`\']', js)
        for u in sorted(set(full_urls)):
            print(f"  {u}")

        # ── Find auth token handling ─────────────────────────────────────
        print("\n=== TOKEN HANDLING ===")
        token_patterns = [
            r'Authorization["\']?\s*[:]\s*["`\'][^"`\']{0,80}["`\']',
            r'Bearer[^"\']{0,60}',
            r'access_token[^;]{0,60}',
            r'id_token[^;]{0,60}',
            r'ktoken[^;]{0,60}',
        ]
        for pat in token_patterns:
            matches = re.findall(pat, js)
            if matches:
                print(f"\n{pat[:30]}:")
                for m in list(set(matches))[:5]:
                    print(f"  {m.strip()[:100]}")

        # ── Find the SSO/login URL ───────────────────────────────────────
        print("\n=== SSO / LOGIN FLOW ===")
        sso_refs = re.findall(r'["`\'][^"`\']*(?:sso|oauth|google|tiktok|kuaishou|kling_token|auth)[^"`\']{0,80}["`\']', js, re.I)
        for r_ in sorted(set(sso_refs))[:20]:
            if len(r_) > 5 and 'function' not in r_.lower():
                print(f"  {r_.strip()[:120]}")


asyncio.run(main())
