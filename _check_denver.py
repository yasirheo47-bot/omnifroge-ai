import requests, json

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H = {'apikey': ANON, 'Content-Type': 'application/json', 'Origin': 'https://zorqai.com'}

creds = json.load(open('zorq_credentials.json'))
refresh = creds['refresh_token']

r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'refresh_token'},
    json={'refresh_token': refresh}, headers=H, timeout=10)
print('Refresh:', r.status_code)

if not r.ok:
    print('Failed:', r.text[:200])
    exit(1)

d = r.json()
jwt = d['access_token']
new_refresh = d.get('refresh_token', refresh)
uid = d['user']['id']
email = d['user']['email']

json.dump({'access_token': jwt, 'refresh_token': new_refresh, 'email': email, 'uid': uid},
          open('zorq_credentials.json', 'w'), indent=2)
print(f'Email: {email}')
print(f'uid: {uid}')

HA = {**H, 'Authorization': f'Bearer {jwt}'}

ru = requests.get(f'{BASE}/rest/v1/users',
    params={'select': 'credits,role,active_subscription,had_subscription', 'id': f'eq.{uid}'},
    headers=HA, timeout=8)
state = ru.json()[0] if ru.ok and ru.json() else ru.text
print('State:', state)

rt = requests.post(f'{BASE}/functions/v1/generateAtlasImage',
    json={'prompt': 'test landscape', 'style': 'photorealistic'},
    headers=HA, timeout=20)
print('genAtlas:', rt.status_code, rt.text[:200])
