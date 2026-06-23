"""
Deep analysis of the fraud/suspension system from bundle:
1. What does adminDashboardV2("fraud") return?
2. What is in recent_refunds (credit_ledgers delta < 0)?
3. What triggers the 'suspended' list?
4. What is the 'total_images_generated' counter — is it incremented by generateAtlasImage?
5. temp-mail domain block list
6. recoverMyStuckMedia token auth issue (401) — why?
"""
import re, requests, json, time

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H_BASE = {'apikey': ANON_KEY, 'Content-Type': 'application/json'}

code = open('_bundle_latest.js', encoding='utf-8', errors='replace').read()

# ─── 1. adminDashboardV2 fraud call context ───────────────────────────────────
print("=== adminDashboardV2 fraud context ===")
idx = code.find('aVe')  # aVe was the fraud component function
while idx != -1:
    ctx = code[max(0,idx-50):idx+2000]
    if 'fraud' in ctx.lower() or 'suspended' in ctx.lower() or 'refund' in ctx.lower():
        print(f"[@ {idx}] ...{ctx}...")
        break
    idx = code.find('aVe', idx+1)

# ─── 2. recent_refunds field origin ──────────────────────────────────────────
print("\n=== recent_refunds usage ===")
for m in re.finditer(r'recent_refunds', code):
    print(f"[@ {m.start()}] ...{code[max(0,m.start()-200):m.start()+500]}...")
    print()

# ─── 3. credit_ledgers — what delta values appear for recover? ───────────────
print("\n=== credit_ledgers delta / recover ===")
for m in re.finditer(r'credit_ledger|delta.*credit|ledger.*delta', code, re.I):
    ctx = code[max(0,m.start()-100):m.start()+400]
    print(f"[@ {m.start()}] ...{ctx}...")
    print()
    break  # first hit

# ─── 4. temp-mail domains block list ─────────────────────────────────────────
print("\n=== temp-mail domain block ===")
for m in re.finditer(r'temp.mail|tempmail|guerrillamail|disposable.*domain|blocked.*domain|domain.*blocked', code, re.I):
    ctx = code[max(0,m.start()-200):m.start()+500]
    print(f"[@ {m.start()}] ...{ctx}...")
    print()

# ─── 5. total_images_generated increment logic ────────────────────────────────
print("\n=== total_images_generated increment ===")
for m in re.finditer(r'total_images_generated', code, re.I):
    ctx = code[max(0,m.start()-200):m.start()+400]
    print(f"[@ {m.start()}] ...{ctx}...")
    print()

# ─── 6. recoverMyStuckMedia full bundle context (what does it invoke?) ────────
print("\n=== recoverMyStuckMedia full context ===")
for m in re.finditer(r'recoverMyStuckMedia', code):
    ctx = code[max(0,m.start()-200):m.start()+600]
    print(f"[@ {m.start()}] ...{ctx}...")
    print()

# ─── 7. What does the fraud tab show - suspended users listing ────────────────
print("\n=== Fraud tab suspended listing ===")
idx2 = code.find('Suspended users')
while idx2 != -1:
    print(f"[@ {idx2}] ...{code[max(0,idx2-100):idx2+1000]}...")
    idx2 = code.find('Suspended users', idx2+1)

# ─── 8. Probe recoverMyStuckMedia 401 — is the header format wrong? ──────────
print("\n=== recoverMyStuckMedia auth probe ===")
with open('_usable_accounts.json') as f:
    pool = json.load(f)

def login(email, pw):
    r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
        json={'email': email, 'password': pw}, headers=H_BASE, timeout=15)
    d = r.json()
    return d.get('access_token') if r.ok else None

tok = login(pool[0]['email'], pool[0]['password'])
if tok:
    print(f"  Pool token OK: {tok[:20]}...")
    # Try different auth formats
    for auth_fmt in [
        f'Bearer {tok}',
        tok,
        f'Token {tok}',
    ]:
        r = requests.post(f'{BASE}/functions/v1/recoverMyStuckMedia',
            headers={'Authorization': auth_fmt, 'apikey': ANON_KEY, 'Content-Type': 'application/json'},
            json={}, timeout=10)
        print(f"  [{auth_fmt[:20]}...] {r.status_code}: {r.text[:150]}")
else:
    print("  Login failed")
