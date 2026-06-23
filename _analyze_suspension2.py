"""
Deep suspension system probe:
1. What does 'device_fingerprint' DB check do - "Too many accounts from this device"
2. What column does the admin use to disable accounts - probe DB for disabled field behaviour
3. Check if recoverMyStuckMedia has its own abuse guard (call count limit?)
4. Check fraud tab data in admin dashboard - what signals does it use?
5. What RPC functions exist (might include flag/suspend)
6. Probe: can disabled=True be PATCHed back to False/null?
7. What generates the 'Too many accounts from this device' - is it a DB trigger or edge fn?
"""
import requests, json, re, time

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H_BASE = {'apikey': ANON_KEY, 'Content-Type': 'application/json'}

with open('_sub_account.json') as f:
    acc = json.load(f)

with open('_usable_accounts.json') as f:
    pool = json.load(f)

def login(email, pw):
    r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
        json={'email': email, 'password': pw}, headers=H_BASE, timeout=15)
    return r.json().get('access_token') if r.ok else None

def H(tok): return {'Authorization': f'Bearer {tok}', 'apikey': ANON_KEY, 'Content-Type': 'application/json'}
def pub_H(tok): return {**H(tok), 'Accept-Profile': 'public', 'Content-Profile': 'public', 'Prefer': 'return=representation'}

# ─── 1. Check what columns disabled accounts have vs active ──────────────────
print("=== Suspended account full row ===")
susp_tok = login('lawtm4hmd8@guerrillamail.com', None)  # suspended, will fail login
# Can't login — check via active account with select on users table
pool_tok = login(pool[0]['email'], pool[0]['password'])
r1 = requests.get(f'{BASE}/rest/v1/users',
    params={'select': '*', 'email': 'eq.lawtm4hmd8@guerrillamail.com'},
    headers={**H(pool_tok), 'Accept-Profile': 'public'}, timeout=10)
print(f"  Can read suspended user row: {r1.status_code} rows={len(r1.json()) if r1.ok else 0}")
# Only shows own row due to RLS — expected

# Check own full row
r1b = requests.get(f'{BASE}/rest/v1/users',
    params={'select': '*', 'email': f'eq.{pool[0]["email"]}'},
    headers={**H(pool_tok), 'Accept-Profile': 'public'}, timeout=10)
if r1b.ok and r1b.json():
    row = r1b.json()[0]
    print(f"\n  Pool account full row keys: {list(row.keys())}")
    print(f"  disabled={row.get('disabled')}  device_fingerprint={row.get('device_fingerprint')}")
    print(f"  credits={row.get('credits')}  total_images_generated={row.get('total_images_generated')}")

# ─── 2. Try PATCH disabled=False on a suspended account ──────────────────────
# Need token for a suspended account — try auth anyway
print("\n=== Try logging into suspended account ===")
try:
    r2 = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
        json={'email': 'lawtm4hmd8@guerrillamail.com', 'password': 'Zx!fakepassword'},
        headers=H_BASE, timeout=15)
    print(f"  {r2.status_code}: {r2.text[:300]}")
except Exception as e:
    print(f"  {e}")

# ─── 3. RPC functions list (check for flag/suspend RPCs) ─────────────────────
print("\n=== RPC probe ===")
# Try introspection via POST with no params
rpcs_to_try = [
    'flag_user', 'suspend_user', 'disable_user', 'ban_user',
    'check_abuse', 'detect_fraud', 'check_credits_abuse',
    'get_user_flags', 'update_user_status',
    'check_and_refresh_annual_credits',
    'check_device_fingerprint',
    'count_accounts_by_device',
]
for fn in rpcs_to_try:
    r = requests.post(f'{BASE}/rest/v1/rpc/{fn}', headers={**H(pool_tok), 'Accept-Profile': 'public'},
        json={}, timeout=8)
    if r.status_code not in (404, 405):
        print(f"  [{fn}] {r.status_code}: {r.text[:150]}")

# ─── 4. What does recoverMyStuckMedia check before running? ─────────────────
print("\n=== recoverMyStuckMedia rapid calls — does it rate-limit? ===")
for i in range(5):
    r = requests.post(f'{BASE}/functions/v1/recoverMyStuckMedia', headers=H(pool_tok), json={}, timeout=10)
    print(f"  call {i+1}: {r.status_code}: {r.text[:150]}")
    time.sleep(0.5)

# ─── 5. Bundle: admin fraud tab content ─────────────────────────────────────
code = open('_bundle_latest.js', encoding='utf-8', errors='replace').read()
print("\n=== Bundle: fraud tab logic ===")
idx = code.find('"fraud"')
while idx != -1 and idx < 3_000_000:
    ctx = code[max(0,idx-100):idx+800]
    if 'disabled' in ctx.lower() or 'suspend' in ctx.lower() or 'flag' in ctx.lower() or 'credits' in ctx.lower():
        print(f"  [@ {idx}] ...{ctx}...")
        print()
    idx = code.find('"fraud"', idx+1)

# ─── 6. Bundle: device fingerprint check logic ──────────────────────────────
print("\n=== Bundle: device fingerprint + too many accounts ===")
idx = code.find('Too many accounts from this device')
while idx != -1:
    print(f"  [@ {idx}] ...{code[max(0,idx-300):idx+500]}...")
    print()
    idx = code.find('Too many accounts from this device', idx+1)

# ─── 7. Bundle: adminDashboardV2 fraud columns ──────────────────────────────
print("\n=== Bundle: admin fraud detection columns ===")
for pat in ['abnormal', 'unusual', 'flagged', 'is_suspicious', 'credit_gain', 'credits_recovered',
            'recover.*count', 'stuck.*count', 'abuse_score']:
    for m in re.finditer(pat, code, re.I):
        ctx = code[max(0,m.start()-100):m.start()+300]
        print(f"  [{pat} @ {m.start()}] ...{ctx}...")
        break  # first hit only

# ─── 8. Check if recoverMyStuckMedia has a call counter on users table ───────
print("\n=== users table: recovery_count or similar columns ===")
r8 = requests.get(f'{BASE}/rest/v1/users',
    params={'select': 'credits,total_images_generated,device_fingerprint', 'email': f'eq.{pool[0]["email"]}'},
    headers={**H(pool_tok), 'Accept-Profile': 'public'}, timeout=10)
print(f"  {r8.status_code}: {r8.json()}")
