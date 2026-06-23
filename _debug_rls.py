"""Probe generated_videos table: schema + full 403 error"""
import requests, json, base64
from zorq_farm import smailpro_create_gmail, _sm_gmail_init_session, signup, confirm_via_link, log
import random, string, uuid
from datetime import datetime, timezone, timedelta

H = {
    "apikey": "sb_publishable_e73eRpNExa0833HiNyj9XQ_9akW10Sn",
    "Content-Type": "application/json",
}
BASE = "https://jktjxzjyhbbxlxrfmcdk.supabase.co"

log("creating account...")
addr_data = smailpro_create_gmail()
email = addr_data["address"]
pw = "Zx!" + "".join(random.choices(string.ascii_lowercase + string.digits, k=14))
signup(email, pw)
sess_sm = _sm_gmail_init_session()
from zorq_farm import smailpro_poll_gmail_inbox, extract_confirm_link, SMAILPRO_GMAIL_INBOX
import time

# poll
inbox_payload = [{"address": addr_data["address"], "timestamp": addr_data["timestamp"], "key": addr_data["key"]}]
from zorq_farm import SONJJ_INBOX_URL, SONJJ_MESSAGE_URL
deadline = time.time() + 120
payload_jwt = None
link = None
while time.time() < deadline:
    r = sess_sm.post(SMAILPRO_GMAIL_INBOX, json=inbox_payload, timeout=15)
    items = r.json()
    item = items[0] if items else {}
    if item.get("payload"):
        payload_jwt = item["payload"]
    if payload_jwt:
        r2 = requests.get(SONJJ_INBOX_URL, params={"payload": payload_jwt}, timeout=15)
        msgs = r2.json().get("messages", [])
        for msg in msgs:
            mid = msg.get("mid")
            if mid:
                r3 = requests.get(SONJJ_MESSAGE_URL, params={"mid": mid, "payload": payload_jwt}, timeout=15)
                body = r3.json().get("body", "")
                link = extract_confirm_link(body)
                if link:
                    break
    if link:
        break
    time.sleep(8)

if not link:
    print("No confirm link!")
    exit(1)

print("confirm link found")
cd = confirm_via_link(link)
access_token = cd.get("access_token")
print(f"access_token: {access_token[:40]}...")

# Decode JWT
pl = access_token.split(".")[1]
pl += "=" * (-len(pl) % 4)
jwt_data = json.loads(base64.urlsafe_b64decode(pl))
print("JWT claims:", json.dumps({k:v for k,v in jwt_data.items() if k != 'app_metadata'}, indent=2))

hdrs = {**H, "Authorization": f"Bearer {access_token}"}
s = requests.Session()
s.headers.update(hdrs)

# --- probe schema via OPTIONS or empty SELECT ---
print("\n=== Schema probe ===")
r = s.get(f"{BASE}/rest/v1/generated_videos", params={"limit": "0"}, timeout=10)
print(f"SELECT limit=0 → {r.status_code}")
print(r.text[:300])
print("Headers:", dict(list(r.headers.items())[:10]))

# --- try minimal insert to get full error ---
print("\n=== Minimal INSERT ===")
now = datetime.now(timezone.utc)
past = now - timedelta(hours=4)
row = {
    "id":              str(uuid.uuid4()),
    "prompt":          "test",
    "status":          "processing",
    "user_email":      email,
    "credits_used":    100,
    "model":           "Seedance 2.0",
    "duration":        "5",
    "resolution":      "720p",
    "provider":        "wavespeed",
    "task_id":         uuid.uuid4().hex,
    "provider_job_id": uuid.uuid4().hex,
    "ingestion_stage": "provider_failed",
    "attempts":        1,
    "source_images":   [],
    "tags":            [],
    "next_check_at":   past.isoformat(),
    "created_at":      past.isoformat(),
    "updated_at":      past.isoformat(),
}
ri = s.post(f"{BASE}/rest/v1/generated_videos",
            headers={"Content-Profile": "public", "Prefer": "return=minimal"},
            json=row, timeout=10)
print(f"INSERT → HTTP {ri.status_code}")
print(ri.text[:500])
