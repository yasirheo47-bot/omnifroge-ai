import json, requests, os

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H = {'apikey': ANON, 'Content-Type': 'application/json'}

with open('zorq_pool.json', encoding='utf-8') as f:
    pool = json.load(f)

def relogin(email, password):
    r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
                      json={'email': email, 'password': password}, headers=H, timeout=15)
    return r.json() if r.ok else {}

def get_credits(tok, email):
    s = requests.Session()
    s.headers.update({**H, 'Authorization': f'Bearer {tok}'})
    r = s.get(f'{BASE}/rest/v1/users',
              params={'select': 'credits', 'email': f'eq.{email}'},
              headers={'Accept-Profile': 'public'}, timeout=10)
    if r.ok and r.json():
        return r.json()[0]['credits']
    return None

updated = []
results = []
for i, acc in enumerate(pool):
    email = acc.get('email', '')
    pw    = acc.get('password', '')
    tok   = acc.get('access_token', '')
    cr = get_credits(tok, email)
    relogged = False
    if cr is None and pw:
        data = relogin(email, pw)
        if data.get('access_token'):
            tok = data['access_token']
            acc['access_token'] = tok
            acc['refresh_token'] = data.get('refresh_token', acc.get('refresh_token', ''))
            relogged = True
            cr = get_credits(tok, email)
    tag = ' [re-logged]' if relogged else ''
    cr_str = str(cr) if cr is not None else 'FAIL'
    print(f'[{i+1:3d}] {email:45s}  cr={cr_str:>6}{tag}')
    if cr is not None:
        acc['credits'] = cr
    results.append((email, cr))
    updated.append(acc)

tmp = 'zorq_pool.json.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(updated, f, indent=2)
os.replace(tmp, 'zorq_pool.json')

print()
above_200 = [c for e, c in results if isinstance(c, int) and c >= 200]
above_300 = [c for e, c in results if isinstance(c, int) and c >= 300]
zero_cr   = [e for e, c in results if isinstance(c, int) and c == 0]
fail_cr   = [e for e, c in results if c is None]
print(f'Total   : {len(results)}')
print(f'>=300cr : {len(above_300)}')
print(f'>=200cr : {len(above_200)}')
print(f'=0cr    : {len(zero_cr)}')
print(f'FAIL    : {len(fail_cr)}')
if fail_cr:
    print('Failed accounts:')
    for e in fail_cr:
        print(f'  {e}')
    cr = a.get('credits', 0) or 0
    total += cr
    print(f"[{status}] {a['email'][:38]:<38} {cr:>10,} cr")
print(f"\n{'='*55}")
print(f"Total : {total:>10,} credits")
print(f"Active: {len(pool)-inactive:>10} / {len(pool)} accounts")
if inactive:
    print(f"Inactive: {inactive} accounts")
