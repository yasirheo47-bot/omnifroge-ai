"""
Try to fix farm accounts by patching is_verified + active_subscription,
then re-running the stuck-row exploit.
Also tests if the edge function works with different user states.
"""
import json, sys, requests, base64, uuid, time
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '.')

SUPABASE_URL = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"
ANON_KEY = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"

accounts = json.load(open('zorq_farm_accounts.json'))
acc = accounts[0]  # account #1
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

def get_row():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/users",
                     params={"select": "credits,is_verified,active_subscription,welcome_granted,has_received_welcome_credits",
                             "id": f"eq.{uid}"},
                     headers={**h, "Accept-Profile": "public"})
    return r.json()[0] if r.ok and r.json() else {}

def get_credits():
    row = get_row()
    return row.get('credits', 0)

now = datetime.now(timezone.utc)
past = now - timedelta(hours=3)

print("=== Current user row ===")
print(json.dumps(get_row(), indent=2))

# Step 1: patch profile flags
print("\n=== Patching is_verified=true, active_subscription=free, welcome_granted=true ===")
r = requests.patch(f"{SUPABASE_URL}/rest/v1/users",
                   params={"id": f"eq.{uid}"},
                   headers={**h, "Content-Profile": "public", "Prefer": "return=representation"},
                   json={
                       "is_verified": True,
                       "active_subscription": "free",
                       "welcome_granted": True,
                       "has_received_welcome_credits": True,
                   })
print(f"status={r.status_code}")
resp_data = r.json()
if isinstance(resp_data, list) and resp_data:
    row = resp_data[0]
    print(f"  is_verified={row.get('is_verified')}  active_subscription={row.get('active_subscription')}  credits={row.get('credits')}")

# Step 2: insert fresh stuck rows (new ones, status=processing)
print("\n=== Inserting 20 fresh stuck rows ===")
inserted_ids = []
for i in range(20):
    row = {
        "id": str(uuid.uuid4()),
        "prompt": f"gen {i}",
        "status": "processing",
        "user_email": email,
        "credits_used": 9999,
        "model": "Seedance 2.0",
        "duration": 15,
        "resolution": "1080p",
        "provider": "wavespeed",
        "task_id": uuid.uuid4().hex,
        "provider_job_id": uuid.uuid4().hex,
        "ingestion_stage": "provider_failed",
        "attempts": 99,
        "source_images": [],
        "tags": [],
        "next_check_at": past.isoformat(),
        "created_at": past.isoformat(),
        "updated_at": past.isoformat(),
    }
    r2 = requests.post(f"{SUPABASE_URL}/rest/v1/generated_videos",
                       headers={**h, "Content-Profile": "public", "Prefer": "return=minimal"},
                       json=row)
    if r2.status_code in (200, 201):
        inserted_ids.append(row["id"])

print(f"Inserted {len(inserted_ids)} rows")

# Step 3: call recoverMyStuckMedia
print("\n=== Calling recoverMyStuckMedia ===")
before = get_credits()
r3 = requests.post(f"{SUPABASE_URL}/functions/v1/recoverMyStuckMedia", headers=h, json={})
print(f"status={r3.status_code}  response={r3.text[:300]}")

# Step 4: wait a bit and check
print("\nWaiting 15s...")
time.sleep(15)
after = get_credits()
print(f"Credits: before={before}  after={after}  gained={after-before}")
print("\nFull row after:")
print(json.dumps(get_row(), indent=2))
