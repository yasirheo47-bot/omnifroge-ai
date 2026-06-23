import requests, json

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'

pool = json.load(open('_usable_accounts.json'))

print(f"{'Email':<38} {'Credits':>8}  {'disabled':>8}  {'role':<12}  Status")
print("-" * 90)

for a in pool:
    r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type':'password'},
        json={'email': a['email'], 'password': a['password']},
        headers={'apikey': ANON_KEY, 'Content-Type': 'application/json'}, timeout=10)
    if not (r.ok and r.json().get('access_token')):
        print(f"{a['email']:<38}  LOGIN FAILED: {r.text[:80]}")
        continue
    tok = r.json()['access_token']
    u = requests.get(f'{BASE}/rest/v1/users',
        params={'select': 'email,credits,disabled,role'},
        headers={'Authorization': f'Bearer {tok}', 'apikey': ANON_KEY,
                 'Accept-Profile': 'public'}, timeout=10)
    row = u.json()[0] if u.ok and u.json() else {}
    disabled = row.get('disabled', '?')
    role     = row.get('role', '?')
    credits  = row.get('credits', '?')
    # suspended if disabled=True OR role='suspended'
    if disabled == True or role == 'suspended':
        flag = '🚫 SUSPENDED'
    else:
        flag = '✅ active'
    print(f"{a['email']:<38} {str(credits):>8}  {str(disabled):>8}  {str(role):<12}  {flag}")

if False:  # old code below kept for reference
    email = None
    token = None

hdrs = {
    'Authorization': f'Bearer {token}',
    'apikey': ANON_KEY,
    'Content-Type': 'application/json',
    'Origin': 'https://zorqai.com',
    'Referer': 'https://zorqai.com/',
}

# 1. Check auth/user — is the account alive at all?
ru = requests.get(f'{BASE}/auth/v1/user', headers=hdrs, timeout=10)
print(f"[auth/user] {ru.status_code}: {ru.text[:300]}")

# 2. Try generateSeedanceVideo and print FULL response
rs = requests.post(
    f'{BASE}/functions/v1/generateSeedanceVideo',
    headers=hdrs,
    json={'text': 'test', 'duration': 5, 'aspectRatio': '9:16', 'resolution': '480p', 'model': 'Seedance 2.0'},
    timeout=20,
)
print(f"\n[generateSeedanceVideo] HTTP {rs.status_code}")
print("Response headers:", dict(rs.headers))
print("Body:", rs.text[:500])

# 3. Check if there's an is_banned or suspended flag in public.users
rp = requests.get(f'{BASE}/rest/v1/users',
                  params={'select': '*', 'email': f'eq.{email}'},
                  headers={**hdrs, 'Accept-Profile': 'public'}, timeout=10)
print(f"\n[public.users full row] {rp.status_code}: {rp.text[:500]}")

# 4. Try re-login with password to get a fresh JWT
pw = acc.get('password', '')
if pw:
    rl = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
                       json={'email': email, 'password': pw}, headers=hdrs, timeout=15)
    print(f"\n[re-login] {rl.status_code}: {rl.text[:300]}")
    if rl.ok:
        fresh = rl.json().get('access_token', '')
        hdrs2 = {**hdrs, 'Authorization': f'Bearer {fresh}'}
        rs2 = requests.post(
            f'{BASE}/functions/v1/generateSeedanceVideo',
            headers=hdrs2,
            json={'text': 'test', 'duration': 5, 'aspectRatio': '9:16', 'resolution': '480p', 'model': 'Seedance 2.0'},
            timeout=20,
        )
        print(f"\n[generateSeedanceVideo with fresh JWT] HTTP {rs2.status_code}: {rs2.text[:300]}")
