#!/usr/bin/env python3
"""
viewmax_scrape.py
─────────────────
For each account in "viewmax axx" (password = email):
  1. Login via API → get session cookie
  2. Save __Secure-better-auth.session_token to "viewmax_tokens.txt"

Run: python viewmax_farm.py
Requires: pip install aiohttp
"""

import asyncio
import os
import random

import aiohttp

# ── paths ─────────────────────────────────────────────────────────────────────
_DIR          = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(_DIR, "viewmax axx")
OUTPUT_FILE   = os.path.join(_DIR, "viewmax_tokens.txt")
BASE          = "https://www.viewmax.io"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent":   UA,
    "Accept":       "application/json, */*",
    "Content-Type": "application/json",
    "Origin":       BASE,
    "Referer":      f"{BASE}/",
}


def load_accounts():
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and "@" in l]


def log(email, msg):
    tag = email.split("@")[0][:22]
    print(f"  [{tag}] {msg}")


def save_token(email, token):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"# {email}\n__Secure-better-auth.session_token={token}\n\n")
    log(email, f"💾 saved: {token[:40]}…")


async def process_account(email: str, results: list):
    jar = aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(cookie_jar=jar) as session:
        # Retry loop for 429 rate-limit
        for attempt in range(4):
            try:
                async with session.post(
                    f"{BASE}/api/auth/sign-in/email",
                    json={"email": email, "password": email, "rememberMe": True},
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as r:
                    if r.status == 429:
                        wait = 45 + random.uniform(0, 20) + attempt * 30
                        log(email, f"⏳ 429 rate-limited — waiting {wait:.0f}s (attempt {attempt+1}/4)")
                        await asyncio.sleep(wait)
                        continue
                    data = await r.json(content_type=None)
                    if not (data.get("token") or data.get("user")):
                        log(email, f"❌ Login failed: {str(data)[:120]}")
                        results.append({"email": email, "ok": False})
                        return
                    log(email, "✅ Login OK")
                    break
            except Exception as e:
                log(email, f"❌ Error: {e}")
                results.append({"email": email, "ok": False})
                return
        else:
            log(email, "❌ Gave up after 4 attempts (rate limited)")
            results.append({"email": email, "ok": False})
            return

        # Human-like pause after login
        await asyncio.sleep(random.uniform(1.5, 3.0))

        # Extract token from cookie jar
        token = None
        for morsel in jar:
            if "session_token" in morsel.key:
                token = morsel.value
                break

        # Fallback: call /api/auth/get-session and grab Set-Cookie header
        if not token:
            try:
                async with session.get(
                    f"{BASE}/api/auth/get-session",
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as r2:
                    for morsel in jar:
                        if "session_token" in morsel.key:
                            token = morsel.value
                            break
            except Exception:
                pass

        if token:
            save_token(email, token)
            results.append({"email": email, "ok": True})
        else:
            log(email, "⚠️  No session_token found in cookies")
            results.append({"email": email, "ok": False})

    await asyncio.sleep(random.uniform(10, 18))


def already_saved() -> set:
    """Return set of emails already present in output file."""
    saved = set()
    if not os.path.exists(OUTPUT_FILE):
        return saved
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                saved.add(line[2:].strip())
    return saved


async def main():
    accounts = load_accounts()
    done = already_saved()
    pending = [e for e in accounts if e not in done]

    print(f"\n🚀 Scraping tokens for {len(pending)} accounts ({len(done)} already saved)")
    print(f"   output → {OUTPUT_FILE}\n")

    if not pending:
        print("Nothing to do.")
        return

    results = []
    for idx, email in enumerate(pending, 1):
        print(f"── {idx}/{len(pending)}: {email}")
        try:
            await process_account(email, results)
        except Exception as e:
            print(f"  [FATAL] {e}")
            results.append({"email": email, "ok": False})

    ok   = sum(1 for r in results if r["ok"])
    fail = len(results) - ok
    print(f"\n✅ Done — {ok} tokens saved, {fail} failed")
    print(f"   file: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
