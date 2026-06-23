"""
check_viewmax_tokens.py
========================
Pings /api/me with every token in scenx_bot._SESSION_POOL
and prints which ones are alive vs dead.
Run: python check_viewmax_tokens.py
"""

import sys
import os
import urllib.parse
import concurrent.futures
import requests

# ── pull the pool directly from scenx_bot without running the bot ────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# only import the pool list, not the whole bot
from scenx_bot import _SESSION_POOL   # type: ignore

BASE = "https://www.viewmax.io"
UA   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"


def _tok_value(cookie_str: str) -> str:
    """Extract just the token value from the full cookie string."""
    # format: "__Secure-better-auth.session_token=VALUE"
    if "=" in cookie_str:
        return cookie_str.split("=", 1)[1]
    return cookie_str


def check_one(idx: int, cookie_str: str) -> dict:
    tok_val = _tok_value(cookie_str)
    try:
        r = requests.get(
            f"{BASE}/api/me",
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "Cookie": f"__Secure-better-auth.session_token={tok_val}",
            },
            timeout=10,
        )
        if r.status_code == 200:
            data  = r.json()
            user  = data.get("user") or {}
            email = user.get("email", "?")
            # credits remaining
            credits = -1
            for svc in (data.get("subscription") or {}).get("services", []):
                if svc.get("type") == "AI_CREDITS":
                    try:
                        credits = int(svc["max"]) - int(svc["used"])
                    except Exception:
                        pass
                    break
            return {"idx": idx, "status": "ALIVE", "email": email, "credits": credits, "cookie": cookie_str}
        elif r.status_code == 401:
            return {"idx": idx, "status": "DEAD (401)", "email": "—", "credits": -1, "cookie": cookie_str}
        else:
            return {"idx": idx, "status": f"ERR {r.status_code}", "email": "—", "credits": -1, "cookie": cookie_str}
    except Exception as e:
        return {"idx": idx, "status": f"TIMEOUT/ERR", "email": "—", "credits": -1, "cookie": cookie_str, "err": str(e)}


def main():
    print(f"\nChecking {len(_SESSION_POOL)} tokens...\n")
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(check_one, i, tok): i for i, tok in enumerate(_SESSION_POOL)}
        for f in concurrent.futures.as_completed(futs):
            results.append(f.result())

    results.sort(key=lambda x: x["idx"])

    alive = [r for r in results if r["status"] == "ALIVE"]
    dead  = [r for r in results if r["status"] != "ALIVE"]

    print("=" * 70)
    print(f"  ALIVE: {len(alive)}   DEAD/ERR: {len(dead)}")
    print("=" * 70)

    print("\n── ALIVE ─────────────────────────────────────────────────────────")
    for r in alive:
        cr = f"{r['credits']:,}" if r["credits"] >= 0 else "?"
        print(f"  [{r['idx']:02d}] {r['email']:<35}  credits={cr}")

    if dead:
        print("\n── DEAD / EXPIRED ────────────────────────────────────────────────")
        for r in dead:
            print(f"  [{r['idx']:02d}] {r['status']}")
            print(f"       cookie: {r['cookie'][:80]}...")

    # write dead indices to a file for easy reference
    dead_indices = [r["idx"] for r in dead]
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dead_tokens.txt")
    with open(out_path, "w") as f:
        f.write(f"Dead token indices ({len(dead_indices)} total):\n")
        for r in dead:
            f.write(f"[{r['idx']:02d}] {r['status']}\n")
            f.write(f"  {r['cookie']}\n\n")
    print(f"\nDead tokens written to: dead_tokens.txt")


if __name__ == "__main__":
    main()
