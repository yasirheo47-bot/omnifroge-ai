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

r2 = requests.get(f'{BASE}/rest/v1/users',
    params={'select':'*','email':f'eq.{acc["email"]}'},
    headers=hdrs, timeout=10)
print(json.dumps(r2.json()[0], indent=2))
