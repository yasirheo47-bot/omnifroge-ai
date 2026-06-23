import requests, json

JWT = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImIyM2JjMjZiLWYzNWMtNDRlMi1iMDMxLTQ4ZjM0ZTA4NTk0OCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2prdGp4emp5aGJieGx4cmZtY2RrLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3NzA5MzBjMS1kMzA2LTQ2ZDAtOGRhYS1iNjdkOTNlYTVmNDQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc2ODQ3OTM1LCJpYXQiOjE3NzY4NDQzMzUsImVtYWlsIjoiaGFtemFhMTExMS5wa0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6Imdvb2dsZSIsInByb3ZpZGVycyI6WyJnb29nbGUiXX0sInVzZXJfbWV0YWRhdGEiOnsiYXZhdGFyX3VybCI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0ptV0xVZGlQUXBhcThzblFSSjRoT3k1ZllXSWt5ZW9LV0x6WEstYXNOX3hYdlA0QT1zOTYtYyIsImVtYWlsIjoiaGFtemFhMTExMS5wa0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiSGFtemEgS2hhbiIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJIYW16YSBLaGFuIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSm1XTFVkaVBRcGFxOHNuUVJKNGhPeTVmWVdJa3llb0tXTHpYSy1hc05feFh2UDRBPXM5Ni1jIiwicHJvdmlkZXJfaWQiOiIxMDg0NjM1MDE3NTMyMzgzNDgyMTYiLCJzdWIiOiIxMDg0NjM1MDE3NTMyMzgzNDgyMTYifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJvYXV0aCIsInRpbWVzdGFtcCI6MTc3NjgzNDkyOH1dLCJzZXNzaW9uX2lkIjoiNmIwNmMwYzgtNDMxZS00NmQ1LWFmYWEtM2Q3NzFiMjEzMzgxIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.92y64HO5X88xJoL3TC6_d8e77vtvRAXBvy33XDIDnEkTWNdfI91d7Uqu3gVsN4ygEjgrEnodEZIt30cp_uqkNQ"
ANON = "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn"
URL = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"

s = requests.Session()
s.headers.update({"Apikey": ANON, "Authorization": f"Bearer {JWT}", "Content-Type": "application/json"})

# Get ALL fields from the completed video
video_id = "2eaeee55-e37a-4863-bc3a-93e2cca883fe"
r = s.get(f"{URL}/rest/v1/generated_videos",
          params={"select": "*", "id": f"eq.{video_id}"},
          headers={"Accept-Profile": "public"})
row = r.json()[0]
print("=== ALL FIELDS ===")
for k, v in row.items():
    if v is not None:
        print(f"  {k}: {v}")

# Check if mp4 exists at same path
jpg_url = row.get("video_url", "")
mp4_url = jpg_url.replace(".jpg", ".mp4")
print(f"\n=== CHECKING MP4 URL ===")
print(f"  jpg: {jpg_url}")
print(f"  mp4: {mp4_url}")
r2 = requests.head(mp4_url, timeout=10)
print(f"  mp4 HEAD status: {r2.status_code}, content-type: {r2.headers.get('content-type')}")

# Also check recent videos to find any mp4s in history
print("\n=== RECENT COMPLETED VIDEOS ===")
r3 = s.get(f"{URL}/rest/v1/generated_videos",
           params={"select": "id,model,video_url,status,created_at", "status": "eq.completed",
                   "order": "created_at.desc", "limit": "10"},
           headers={"Accept-Profile": "public"})
for v in r3.json():
    url = v.get("video_url", "")
    ext = url.split(".")[-1].split("?")[0] if url else "none"
    print(f"  [{v['model']}] {ext} — {url[-50:] if url else 'no url'}")
