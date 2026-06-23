"""
Check ALL account JSON files for accounts with credits > 0 and not suspended.
"""
import requests, json, os, time

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H = {'apikey': ANON_KEY, 'Content-Type': 'application/json'}

def login(email, pw):
    try:
        r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
            json={'email': email, 'password': pw}, headers=H, timeout=12)
        d = r.json()
        if r.ok and d.get('access_token'):
            return d['access_token'], None
        return None, d.get('error_description') or d.get('msg') or d.get('error') or str(d)
    except Exception as e:
        return None, str(e)

def get_user(tok, email):
    r = requests.get(f'{BASE}/rest/v1/users',
        params={'select': 'credits,multigen_credits,active_subscription,subscription_status,disabled,role', 'email': f'eq.{email}'},
        headers={'Authorization': f'Bearer {tok}', 'apikey': ANON_KEY, 'Accept-Profile': 'public'}, timeout=10)
    return r.json()[0] if r.ok and r.json() else {}

# Collect all accounts from all JSON files
accounts = {}  # email -> {password, source}

FILES = [
    'zorq_accounts_all.json',
    'zorq_batch2.json',
    'zorq_credentials.json',
    'zorq_farm_accounts.json',
    'zorq_pool.json',
    'zorq_pool_backup.json',
    '_farmed_accounts.json',
    '_sub_account.json',
    '_sub_account2.json',
]

for fn in FILES:
    if not os.path.exists(fn): continue
    try:
        data = json.load(open(fn))
        # Handle various formats
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    email = item.get('email') or item.get('user') or item.get('username')
                    pw    = item.get('password') or item.get('pass') or item.get('pw')
                    if email and pw and '@' in email:
                        accounts[email] = {'password': pw, 'source': fn}
        elif isinstance(data, dict):
            email = data.get('email') or data.get('user')
            pw    = data.get('password') or data.get('pass')
            if email and pw and '@' in email:
                accounts[email] = {'password': pw, 'source': fn}
            # Also check nested keys
            for k, v in data.items():
                if isinstance(v, dict):
                    e2 = v.get('email'); p2 = v.get('password')
                    if e2 and p2 and '@' in e2:
                        accounts[e2] = {'password': p2, 'source': f'{fn}[{k}]'}
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            e2 = item.get('email'); p2 = item.get('password') or item.get('pass')
                            if e2 and p2 and '@' in e2:
                                accounts[e2] = {'password': p2, 'source': fn}
    except Exception as ex:
        print(f"  PARSE ERROR {fn}: {ex}")

print(f"Total unique accounts: {len(accounts)}\n")
print(f"{'EMAIL':<45} {'CREDITS':>8} {'MULTI':>6} {'PLAN':<20} STATUS")
print("-" * 110)

good = []
bad  = []

for email, info in accounts.items():
    tok, err = login(email, info['password'])
    if not tok:
        bad.append({'email': email, 'reason': err, 'source': info['source']})
        print(f"  ✗ {email:<43} LOGIN FAIL: {err}")
        time.sleep(0.3)
        continue
    
    user = get_user(tok, email)
    credits     = user.get('credits', 0) or 0
    multi       = user.get('multigen_credits', 0) or 0
    sub         = user.get('active_subscription') or 'none'
    disabled    = user.get('disabled')
    
    suspended = bool(disabled)
    has_credits = credits > 0 or multi > 0 or sub not in ('none', None, 'null')
    
    if has_credits and not suspended:
        flag = '✓✓✓'
        good.append({'email': email, 'password': info['password'], 'credits': credits, 'multigen': multi, 'plan': sub, 'source': info['source'], 'token': tok})
    elif suspended:
        flag = 'SUSPENDED'
    else:
        flag = '—'
    
    print(f"  {flag} {email:<43} credits={credits:>6} multi={multi:>5} plan={str(sub):<20} disabled={disabled}")
    time.sleep(0.4)

print(f"\n{'='*80}")
print(f"USABLE ACCOUNTS ({len(good)} found):")
for a in good:
    print(f"  email: {a['email']}")
    print(f"  pass:  {a['password']}")
    print(f"  credits: {a['credits']}  multigen: {a['multigen']}  plan: {a['plan']}")
    print(f"  source: {a['source']}")
    print()

print(f"\nFAILED LOGINS ({len(bad)}):")
for a in bad:
    print(f"  {a['email']} — {a['reason']}")

# Save usable accounts
if good:
    with open('_usable_accounts.json', 'w') as f:
        json.dump(good, f, indent=2)
    print(f"\nSaved {len(good)} usable accounts to _usable_accounts.json")
