"""Quick diagnostic for why credits = 0"""
import json, sys, requests, base64
sys.path.insert(0, '.')

SUPABASE_URL = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"
ANON_KEY = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"

accounts = json.load(open('zorq_farm_accounts.json'))
acc = accounts[0]  # check first account

jwt = acc['access_token']
payload_b64 = jwt.split(".")[1]
payload_b64 += "=" * (-len(payload_b64) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_b64))
uid  = payload['sub']
email = payload.get('email', '')

print(f"uid={uid}")
print(f"email={email}")

h = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {jwt}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# 1. check public.users by auth uid
r = requests.get(f"{SUPABASE_URL}/rest/v1/users",
                 params={"select": "*", "auth_id": f"eq.{uid}"},
                 headers={**h, "Accept-Profile": "public"})
print(f"\n[users by auth_id] status={r.status_code}  body={r.text[:300]}")

# 2. check public.users by email
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/users",
                  params={"select": "*", "email": f"eq.{email}"},
                  headers={**h, "Accept-Profile": "public"})
print(f"\n[users by email] status={r2.status_code}  body={r2.text[:300]}")

# 3. check public.users by id = uid directly
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/users",
                  params={"select": "*", "id": f"eq.{uid}"},
                  headers={**h, "Accept-Profile": "public"})
print(f"\n[users by id=uid] status={r3.status_code}  body={r3.text[:300]}")

# 4. list all columns — get any row
r4 = requests.get(f"{SUPABASE_URL}/rest/v1/users",
                  params={"select": "*", "limit": 1},
                  headers={**h, "Accept-Profile": "public"})
print(f"\n[users sample row] status={r4.status_code}  body={r4.text[:400]}")

# 5. check profiles table (some Supabase apps use this)
r5 = requests.get(f"{SUPABASE_URL}/rest/v1/profiles",
                  params={"select": "*", "id": f"eq.{uid}"},
                  headers={**h, "Accept-Profile": "public"})
print(f"\n[profiles by id] status={r5.status_code}  body={r5.text[:300]}")

# 6. check generated_videos — did our fake rows land?
r6 = requests.get(f"{SUPABASE_URL}/rest/v1/generated_videos",
                  params={"select": "id,status,ingestion_stage,credits_used", "limit": 5},
                  headers={**h, "Accept-Profile": "public"})
print(f"\n[generated_videos] status={r6.status_code}  body={r6.text[:400]}")
