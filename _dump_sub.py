"""
_dump_sub.py — dumps the raw /api/me subscription object for the first live pool token.
Run: python _dump_sub.py
"""
import json, requests

BASE = "https://www.viewmax.io"
UA   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

TOKEN = "__Secure-better-auth.session_token=cQtzaK61W7spAybV8EM0LANJVmWL9Ujd.VJtd%2FX0PM%2BM%2Fx9BqwFWNhI6cMelSMOrAmVd8tVYskMw%3D"

r = requests.get(
    f"{BASE}/api/me",
    headers={"Cookie": TOKEN, "User-Agent": UA, "Accept": "application/json"},
    timeout=12,
)
print(f"HTTP {r.status_code}")
if r.status_code == 200:
    d = r.json()
    sub = d.get("subscription") or {}
    print("\n=== subscription keys ===")
    print(json.dumps(sub, indent=2))
else:
    print(r.text[:500])
