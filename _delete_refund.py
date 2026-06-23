"""
Test: Generate a clip, delete the creation immediately, check if credits refund.
Also: generate → delete BEFORE completion (cancel-before-charge).
"""
import requests, json, time

T = 'uVrw1NqmIvzEcGBdHduaJwAzTySq55TN.inTUrq0EHJ%2F24cDxQXOvikggOi2Zk2AX9Olom2%2Brhqs%3D'
D = 'eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwODozMjozNi40OTFaIiwidG9rZW4iOiJ1VnJ3MU5xbUl2ekVjR0JkSGR1YUp3QXpUeVNxNTVUTiIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIiwiaWQiOiJQMUR6cVROQ1ZVeklOZ2Y5eEVDZnJtQm1mTk5NeWVwTSJ9LCJ1c2VyIjp7Im5hbWUiOiJuZmoxM0BlZHUtbWFpbC5lZHUucnMiLCJlbWFpbCI6Im5majEzQGVkdS1tYWlsLmVkdS5ycyIsImVtYWlsVmVyaWZpZWQiOnRydWUsImltYWdlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJ1cGRhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJpZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIn0sInVwZGF0ZWRBdCI6MTc3NzM2NTE1Njc0MSwidmVyc2lvbiI6IjEifSwiZXhwaXJlc0F0IjoxNzc3MzY1NDU2NzQxLCJzaWduYXR1cmUiOiJpRzIwRUl2cU5QbVhlTWg3bkhWT2lUUE5LNzNCUXNmbmp1Z09NTFVZcEE4In0'
C = {'__Secure-better-auth.session_token': T, '__Secure-better-auth.session_data': D}
H  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
      'Content-Type': 'application/json'}
H_g = {'User-Agent': H['User-Agent']}

def get_credits():
    r = requests.get('https://viddo.ai/api/user/credits', headers=H_g, cookies=C, timeout=10)
    if r.status_code == 200:
        d = r.json()
        # try common key names
        for k in ['credits', 'balance', 'remaining', 'credit']:
            if k in d:
                return d[k]
        # return full dict
        return d
    return f'HTTP {r.status_code}: {r.text[:80]}'

def get_user_info():
    r = requests.get('https://viddo.ai/api/auth/get-session', headers=H_g, cookies=C, timeout=10)
    if r.status_code == 200:
        return r.json()
    return f'HTTP {r.status_code}'

print('=== Credit Balance Check ===')
info = get_user_info()
print(f'Session: {json.dumps(info)[:300]}')
creds_before = get_credits()
print(f'Credits before: {creds_before}')

# Submit generation
print()
print('=== Submit Generation ===')
body = {
    'type': 'grok-imagine',
    'prompt': 'a simple red circle on black background',
    'duration': 10,
    'quality': '480p',
    'aspectRatio': '16:9',
    'channel': 'version2'
}
r = requests.post('https://viddo.ai/api/middle-layer', headers=H, cookies=C, json=body, timeout=15)
print(f'Submit: {r.status_code} {r.text[:200]}')
if r.status_code != 200:
    print('FAILED. Session likely expired. Update cookies.')
    exit()
d = r.json()
if 'taskId' not in d:
    print(f'No taskId: {d}')
    exit()
tid = d['taskId']
cid = d.get('id', d.get('creationId', ''))
print(f'taskId={tid}, creationId={cid}')

# Check credits right after submit (before completion)
import time; time.sleep(1)
creds_after_submit = get_credits()
print(f'Credits after submit (pre-completion): {creds_after_submit}')

# IMMEDIATELY delete the creation BEFORE it completes
print()
print(f'=== DELETE creation BEFORE completion ===')
if cid:
    rd = requests.delete(f'https://viddo.ai/api/creation?id={cid}', headers=H_g, cookies=C, timeout=10)
    print(f'DELETE (QS): {rd.status_code} {rd.text[:150]}')
    rd2 = requests.delete('https://viddo.ai/api/creation', headers=H, cookies=C, json={'id': cid}, timeout=10)
    print(f'DELETE (body): {rd2.status_code} {rd2.text[:150]}')

creds_after_delete = get_credits()
print(f'Credits after delete: {creds_after_delete}')

# Now wait for it to try to complete anyway  
print()
print('=== Poll for completion (does it still charge?) ===')
for i in range(30):
    time.sleep(5)
    rp = requests.get(f'https://viddo.ai/api/middle-layer/callback?taskId={tid}', headers=H_g, cookies=C, timeout=10)
    if rp.status_code != 200:
        print(f'Poll {i+1}: HTTP {rp.status_code}')
        break
    pd = rp.json()
    print(f'Poll {i+1}: processing={pd.get("processing")} success={pd.get("success")}')
    if not pd.get('processing') or pd.get('success'):
        break

creds_final = get_credits()
print(f'Credits final: {creds_final}')
print()
print(f'Summary: before={creds_before}, after_submit={creds_after_submit}, after_delete={creds_after_delete}, final={creds_final}')
