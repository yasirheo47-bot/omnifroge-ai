import requests
import json

BASE = "https://www.viewmax.io"
TOKEN = "d9QuNKM5ffxCJGIchmsMR7dcePrKv1ot.B%2B0dRzWctIaEopGDEVaAb%2BRedimLfHQ%2FJbPsj%2FAu%2F5I%3D"
TASK_ID = "cmooit1ht0003kr06tlfpikpq"

hdrs = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"__Secure-better-auth.session_token={TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("  DEBUG: STATUS ENDPOINT RAW RESPONSE")
print("=" * 70)
print()

r = requests.get(f"{BASE}/api/video-generation/status?ids={TASK_ID}", headers=hdrs, timeout=10)
print(f"Status code: {r.status_code}")
print(f"Headers: {dict(r.headers)}")
print()
print(f"Raw text response:")
print(r.text)
print()

try:
    data = r.json()
    print(f"Parsed JSON:")
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"JSON parse error: {e}")

print()
print("[*] Done.")
