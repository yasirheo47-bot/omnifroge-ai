import json, base64, requests, uuid
from datetime import datetime, timezone, timedelta

with open('zorq_batch2.json') as f:
    data = json.load(f)

nonzero = [a for a in data if isinstance(a, dict) and (a.get('credits') or 0) > 0]
print(f'Accounts with credits: {len(nonzero)}')

if nonzero:
    acc = nonzero[0]
    print('Email:', acc.get('email'))
    print('Credits:', acc.get('credits'))
    jwt = acc.get('access_token', '') or acc.get('jwt', '')
    if jwt:
        pl = jwt.split('.')[1]
        pl += '=' * (-len(pl) % 4)
        d = json.loads(base64.urlsafe_b64decode(pl))
        print('provider:', d.get('app_metadata', {}).get('provider'))
        print('amr method:', d.get('amr', [{}])[0].get('method'))
        print('exp:', d.get('exp'))
        import time
        print('expired?', d.get('exp', 0) < time.time())

    # Try re-login to get fresh JWT
    email = acc.get('email', '')
    pw = acc.get('password', '')
    if email and pw:
        print(f'\nTrying re-login for {email}...')
        BASE = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"
        H = {"apikey": "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn", "Content-Type": "application/json"}
        r = requests.post(f"{BASE}/auth/v1/token", params={"grant_type": "password"},
                          json={"email": email, "password": pw}, headers=H, timeout=15)
        print(f"Login → {r.status_code}")
        d2 = r.json()
        if d2.get('access_token'):
            fresh_jwt = d2['access_token']
            print('Got fresh JWT')
            # Try INSERT
            hdrs = {**H, "Authorization": f"Bearer {fresh_jwt}"}
            s = requests.Session()
            s.headers.update(hdrs)
            now = datetime.now(timezone.utc)
            past = now - timedelta(hours=4)
            row = {
                "id": str(uuid.uuid4()),
                "prompt": "test from old account",
                "status": "processing",
                "user_email": email,
                "credits_used": 100,
                "model": "Seedance 2.0",
                "duration": "5",
                "resolution": "720p",
                "provider": "wavespeed",
                "task_id": uuid.uuid4().hex,
                "provider_job_id": uuid.uuid4().hex,
                "ingestion_stage": "provider_failed",
                "attempts": 1,
                "source_images": [],
                "tags": [],
                "next_check_at": past.isoformat(),
                "created_at": past.isoformat(),
                "updated_at": past.isoformat(),
            }
            ri = s.post(f"{BASE}/rest/v1/generated_videos",
                        headers={"Content-Profile": "public", "Prefer": "return=minimal"},
                        json=row, timeout=10)
            print(f"INSERT with OLD account → HTTP {ri.status_code}")
            print(ri.text[:300])
        else:
            print('Login failed:', d2.get('error_description', d2))
