"""
Find s0 axios instance + try POST to app.klingai.com/api/* + email login flow
"""
import asyncio, aiohttp, re, json

APP = "https://app.klingai.com"
JS_URL = "https://s15-kling.klingai.com/kos/s101/nlav112918/kling-web/assets/js/index-DmZd8wtW.js"
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124",
    "Accept": "application/json, */*",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/json",
    "Referer": APP + "/",
    "Origin": APP,
}

async def main():
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as s:

        print("Loading JS bundle (2MB)...")
        async with s.get(JS_URL, headers=HDR, timeout=aiohttp.ClientTimeout(total=60)) as r:
            js = await r.text()
        print(f"Loaded: {len(js)} chars")

        # ── Find s0 axios instance definition ──────────────────────────
        print("\n=== s0 AXIOS INSTANCE ===")
        # Look for where s0 is created
        s0_defs = re.findall(r'.{0,30}s0\s*[=,]\s*.{0,100}(?:axios|create|instance).{0,100}', js)
        for d in list(set(s0_defs))[:10]:
            print(f"  {d.strip()[:150]}")

        # Look for axios.create patterns
        print("\n=== AXIOS.CREATE CALLS ===")
        create_calls = re.finditer(r'\.create\s*\(\s*\{([^}]{0,300})\}', js)
        for m in create_calls:
            block = m.group(1)
            if 'URL' in block.upper() or 'url' in block.lower() or 'base' in block.lower():
                print(f"  create({{ {block.strip()[:200]} }})")

        # ── Find email login endpoint ────────────────────────────────────
        print("\n=== EMAIL LOGIN CONTEXT ===")
        email_login = re.findall(r'.{0,80}email.{0,40}(?:login|sign|auth|code|token|verif).{0,80}', js, re.I)
        for e in list(set(email_login))[:15]:
            if '/api/' in e or 'post' in e.lower() or 'login' in e.lower():
                print(f"  {e.strip()[:150]}")

        # ── Find all /api/ POST calls ────────────────────────────────────
        print("\n=== ALL POST /api CALLS ===")
        posts = re.findall(r's0\.post\s*\(["`\']([^"`\']+)["`\']', js)
        for p in sorted(set(posts)):
            print(f"  POST {p}")

        # Also get calls
        print("\n=== ALL GET /api CALLS ===")
        gets = re.findall(r's0\.get\s*\(["`\']([^"`\']+)["`\']', js)
        for p in sorted(set(gets)):
            print(f"  GET {p}")

        # ── Find any HTTP client base URLs ───────────────────────────────
        print("\n=== ALL HTTP CLIENT BASE URLS ===")
        # Find all variables assigned to axios instances
        all_instances = re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*\w+\.create\s*\(\s*\{([^}]{0,300})\}', js)
        for name, block in all_instances:
            print(f"  {name}: {block.strip()[:150]}")

        # ── Find auth cookie or token key ────────────────────────────────
        print("\n=== COOKIE/TOKEN KEYS ===")
        # Look for ktoken, session, kling_token etc.
        token_keys = re.findall(r'["\']([a-zA-Z_\-\.]{3,40})["\'].{0,20}(?:cookie|token|session|auth)', js, re.I)
        print(f"  Token-related: {set(list(token_keys)[:20])}")

        # ── Try POST to app.klingai.com endpoints ────────────────────────
        print("\n=== PROBE POST /api on app.klingai.com ===")
        # First: try all POST /api/* found from JS
        all_post_eps = sorted(set(posts))
        # Add common auth endpoints
        auth_eps = [
            "/api/user/login",
            "/api/user/register",
            "/api/user/email/login",
            "/api/user/email/register",
            "/api/user/send-code",
            "/api/auth/email",
            "/api/auth/login",
            "/api/login",
        ]
        # Combine all non-dynamic paths
        test_eps = [ep for ep in all_post_eps + auth_eps if "${" not in ep]

        login_payload = {"email": "test@example.com", "password": "test123"}
        code_payload = {"email": "test@example.com"}

        for ep in test_eps:
            try:
                async with s.post(APP + ep, json=login_payload, headers=HDR,
                                   timeout=aiohttp.ClientTimeout(total=8)) as r:
                    body = (await r.text())[:200].replace('\n', ' ')
                    # Check if it's HTML (SPA catch-all) or real API response
                    is_html = body.strip().startswith('<!') or body.strip().startswith('<html')
                    if not is_html:
                        print(f"  *** [{r.status}] POST {ep} -> {body[:150]}")
                    # Also interesting: non-200 non-HTML
                    elif r.status not in (200,):
                        print(f"  [{r.status}] POST {ep} -> {body[:80]}")
            except Exception as e:
                pass

        print("\n=== DONE ===")

asyncio.run(main())
