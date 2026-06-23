import requests, json

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H = {'apikey': ANON_KEY, 'Content-Type': 'application/json'}

# accounts created in previous test runs
emails = [
    'carriewat.son.6.682.2@gmail.com',   # went through Playwright browser flow
    'jeremypalmemr.251.98.9@gmail.com',   # confirmed but no row ever
    'coachdach.doet.kie.c@gmail.com',     # latest run with id=jwt_uid
    'richardcollins.262.4.9@gmail.com',   # first run with POST users
    'eggerandrapo.ole123.2@gmail.com',    # upsert run
    'ly.lak.ha.8.5.8@gmail.com',          # upsert run 2
]

PW = 'Hamza@12@@'
for email in emails:
    r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
                      headers=H, json={'email': email, 'password': PW}, timeout=15)
    if not r.ok or not r.json().get('access_token'):
        print(f'{email}: login FAIL ({r.status_code})')
        continue
    tok = r.json()['access_token']
    rg = requests.get(f'{BASE}/rest/v1/users',
                      params={'select': 'email,credits,welcome_granted,has_received_welcome_credits,is_verified', 'email': f'eq.{email}'},
                      headers={'Authorization': f'Bearer {tok}', 'apikey': ANON_KEY, 'Accept-Profile': 'public'}, timeout=10)
    rows = rg.json() if rg.ok else []
    if rows:
        print(f'{email}: {rows[0]}')
    else:
        print(f'{email}: NO ROW (status={rg.status_code})')
