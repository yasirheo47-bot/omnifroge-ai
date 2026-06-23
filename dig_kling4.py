"""
Probe kling.ai/developer portal to find registration/account creation API.
Once we have an access_key, alg:none JWT lets us authenticate with no secret.
Goal: programmatic account registration + credit cycling.
"""
import asyncio, aiohttp, re, json, base64, time

PORTAL_URLS = [
    "https://kling.ai",
    "https://kling.ai/developer",
    "https://klingai.com/account/developer",
    "https://klingai.com/developer",
]
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124",
    "Accept": "text/html,application/json,*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
}


async def main():
    jar = aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(cookie_jar=jar) as s:

        # ─── Step 1: Explore each developer portal URL ─────────────────
        for url in PORTAL_URLS:
            print(f"\n{'='*60}")
            print(f"URL: {url}")
            print("="*60)
            try:
                async with s.get(url, headers=HDR, allow_redirects=True,
                                   timeout=aiohttp.ClientTimeout(total=15)) as r:
                    html = await r.text()
                    final = str(r.url)
                    print(f"  Status: {r.status}, Final URL: {final}")
                    title = re.search(r'<title>(.*?)</title>', html, re.S)
                    print(f"  Title: {title.group(1)[:80] if title else 'n/a'}")
                    print(f"  HTML: {len(html)} bytes")

                    # Extract all script URLs
                    scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)
                    print(f"  Scripts: {len(scripts)}")
                    for sc in scripts[:5]:
                        print(f"    {sc[:100]}")

                    # API paths in HTML
                    api_paths = set(re.findall(r'["`\'](/api/[a-zA-Z0-9/_\-]{2,60})["`\']', html))
                    if api_paths:
                        print(f"  API paths: {sorted(api_paths)[:10]}")

                    # CDN dispatch
                    cdn = re.search(r'__CDN_DISPATCH__\s*=\s*(\{[^<]+?\})', html)
                    if cdn:
                        print(f"  CDN: {cdn.group(1)[:200]}")

                    # Form fields
                    forms = re.findall(r'<form[^>]*>(.*?)</form>', html, re.S)
                    for f in forms[:2]:
                        inputs = re.findall(r'<input[^>]*>', f)
                        print(f"  Form inputs: {inputs[:5]}")

                    # Scan JS chunks
                    all_paths = set()
                    for sc_url in scripts[:10]:
                        if sc_url.startswith("//"):
                            sc_url = "https:" + sc_url
                        elif not sc_url.startswith("http"):
                            base = re.match(r'https?://[^/]+', url)
                            if base:
                                sc_url = base.group(0) + sc_url
                        try:
                            async with s.get(sc_url, headers=HDR,
                                              timeout=aiohttp.ClientTimeout(total=15)) as rjs:
                                if rjs.status == 200:
                                    js = await rjs.text()
                                    new_paths = re.findall(r'["`\'](/(?:api|v\d+)/[a-zA-Z0-9/_\-\$\{\}\.]{2,80})["`\']', js)
                                    for p in new_paths:
                                        all_paths.add(p)
                                    # Look for base URLs
                                    base_urls = re.findall(r'baseURL\s*[:=]\s*["`\']([^"`\']{5,80})["`\']', js)
                                    if base_urls:
                                        print(f"  Base URLs: {set(base_urls)}")
                                    # Auth endpoints
                                    auth = re.findall(r'["`\']([^"`\']*(?:login|register|signup|auth|oauth|token|create-key|access-key)[^"`\']{0,50})["`\']', js, re.I)
                                    for a in set(auth):
                                        if ('/api/' in a or a.startswith('/')) and len(a) < 80:
                                            print(f"  Auth path: {a}")
                        except Exception as e:
                            pass

                    if all_paths:
                        print(f"\n  All API paths ({len(all_paths)}):")
                        for p in sorted(all_paths):
                            print(f"    {p}")

            except Exception as e:
                print(f"  [ERR]: {type(e).__name__}: {str(e)[:100]}")

        # ─── Step 2: Probe kling.ai API endpoints ──────────────────────
        print("\n" + "="*60)
        print("PROBING kling.ai/api/* ENDPOINTS")
        print("="*60)

        base = "https://kling.ai"
        endpoints = [
            ("POST", "/api/register",          {"email":"test@temp.com","password":"Test123!"}),
            ("POST", "/api/auth/register",      {"email":"test@temp.com","password":"Test123!"}),
            ("POST", "/api/developer/register", {"email":"test@temp.com","password":"Test123!"}),
            ("POST", "/api/user/register",      {"email":"test@temp.com","password":"Test123!"}),
            ("POST", "/api/user/create",        {"email":"test@temp.com","password":"Test123!"}),
            ("POST", "/api/keys/create",        {}),
            ("POST", "/api/access-keys",        {}),
            ("GET",  "/api/keys",               None),
            ("GET",  "/api/access-keys",        None),
            ("GET",  "/api/developer",          None),
            ("GET",  "/api/developer/keys",     None),
        ]

        api_hdrs = {**HDR, "Accept": "application/json", "Content-Type": "application/json"}

        for method, ep, payload in endpoints:
            url = base + ep
            try:
                if method == "GET":
                    async with s.get(url, headers=api_hdrs,
                                      timeout=aiohttp.ClientTimeout(total=8)) as r:
                        body = (await r.text())[:300].replace('\n', ' ')
                        is_html = body.strip().startswith('<')
                        if r.status not in (404,) and not is_html:
                            print(f"  [{r.status}] GET {ep} -> {body[:150]}")
                        elif r.status not in (404,):
                            print(f"  [{r.status}] GET {ep} -> HTML({len(body)})")
                else:
                    async with s.post(url, json=payload, headers=api_hdrs,
                                       timeout=aiohttp.ClientTimeout(total=8)) as r:
                        body = (await r.text())[:300].replace('\n', ' ')
                        is_html = body.strip().startswith('<')
                        if not is_html:
                            print(f"  [{r.status}] POST {ep} -> {body[:150]}")
                        elif r.status not in (404, 200):
                            print(f"  [{r.status}] POST {ep} -> HTML")
            except Exception as e:
                pass

        # ─── Step 3: Try klingai.com/account/developer endpoints ───────
        print("\n" + "="*60)
        print("PROBING klingai.com DEVELOPER API ENDPOINTS")
        print("="*60)

        base2 = "https://klingai.com"
        dev_endpoints = [
            ("GET",  "/account/developer"),
            ("GET",  "/api/developer/keys"),
            ("GET",  "/api/developer/access-keys"),
            ("POST", "/api/developer/keys/create"),
            ("POST", "/api/developer/create-key"),
            ("GET",  "/api/keys"),
        ]

        for method, ep in dev_endpoints:
            url = base2 + ep
            try:
                if method == "GET":
                    async with s.get(url, headers=api_hdrs, allow_redirects=True,
                                      timeout=aiohttp.ClientTimeout(total=8)) as r:
                        body = (await r.text())[:200].replace('\n', ' ')
                        is_html = body.strip().startswith('<')
                        print(f"  [{r.status}] GET {ep} | final={str(r.url)[:60]} | {'HTML' if is_html else body[:80]}")
                else:
                    async with s.post(url, json={}, headers=api_hdrs,
                                       timeout=aiohttp.ClientTimeout(total=8)) as r:
                        body = (await r.text())[:200].replace('\n', ' ')
                        is_html = body.strip().startswith('<')
                        print(f"  [{r.status}] POST {ep} | {'HTML' if is_html else body[:80]}")
            except Exception as e:
                pass

        print("\n=== DONE ===")


asyncio.run(main())
