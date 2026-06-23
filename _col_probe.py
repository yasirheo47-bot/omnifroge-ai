"""
Enumerate generated_images column names via PostgREST error messages.
Also try different credit-seeding vectors.
"""
import requests, json

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H = {'apikey': ANON, 'Content-Type': 'application/json',
     'Origin': 'https://zorqai.com', 'User-Agent': 'Mozilla/5.0'}
PAST = '2024-01-01T00:00:00Z'

pool = json.load(open('_pool_gmail.json'))
acc  = pool[0]
r = requests.post(f'{BASE}/auth/v1/token?grant_type=password',
    json={'email': acc['email'], 'password': acc['password']}, headers=H, timeout=10)
jwt = r.json()['access_token']
uid = r.json()['user']['id']
HA  = {**H, 'Authorization': f'Bearer {jwt}'}

def try_insert(table, body):
    r = requests.post(f'{BASE}/rest/v1/{table}', json=body,
        headers={**HA, 'Prefer': 'return=representation'}, timeout=8)
    return r.status_code, r.text[:200]

def try_select(table, params):
    r = requests.get(f'{BASE}/rest/v1/{table}', params=params, headers=HA, timeout=8)
    return r.status_code, r.text[:300]

# Enumerate generated_images columns — PostgREST error tells you which column is wrong
print("=== generated_images column enumeration ===")
for col in ['author_id', 'owner_id', 'created_by', 'account_id', 'profile_id',
            'user_uid', 'uid', 'created_by_id', 'user_ref']:
    sc, t = try_insert('generated_images', {col: uid})
    if 'Could not find' not in t:
        print(f"  [HIT!] {col}: {sc} {t}")
    else:
        print(f"  {col}: not found")

# Try SELECT with explicit column names to see what exists
print("\n=== generated_images SELECT columns ===")
for col in ['id', 'created_at', 'status', 'credits_used', 'cost', 'credits',
            'image_url', 'prompt', 'style', 'url', 'user_id', 'author_id']:
    sc, t = try_select('generated_images', {'select': col, 'limit': '0'})
    if sc == 400:
        print(f"  {col}: NOT FOUND ({t[:80]})")
    else:
        print(f"  {col}: EXISTS ({sc})")

# Try generated_videos column names
print("\n=== generated_videos SELECT columns ===")
for col in ['id', 'created_at', 'status', 'credits_used', 'cost', 'credits',
            'user_id', 'author_id', 'creator_id', 'prompt', 'url']:
    sc, t = try_select('generated_videos', {'select': col, 'limit': '0'})
    if sc == 400:
        print(f"  {col}: NOT FOUND")
    else:
        print(f"  {col}: EXISTS ({sc})")

# Try runAgent (might not check credits for some operations)
print("\n=== runAgent ===")
r2 = requests.post(f'{BASE}/functions/v1/runAgent',
    json={'action': 'status'}, headers=HA, timeout=10)
print(f"  {r2.status_code}: {r2.text[:200]}")

# Try requestRefund  
print("\n=== requestRefund ===")
r3 = requests.post(f'{BASE}/functions/v1/requestRefund',
    json={'reason': 'test'}, headers=HA, timeout=10)
print(f"  {r3.status_code}: {r3.text[:200]}")

# Try stripeCreateBillingPortalSession
print("\n=== stripeCreateBillingPortalSession ===")
r4 = requests.post(f'{BASE}/functions/v1/stripeCreateBillingPortalSession',
    json={}, headers=HA, timeout=10)
print(f"  {r4.status_code}: {r4.text[:200]}")

# Try whopCheckout with membership body (might grant membership-based credits)
print("\n=== whopCheckout ===")
for plan in ['starter', 'basic', 'free', 'trial']:
    rw = requests.post(f'{BASE}/functions/v1/whopCheckout',
        json={'plan': plan, 'membership_id': f'mem_test123'}, headers=HA, timeout=10)
    print(f"  plan={plan}: {rw.status_code} {rw.text[:100]}")
