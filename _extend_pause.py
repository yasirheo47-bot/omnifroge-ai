import requests
import json

BASE = "https://www.viewmax.io"
TOKEN = "d9QuNKM5ffxCJGIchmsMR7dcePrKv1ot.B%2B0dRzWctIaEopGDEVaAb%2BRedimLfHQ%2FJbPsj%2FAu%2F5I%3D"

hdrs = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"__Secure-better-auth.session_token={TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("  EXTENDING PAUSE TO 3 MONTHS")
print("=" * 70)
print()

# 1. Check current pause state
print("[1] Current account state:")
r = requests.get(f"{BASE}/api/me", headers=hdrs, timeout=10)
data = r.json()
print(f"Subscription status: {data.get('subscription', {}).get('status')}")
print(f"Pause collection: {data.get('subscription', {}).get('pause_collection')}")
print(f"Purchased credits: {data.get('purchasedCredits')}")
print()

# 2. Extend pause to 3 months
print("[2] Calling pause endpoint with months=3...")
r2 = requests.post(
    f"{BASE}/api/account/subscription/pause",
    headers=hdrs,
    json={"months": 3},
    timeout=10
)

print(f"Status: {r2.status_code}")
try:
    resp = r2.json()
    print(f"Response: {json.dumps(resp, indent=2)}")
    
    if resp.get("success"):
        print()
        print("=" * 70)
        print("✅ PAUSE EXTENDED TO 3 MONTHS")
        print("=" * 70)
        print(f"Resumes at: {resp.get('resumesAt')}")
except Exception as e:
    print(f"Response: {r2.text}")
    print(f"Error: {e}")

print()

# 3. Verify new state
print("[3] Verifying new pause state:")
r3 = requests.get(f"{BASE}/api/me", headers=hdrs, timeout=10)
data3 = r3.json()
sub = data3.get('subscription', {})
print(f"Subscription status: {sub.get('status')}")
print(f"Pause collection: {sub.get('pause_collection')}")
if sub.get('pause_collection'):
    print(f"Pause behavior: {sub['pause_collection'].get('behavior')}")
    print(f"Resumes at: {sub['pause_collection'].get('resumes_at')}")

print()
print("[*] Done. Bypass now active until the new resume date.")
