"""Find how to create the public.users row for new accounts."""
import json, sys, requests, base64
sys.path.insert(0, '.')

SUPABASE_URL = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"
ANON_KEY = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"

accounts = json.load(open('zorq_farm_accounts.json'))
acc = accounts[0]
jwt = acc['access_token']
payload_b64 = jwt.split(".")[1]
payload_b64 += "=" * (-len(payload_b64) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_b64))
uid   = payload['sub']
email = payload.get('email', '')

h = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {jwt}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://zorqai.com",
    "Referer": "https://zorqai.com/",
}

print("=== public.public_profiles ===")
r = requests.get(f"{SUPABASE_URL}/rest/v1/public_profiles",
                 params={"select": "*", "id": f"eq.{uid}"},
                 headers={**h, "Accept-Profile": "public"})
print(f"status={r.status_code}  body={r.text[:300]}")

print("\n=== try INSERT into public.users ===")
r2 = requests.post(f"{SUPABASE_URL}/rest/v1/users",
                   headers={**h, "Content-Profile": "public", "Prefer": "return=representation"},
                   json={"id": uid, "email": email, "credits": 100, "active_subscription": "free"})
print(f"status={r2.status_code}  body={r2.text[:400]}")

print("\n=== edge functions probe ===")
for fn in ["getUserProfile", "getOrCreateUser", "initUser", "createProfile",
           "onAuthStateChange", "syncUser", "getUserData", "getUser"]:
    r3 = requests.post(f"{SUPABASE_URL}/functions/v1/{fn}", headers=h, json={}, timeout=8)
    print(f"  {fn:<25} status={r3.status_code}  body={r3.text[:100]}")

print("\n=== zorqai /api/auth check ===")
r4 = requests.get("https://zorqai.com/api/auth/session",
                  headers={"Cookie": f"supabase-auth-token={jwt}"}, timeout=10)
print(f"status={r4.status_code}  body={r4.text[:200]}")
