import json, requests
BASE = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"
ANON = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"
accs = json.load(open("zorq_farm_accounts.json"))

def refresh_jwt(rt):
    r = requests.post(f"{BASE}/auth/v1/token",
                      params={"grant_type": "refresh_token"},
                      headers={"apikey": ANON, "Content-Type": "application/json"},
                      json={"refresh_token": rt})
    if r.ok:
        d = r.json()
        return d.get("access_token"), d.get("refresh_token")
    return None, None

total = 0
for a in accs:
    jwt = a["access_token"]
    r = requests.get(f"{BASE}/rest/v1/users",
                     params={"select": "credits,is_verified", "email": f"eq.{a['email']}"},
                     headers={"apikey": ANON, "Authorization": f"Bearer {jwt}"})
    d = r.json()
    # token expired — refresh
    if not isinstance(d, list):
        jwt, new_rt = refresh_jwt(a["refresh_token"])
        if jwt:
            a["access_token"] = jwt
            if new_rt:
                a["refresh_token"] = new_rt
            r = requests.get(f"{BASE}/rest/v1/users",
                             params={"select": "credits,is_verified", "email": f"eq.{a['email']}"},
                             headers={"apikey": ANON, "Authorization": f"Bearer {jwt}"})
            d = r.json()
    row = d[0] if isinstance(d, list) and d else {}
    c = row.get("credits", "?")
    v = row.get("is_verified")
    if isinstance(c, int):
        total += c
    print(f"{a['email']:45s}  credits={str(c):>8}  verified={v}")

# save refreshed tokens
with open("zorq_farm_accounts.json", "w") as f:
    json.dump(accs, f, indent=2)

print(f"\nTotal: {total:,}")
