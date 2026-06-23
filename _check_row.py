import requests, json
BASE = 'https://jktjxzjyhbbxlxrfmcdk.supabase.co'
ANON_KEY = 'sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn'
with open('_sub_account.json') as f:
    acc = json.load(f)
r = requests.post(f'{BASE}/auth/v1/token', params={'grant_type':'password'},
    json={'email':acc['email'],'password':acc['password']},
    headers={'apikey':ANON_KEY,'Content-Type':'application/json'}, timeout=15)
token = r.json()['access_token']
hdrs = {'Authorization':f'Bearer {token}','apikey':ANON_KEY,'Content-Type':'application/json','Accept-Profile':'public'}

# Get full row
r2 = requests.get(f'{BASE}/rest/v1/generated_videos',
    params={'select':'*','id':'eq.1ba16002-956c-4553-8e2f-11299e49abf0'},
    headers=hdrs, timeout=10)
print(json.dumps(r2.json(), indent=2))

# Also get credits
r3 = requests.get(f'{BASE}/rest/v1/users',
    params={'select':'credits','email':f'eq.{acc["email"]}'},
    headers=hdrs, timeout=10)
print("CREDITS:", r3.json())
