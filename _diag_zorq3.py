"""Inspect users row before/after PATCH to find what's resetting credits."""
import json, sys, requests, base64
sys.path.insert(0, '.')

SUPABASE_URL = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"
ANON_KEY = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"

accounts = json.load(open('zorq_farm_accounts.json'))
acc = accounts[1]  # account #2 — has a users row now
jwt = acc['access_token']
payload_b64 = jwt.split(".")[1]
payload_b64 += "=" * (-len(payload_b64) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_b64))
uid = payload['sub']

h = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {jwt}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def get_row():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/users",
                     params={"select": "*", "id": f"eq.{uid}"},
                     headers={**h, "Accept-Profile": "public"})
    return r.json()

print("Before patch:")
print(json.dumps(get_row(), indent=2))

# patch with various combinations
print("\nPATCH credits=99999 + active_subscription=pro:")
r = requests.patch(f"{SUPABASE_URL}/rest/v1/users",
                   params={"id": f"eq.{uid}"},
                   headers={**h, "Content-Profile": "public", "Prefer": "return=representation"},
                   json={"credits": 99999, "active_subscription": "pro"})
print(f"status={r.status_code}  body={r.text[:400]}")

print("\nAfter patch:")
print(json.dumps(get_row(), indent=2))
