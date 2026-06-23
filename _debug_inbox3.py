"""Debug: fetch full message body using mid"""
import time, json, requests, base64
from zorq_farm import smailpro_create_gmail, _sm_gmail_init_session, signup, log

SMAILPRO_GMAIL_INBOX = "https://smailpro.com/app/inbox"
SONJJ_INBOX = "https://api.sonjj.com/v1/temp_gmail/inbox"
# common patterns for message fetch:
SONJJ_MSG_PATTERNS = [
    "https://api.sonjj.com/v1/temp_gmail/message",   # ?mid=X&payload=Y
    "https://api.sonjj.com/v1/temp_gmail/email",      # ?mid=X&payload=Y
    "https://api.sonjj.com/v1/temp_gmail/read",       # ?mid=X&payload=Y
    "https://api.sonjj.com/v1/temp_gmail/mail",
]

log("creating gmail...")
addr_data = smailpro_create_gmail()
print("addr:", addr_data["address"])

import random, string
email = addr_data["address"]
pw = "Zx!" + "".join(random.choices(string.ascii_lowercase + string.digits, k=14))
log(f"signing up {email}")
d = signup(email, pw)
print("signup:", d.get("id","???"), d.get("error","OK"))

sess = _sm_gmail_init_session()
inbox_payload = [{"address": addr_data["address"],
                   "timestamp": addr_data["timestamp"],
                   "key": addr_data["key"]}]

log("polling for email + probing message fetch...")
deadline = time.time() + 180
current_payload_jwt = None

while time.time() < deadline:
    r = sess.post(SMAILPRO_GMAIL_INBOX, json=inbox_payload, timeout=15)
    items = r.json()
    item = items[0] if items else {}
    if item.get("payload"):
        current_payload_jwt = item["payload"]

    if current_payload_jwt:
        r2 = requests.get(SONJJ_INBOX, params={"payload": current_payload_jwt}, timeout=15)
        data2 = r2.json()
        msgs = data2.get("messages", [])
        if msgs:
            print("Message metadata:", json.dumps(msgs, indent=2))
            mid = msgs[0]["mid"]
            print(f"\n>>> Got mid={mid}, probing fetch endpoints...")
            # try each pattern
            for url in SONJJ_MSG_PATTERNS:
                for param_combo in [
                    {"mid": mid, "payload": current_payload_jwt},
                    {"id": mid, "payload": current_payload_jwt},
                    {"mid": mid},
                ]:
                    try:
                        rx = requests.get(url, params=param_combo, timeout=10)
                        print(f"\n  GET {url} params={list(param_combo.keys())} → HTTP {rx.status_code}")
                        print("  ", rx.text[:500])
                    except Exception as e:
                        print(f"  {url}: {e}")
            # also try POST variants
            for url in SONJJ_MSG_PATTERNS:
                try:
                    rx = requests.post(url, json={"mid": mid, "payload": current_payload_jwt}, timeout=10)
                    print(f"\n  POST {url} → HTTP {rx.status_code}")
                    print("  ", rx.text[:500])
                except Exception as e:
                    print(f"  POST {url}: {e}")
            exit(0)
    time.sleep(10)

print("timed out")
