import base64, json, requests

SUPABASE_URL = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"
ANON_KEY = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"
JWT = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImIyM2JjMjZiLWYzNWMtNDRlMi1iMDMxLTQ4ZjM0ZTA4NTk0OCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2prdGp4emp5aGJieGx4cmZtY2RrLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3NzA5MzBjMS1kMzA2LTQ2ZDAtOGRhYS1iNjdkOTNlYTVmNDQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc2ODQ0MzUyLCJpYXQiOjE3NzY4NDA3NTIsImVtYWlsIjoiaGFtemFhMTExMS5wa0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6Imdvb2dsZSIsInByb3ZpZGVycyI6WyJnb29nbGUiXX0sInVzZXJfbWV0YWRhdGEiOnsiYXZhdGFyX3VybCI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0ptV0xVZGlQUXBhcThzblFSSjRoT3k1ZllXSWt5ZW9LV0x6WEstYXNOX3hYdlA0QT1zOTYtYyIsImVtYWlsIjoiaGFtemFhMTExMS5wa0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiSGFtemEgS2hhbiIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJIYW16YSBLaGFuIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSm1XTFVkaVBRcGFxOHNuUVJKNGhPeTVmWVdJa3llb0tXTHpYSy1hc05feFh2UDRBPXM5Ni1jIiwicHJvdmlkZXJfaWQiOiIxMDg0NjM1MDE3NTMyMzgzNDgyMTYiLCJzdWIiOiIxMDg0NjM1MDE3NTMyMzgzNDgyMTYifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJvYXV0aCIsInRpbWVzdGFtcCI6MTc3NjgzNDkyOH1dLCJzZXNzaW9uX2lkIjoiNmIwNmMwYzgtNDMxZS00NmQ1LWFmYWEtM2Q3NzFiMjEzMzgxIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.jPe1vYPZARKn8WBsImoFBc4RbdEOkqmF24crdE6zjkgAjDEJpolyrq8yqZODEEs6DPaYOFcGEgLxaPgy6Fzh1A"

# decode JWT
payload_b64 = JWT.split(".")[1]
payload_b64 += "=" * (-len(payload_b64) % 4)
jwt_data = json.loads(base64.urlsafe_b64decode(payload_b64))
print("JWT sub (auth.uid):", jwt_data["sub"])
print("JWT email:", jwt_data["email"])

s = requests.Session()
s.headers.update({
    "Apikey": ANON_KEY,
    "Authorization": f"Bearer {JWT}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://zorqai.com",
    "Referer": "https://zorqai.com/",
})

# fetch full user row to see all columns
r = s.get(f"{SUPABASE_URL}/rest/v1/users",
    params={"select": "*", "email": f"eq.{jwt_data['email']}"},
    headers={"Accept-Profile": "public"})
print("\nGET /rest/v1/users response status:", r.status_code)
if r.ok:
    rows = r.json()
    if rows:
        print("Full row:")
        for k, v in rows[0].items():
            print(f"  {k}: {v}")
    else:
        print("  Empty result")
else:
    print("Error:", r.text[:300])

# now try PATCH using jwt sub as the id (maybe RLS matches on auth.uid())
print("\n--- PATCH attempt using jwt sub ---")
r2 = s.patch(f"{SUPABASE_URL}/rest/v1/users",
    params={"id": f"eq.{jwt_data['sub']}"},
    headers={"Content-Profile": "public", "Prefer": "return=representation,count=exact"},
    json={"credits": 99999, "multigen_credits": 99999})
print("PATCH status:", r2.status_code)
print("PATCH headers:", dict(r2.headers))
print("PATCH body:", r2.text[:400])
