import requests, json, base64, time

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'

with open('_sub_account.json') as f:
    acc = json.load(f)

rl = requests.post(f'{BASE}/auth/v1/token', params={'grant_type':'password'},
    json={'email': acc['email'], 'password': acc['password']},
    headers={'apikey': ANON_KEY, 'Content-Type':'application/json'}, timeout=15)
d = rl.json()
token = d.get('access_token','')
if not token:
    print("LOGIN FAIL:", d)
    exit(1)

pl = token.split('.')[1]
pl += '=' * (-len(pl) % 4)
jwt_uid = json.loads(base64.urlsafe_b64decode(pl)).get('sub','')
print('JWT uid:', jwt_uid)

hdrs = {'Authorization': f'Bearer {token}', 'apikey': ANON_KEY,
        'Content-Type':'application/json', 'Accept-Profile':'public',
        'Content-Profile':'public', 'Prefer':'return=representation'}

r = requests.get(f'{BASE}/rest/v1/users',
    params={'select':'id,credits,welcome_granted,has_received_welcome_credits', 'email': f'eq.{acc["email"]}'},
    headers=hdrs, timeout=10)
row = r.json()[0] if r.ok and r.json() else {}
print('Row:', row)
print('Row id == JWT uid:', row.get('id') == jwt_uid)

# If id doesn't match, update it
if row and row.get('id') != jwt_uid:
    print("\nMISMATCH — deleting old row and creating with correct id...")
    # Delete the mismatched row
    rd = requests.delete(f'{BASE}/rest/v1/users',
        params={'email': f'eq.{acc["email"]}'},
        headers=hdrs, timeout=10)
    print(f"DELETE: {rd.status_code} {rd.text[:80]}")
    time.sleep(1)
    # Re-create with correct id
    body = {'id': jwt_uid, 'email': acc['email'], 'full_name': acc['email'],
            'is_verified': True, 'role': 'user', 'device_fingerprint': None,
            'welcome_granted': False, 'has_received_welcome_credits': False}
    rp = requests.post(f'{BASE}/rest/v1/users', params={'select':'*'}, headers=hdrs, json=body, timeout=15)
    print(f"POST: {rp.status_code} {rp.text[:200]}")
    time.sleep(1)

# Now try the welcome flip
print("\nFlipping welcome_granted false->true...")
r1 = requests.patch(f'{BASE}/rest/v1/users',
    params={'email': f'eq.{acc["email"]}'},
    headers=hdrs,
    json={'welcome_granted': False, 'has_received_welcome_credits': False}, timeout=10)
print(f"reset: {r1.status_code} {r1.text[:100]}")
time.sleep(1)

r2 = requests.patch(f'{BASE}/rest/v1/users',
    params={'email': f'eq.{acc["email"]}'},
    headers=hdrs,
    json={'welcome_granted': True}, timeout=10)
print(f"flip: {r2.status_code} {r2.text[:200]}")
time.sleep(3)

r3 = requests.get(f'{BASE}/rest/v1/users',
    params={'select':'id,credits,welcome_granted,has_received_welcome_credits', 'email': f'eq.{acc["email"]}'},
    headers=hdrs, timeout=10)
print(f"Final row: {r3.json()}")
