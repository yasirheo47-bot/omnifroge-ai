import requests, json, time

JWT = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImIyM2JjMjZiLWYzNWMtNDRlMi1iMDMxLTQ4ZjM0ZTA4NTk0OCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2prdGp4emp5aGJieGx4cmZtY2RrLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3NzA5MzBjMS1kMzA2LTQ2ZDAtOGRhYS1iNjdkOTNlYTVmNDQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc2ODQ3OTM1LCJpYXQiOjE3NzY4NDQzMzUsImVtYWlsIjoiaGFtemFhMTExMS5wa0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6Imdvb2dsZSIsInByb3ZpZGVycyI6WyJnb29nbGUiXX0sInVzZXJfbWV0YWRhdGEiOnsiYXZhdGFyX3VybCI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0ptV0xVZGlQUXBhcThzblFSSjRoT3k1ZllXSWt5ZW9LV0x6WEstYXNOX3hYdlA0QT1zOTYtYyIsImVtYWlsIjoiaGFtemFhMTExMS5wa0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiSGFtemEgS2hhbiIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJIYW16YSBLaGFuIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSm1XTFVkaVBRcGFxOHNuUVJKNGhPeTVmWVdJa3llb0tXTHpYSy1hc05feFh2UDRBPXM5Ni1jIiwicHJvdmlkZXJfaWQiOiIxMDg0NjM1MDE3NTMyMzgzNDgyMTYiLCJzdWIiOiIxMDg0NjM1MDE3NTMyMzgzNDgyMTYifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJvYXV0aCIsInRpbWVzdGFtcCI6MTc3NjgzNDkyOH1dLCJzZXNzaW9uX2lkIjoiNmIwNmMwYzgtNDMxZS00NmQ1LWFmYWEtM2Q3NzFiMjEzMzgxIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.92y64HO5X88xJoL3TC6_d8e77vtvRAXBvy33XDIDnEkTWNdfI91d7Uqu3gVsN4ygEjgrEnodEZIt30cp_uqkNQ"
ANON = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"
URL = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"

s = requests.Session()
s.headers.update({
    "Apikey": ANON,
    "Authorization": f"Bearer {JWT}",
    "Content-Type": "application/json",
    "Origin": "https://zorqai.com",
    "Referer": "https://zorqai.com/",
})

# fire generation
body = {"text": "a sunset over mountains", "duration": 5, "aspectRatio": "16:9", "resolution": "720p", "model": "Seedance 2.0"}
r = s.post(f"{URL}/functions/v1/generateSeedanceVideo", json=body)
print("STATUS:", r.status_code)
resp = r.json()
print("RESPONSE:", json.dumps(resp, indent=2))

# poll for result
video_id = resp.get("video_id")
if video_id:
    print(f"\nPolling video_id={video_id} ...")
    for i in range(60):
        time.sleep(6)
        pr = s.get(f"{URL}/rest/v1/generated_videos",
                   params={"select": "status,video_url,error_message,model,credits_used", "id": f"eq.{video_id}"},
                   headers={"Accept-Profile": "public"})
        rows = pr.json()
        if rows:
            row = rows[0]
            print(f"  [{i+1}] status={row['status']} url={row.get('video_url','')}")
            if row["status"] != "processing":
                print("FINAL:", json.dumps(row, indent=2))
                break
