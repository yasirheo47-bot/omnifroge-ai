import requests, json, base64, time

BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'

with open('zorq_pool.json') as f:
    pool = json.load(f)

active = [a for a in pool if a.get('active', True) and (a.get('credits') or 0) > 0]
print(f"Active accounts with credits: {len(active)}")

for acc in active[:3]:
    email = acc.get('email', '')
    token = acc.get('access_token', '')
    credits = acc.get('credits', 0)

    # check token expiry
    pl = token.split('.')[1]
    pl += '=' * (-len(pl) % 4)
    d = json.loads(base64.urlsafe_b64decode(pl))
    exp = d.get('exp', 0)
    expired = exp < time.time()

    hdrs = {
        'Authorization': f'Bearer {token}',
        'apikey': ANON_KEY,
        'Content-Type': 'application/json',
    }

    # 1. check /auth/v1/user
    ru = requests.get(f'{BASE}/auth/v1/user', headers=hdrs, timeout=10)
    user_ok = ru.status_code == 200

    # 2. check public.users row (credits, is_verified)
    rp = requests.get(f'{BASE}/rest/v1/users',
                      params={'select': 'email,credits,is_verified', 'email': f'eq.{email}'},
                      headers={**hdrs, 'Accept-Profile': 'public'}, timeout=10)
    pub_row = rp.json() if rp.ok else rp.text[:100]

    # 3. try uploadToCloudinaryDirect
    tiny = base64.b64decode('/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8AVf/Z')
    rc = requests.post(
        f'{BASE}/functions/v1/uploadToCloudinaryDirect',
        headers=hdrs,
        json={'fileData': base64.b64encode(tiny).decode()},
        timeout=30,
    )

    # 4. try generateSeedanceVideo (dry — just check if accepted)
    rs = requests.post(
        f'{BASE}/functions/v1/generateSeedanceVideo',
        headers=hdrs,
        json={'text': 'test', 'duration': 5, 'aspectRatio': '9:16', 'resolution': '480p', 'model': 'Seedance 2.0'},
        timeout=20,
    )

    print(f"\n{'='*60}")
    print(f"Email:    {email}")
    print(f"Credits:  {credits} | JWT expired: {expired}")
    print(f"/user:    {ru.status_code}")
    print(f"pub.users:{pub_row}")
    print(f"Cloudinary: {rc.status_code} {rc.text[:150]}")
    print(f"Seedance:   {rs.status_code} {rs.text[:200]}")
