"""Check current credit balance and find creation by taskId"""
import requests, json

T = 'uVrw1NqmIvzEcGBdHduaJwAzTySq55TN.inTUrq0EHJ%2F24cDxQXOvikggOi2Zk2AX9Olom2%2Brhqs%3D'
D = 'eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwODozMjozNi40OTFaIiwidG9rZW4iOiJ1VnJ3MU5xbUl2ekVjR0JkSGR1YUp3QXpUeVNxNTVUTiIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIiwiaWQiOiJQMUR6cVROQ1ZVeklOZ2Y5eEVDZnJtQm1mTk5NeWVwTSJ9LCJ1c2VyIjp7Im5hbWUiOiJuZmoxM0BlZHUtbWFpbC5lZHUucnMiLCJlbWFpbCI6Im5majEzQGVkdS1tYWlsLmVkdS5ycyIsImVtYWlsVmVyaWZpZWQiOnRydWUsImltYWdlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJ1cGRhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJpZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIn0sInVwZGF0ZWRBdCI6MTc3NzM2NTE1Njc0MSwidmVyc2lvbiI6IjEifSwiZXhwaXJlc0F0IjoxNzc3MzY1NDU2NzQxLCJzaWduYXR1cmUiOiJpRzIwRUl2cU5QbVhlTWg3bkhWT2lUUE5LNzNCUXNmbmp1Z09NTFVZcEE4In0'
C = {'__Secure-better-auth.session_token': T, '__Secure-better-auth.session_data': D}
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0'}

print('=== Credit balance check ===')
for endpoint in ['/api/user', '/api/me', '/api/account', '/api/credits',
                 '/api/user/info', '/api/user/credits', '/api/profile',
                 '/api/subscription', '/api/plan']:
    r = requests.get(f'https://viddo.ai{endpoint}', headers=H, cookies=C, timeout=10)
    if r.status_code == 200 and r.headers.get('content-type','').startswith('application/json'):
        try:
            d = r.json()
            text = json.dumps(d)
            if any(k in text.lower() for k in ['credit', 'balance', 'token', 'quota']):
                print(f'{endpoint}: {text[:300]}')
            else:
                print(f'{endpoint}: 200 json (no credit key) {text[:80]}')
        except:
            print(f'{endpoint}: 200 non-json {r.text[:60]}')
    elif r.status_code != 404:
        print(f'{endpoint}: {r.status_code}')

# Also try auth session endpoint (better-auth)
print()
print('=== better-auth session ===')
r = requests.get('https://viddo.ai/api/auth/get-session', headers=H, cookies=C, timeout=10)
print(f'status={r.status_code}')
if r.status_code == 200:
    try:
        d = r.json()
        print(json.dumps(d, indent=2)[:500])
    except:
        print(r.text[:200])

# Try to find creation by taskId
print()
print('=== creation by taskId ===')
test_tid = '019dd384-c731-7809-8da0-09b32aabf0bd'  # ch-free
for endpoint in [
    f'/api/creation?taskId={test_tid}',
    f'/api/creation/{test_tid}',
    f'/api/task/{test_tid}',
    f'/api/middle-layer/{test_tid}',
]:
    r = requests.get(f'https://viddo.ai{endpoint}', headers=H, cookies=C, timeout=10)
    if r.status_code == 200:
        print(f'{endpoint}: {r.text[:200]}')
    else:
        print(f'{endpoint}: {r.status_code}')
