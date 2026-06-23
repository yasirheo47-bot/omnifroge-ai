import requests, json, base64, time

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'

with open('zorq_credentials.json') as f:
    creds = json.load(f)

token = creds.get('access_token', '')
refresh = creds.get('refresh_token', '')

# decode JWT to see email/exp
pl = token.split('.')[1]
pl += '=' * (-len(pl) % 4)
d = json.loads(base64.urlsafe_b64decode(pl))
email = d.get('email')
exp = d.get('exp', 0)
print(f"Email: {email}")
print(f"JWT expired: {exp < time.time()} (exp={exp}, now={int(time.time())})")
print(f"Provider: {d.get('app_metadata', {}).get('provider')}")

# try refresh
print("\n--- Refreshing token ---")
rr = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'refresh_token'},
                   json={'refresh_token': refresh},
                   headers={'apikey': ANON_KEY, 'Content-Type': 'application/json'}, timeout=15)
print(f"Refresh: {rr.status_code}")
if rr.ok:
    new_data = rr.json()
    new_token = new_data.get('access_token', '')
    new_refresh = new_data.get('refresh_token', '')
    print(f"Got new token: {bool(new_token)}")
    
    # save back
    with open('zorq_credentials.json', 'w') as f:
        json.dump({'access_token': new_token, 'refresh_token': new_refresh}, f)
    print("Saved new tokens")
    token = new_token
else:
    print(f"Refresh failed: {rr.text[:200]}")

hdrs = {'Authorization': f'Bearer {token}', 'apikey': ANON_KEY, 'Content-Type': 'application/json', 'Origin': 'https://zorqai.com', 'Referer': 'https://zorqai.com/'}

# check auth
ru = requests.get(f'{BASE}/auth/v1/user', headers=hdrs, timeout=10)
print(f"\n[auth/user] {ru.status_code}: {ru.text[:100]}")

# check public.users
rp = requests.get(f'{BASE}/rest/v1/users',
                  params={'select': 'email,role,disabled,credits', 'email': f'eq.{email}'},
                  headers={**hdrs, 'Accept-Profile': 'public'}, timeout=10)
print(f"[public.users] {rp.status_code}: {rp.text[:300]}")

# try generateSeedanceVideo
rs = requests.post(f'{BASE}/functions/v1/generateSeedanceVideo',
    headers=hdrs,
    json={'text': 'test', 'duration': 5, 'aspectRatio': '9:16', 'resolution': '480p', 'model': 'Seedance 2.0'},
    timeout=20)
print(f"\n[generateSeedanceVideo] {rs.status_code}: {rs.text[:300]}")
