"""
Deep probe:
1. Bundle search for whop webhook event format / membership activation
2. Try whop membership.was_created with various formats
3. Bundle search for mollieWebhook / Mollie flow
4. Check all payment-related edge function names in bundle
5. Check if any admin function names differ (case/variation)
"""
import re, json, requests, time

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'

with open('_sub_account.json') as f:
    acc = json.load(f)
def login():
    r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type': 'password'},
        json={'email': acc['email'], 'password': acc['password']},
        headers={'apikey': ANON_KEY, 'Content-Type': 'application/json'}, timeout=15)
    return r.json().get('access_token')
tok = login()

code = open('_bundle_latest.js', encoding='utf-8', errors='replace').read()

print("=== Bundle: whop* all occurrences ===")
for m in re.finditer(r'whop', code, re.I):
    ctx = code[max(0,m.start()-100):m.start()+300]
    print(f"[{m.start()}] ...{ctx}...")
    print()

print("\n=== Bundle: mollie* all occurrences ===")
for m in re.finditer(r'mollie', code, re.I):
    ctx = code[max(0,m.start()-100):m.start()+300]
    print(f"[{m.start()}] ...{ctx}...")
    print()

print("\n=== Bundle: ALL functions.invoke calls ===")
for m in re.finditer(r'functions\.invoke\(["\']([^"\']+)["\']', code):
    print(f"  {m.group(1)}")
