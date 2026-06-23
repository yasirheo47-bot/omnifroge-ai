"""
Probe:
1. Read coupons table directly
2. Find Whop plan_keys from sora2_key_calls or study/ files  
3. Check generated_videos created_by column
4. Try validateCoupon with different body key names
5. Try downgradeToFree / referral flows
"""
import requests, json

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
H = {'apikey': ANON, 'Content-Type': 'application/json',
     'Origin': 'https://zorqai.com', 'User-Agent': 'Mozilla/5.0'}
PAST = '2024-01-01T00:00:00Z'

pool = json.load(open('_pool_gmail.json'))
acc  = pool[0]
r = requests.post(f'{BASE}/auth/v1/token?grant_type=password',
    json={'email': acc['email'], 'password': acc['password']}, headers=H, timeout=10)
jwt = r.json()['access_token']
uid = r.json()['user']['id']
HA  = {**H, 'Authorization': f'Bearer {jwt}'}

# 1. Read coupon tables
print("=== coupon/promo tables ===")
for tbl in ['coupons', 'promo_codes', 'promo', 'credits', 'credit_packs', 'plans',
            'subscriptions', 'products', 'packages', 'discount_codes']:
    r1 = requests.get(f'{BASE}/rest/v1/{tbl}', params={'limit': '5'}, headers=HA, timeout=6)
    if r1.status_code == 404:
        print(f"  {tbl}: 404")
    else:
        print(f"  {tbl}: {r1.status_code} {r1.text[:200]}")

# 2. validateCoupon with different key names
print("\n=== validateCoupon key names ===")
for key in ['code', 'coupon', 'coupon_code', 'promo_code', 'discount_code', 'token']:
    rc = requests.post(f'{BASE}/functions/v1/validateCoupon',
        json={key: 'ZORQTEST'}, headers=HA, timeout=6)
    if 'required' not in rc.text.lower():
        print(f"  [{key}]: {rc.status_code} {rc.text[:100]}")
    else:
        print(f"  [{key}]: still required")

# 3. generated_videos has created_by?
print("\n=== generated_videos created_by column ===")
for col in ['created_by', 'created_by_id', 'user_uuid', 'author']:
    rg = requests.get(f'{BASE}/rest/v1/generated_videos',
        params={'select': col, 'limit': '0'}, headers=HA, timeout=6)
    if rg.status_code == 200:
        print(f"  {col}: EXISTS")
    else:
        print(f"  {col}: NOT FOUND")

# 4. Try INSERT into generated_images without specifying created_by at all
print("\n=== INSERT generated_images no user field ===")
ri = requests.post(f'{BASE}/rest/v1/generated_images',
    json={'prompt': 'test', 'status': 'processing', 'credits_used': 50000,
          'next_check_at': PAST},
    headers={**HA, 'Prefer': 'return=representation'}, timeout=8)
print(f"  {ri.status_code}: {ri.text[:200]}")

# 5. Try setReferredBy with an existing referral code
# First check what referral_code values existing users have
print("\n=== check referral_codes in public.users ===")
# query users with referral_code != null (public data maybe?)
rref = requests.get(f'{BASE}/rest/v1/users',
    params={'select': 'referral_code', 'referral_code': 'not.is.null', 'limit': '5'},
    headers=HA, timeout=8)
print(f"  {rref.status_code}: {rref.text[:200]}")

# 6. Try Whop plan keys from bundle analysis
print("\n=== whopCheckout with plan_keys ===")
# Common Whop plan key patterns
for pk in ['zorq_starter', 'zorq_pro', 'zorq_free', 'starter_monthly', 'pro_monthly',
           'basic_monthly', 'free_tier', 'trial_7', 'trial_14']:
    rw = requests.post(f'{BASE}/functions/v1/whopCheckout',
        json={'plan_key': pk}, headers=HA, timeout=8)
    if 'invalid' not in rw.text.lower() and 'not found' not in rw.text.lower():
        print(f"  [{pk}]: {rw.status_code} {rw.text[:150]}")
    else:
        print(f"  [{pk}]: invalid/not found")

# 7. Try stripeCoupons function
print("\n=== stripeCoupons ===")
rs = requests.post(f'{BASE}/functions/v1/stripeCoupons', json={}, headers=HA, timeout=8)
print(f"  {rs.status_code}: {rs.text[:200]}")

# 8. adminListRefunds (maybe accessible?)
print("\n=== adminListRefunds ===")
ra = requests.post(f'{BASE}/functions/v1/adminListRefunds', json={}, headers=HA, timeout=8)
print(f"  {ra.status_code}: {ra.text[:200]}")
