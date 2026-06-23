#!/usr/bin/env python3
"""
One-off scraper for push.tg accounts (fixed password: Hamza@12@@)
Appends to viewmax_tokens.txt alongside the regular accounts.
"""
import asyncio, os, random
import aiohttp

_DIR        = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(_DIR, "viewmax_tokens.txt")
BASE        = "https://www.viewmax.io"
PASSWORD    = "Hamza@12@@"

ACCOUNTS = [
    "ffd8b9a@push.tg",
    "w637761@push.tg",
    "d2927e6@push.tg",
    "dbf79a0@push.tg",
    "u70fb87@push.tg",
    "vaa219f@push.tg",
]

HEADERS = {
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":       "application/json, */*",
    "Content-Type": "application/json",
    "Origin":       BASE,
    "Referer":      f"{BASE}/",
}


def already_saved() -> set:
    saved = set()
    if not os.path.exists(OUTPUT_FILE):
        return saved
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                saved.add(line[2:].strip())
    return saved


def log(email, msg):
    tag = email.split("@")[0][:22]
    print(f"  [{tag}] {msg}")


def save_token(email, token):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"# {email}\n__Secure-better-auth.session_token={token}\n\n")
    log(email, f"💾 saved: {token[:40]}…")


async def process(email: str):
    jar = aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(cookie_jar=jar) as session:
        for attempt in range(4):
            try:
                async with session.post(
                    f"{BASE}/api/auth/sign-in/email",
                    json={"email": email, "password": PASSWORD, "rememberMe": True},
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as r:
                    if r.status == 429:
                        wait = 45 + random.uniform(0, 20) + attempt * 30
                        log(email, f"⏳ 429 — waiting {wait:.0f}s (attempt {attempt+1}/4)")
                        await asyncio.sleep(wait)
                        continue
                    data = await r.json(content_type=None)
                    if not (data.get("token") or data.get("user")):
                        log(email, f"❌ Login failed: {str(data)[:120]}")
                        return
                    log(email, "✅ Login OK")
                    break
            except Exception as e:
                log(email, f"❌ Error: {e}")
                return
        else:
            log(email, "❌ Gave up after 4 attempts")
            return

        await asyncio.sleep(random.uniform(1.5, 3.0))

        token = None
        for morsel in jar:
            if "session_token" in morsel.key:
                token = morsel.value
                break

        if not token:
            try:
                async with session.get(f"{BASE}/api/auth/get-session", headers=HEADERS,
                                       timeout=aiohttp.ClientTimeout(total=15)) as r2:
                    for morsel in jar:
                        if "session_token" in morsel.key:
                            token = morsel.value
                            break
            except Exception:
                pass

        if token:
            save_token(email, token)
        else:
            log(email, "⚠️  No session_token found")

    await asyncio.sleep(random.uniform(10, 18))


async def main():
    done = already_saved()
    pending = [e for e in ACCOUNTS if e not in done]

    print(f"\n🚀 push.tg accounts: {len(pending)} to do ({len(done)} already saved)")
    print(f"   password: {PASSWORD}")
    print(f"   output → {OUTPUT_FILE}\n")

    if not pending:
        print("Nothing to do.")
        return

    for idx, email in enumerate(pending, 1):
        print(f"── {idx}/{len(pending)}: {email}")
        await process(email)

    print("\n✅ Done")


if __name__ == "__main__":
    asyncio.run(main())
