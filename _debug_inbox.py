"""Debug: create a fresh gmail, sign up, then dump raw /app/inbox responses"""
import time, json, requests
from zorq_farm import smailpro_create_gmail, _sm_gmail_init_session, signup, SMAILPRO_GMAIL_INBOX, log

log("creating gmail...")
addr_data = smailpro_create_gmail()
print("addr:", addr_data)
if not addr_data:
    exit(1)

import random, string
email = addr_data["address"]
pw = "Zx!" + "".join(random.choices(string.ascii_lowercase + string.digits, k=14))
log(f"signing up {email}")
d = signup(email, pw)
print("signup:", d.get("id","???"), d.get("error","OK"))

sess = _sm_gmail_init_session()
payload = [{"address": addr_data["address"],
             "timestamp": addr_data["timestamp"],
             "key": addr_data["key"]}]

log("polling /app/inbox for 180s, dumping raw each cycle...")
deadline = time.time() + 180
cycle = 0
while time.time() < deadline:
    cycle += 1
    try:
        r = sess.post(SMAILPRO_GMAIL_INBOX, json=payload, timeout=15)
        print(f"\n--- cycle {cycle} | HTTP {r.status_code} ---")
        raw = r.text[:2000]
        print(raw)
        # try to decode payload JWT if present
        try:
            items = r.json()
            for it in items:
                msgs = it.get("messages", [])
                if msgs:
                    print(">>> MESSAGES FOUND:", json.dumps(msgs, indent=2)[:3000])
                    exit(0)
                pay = it.get("payload")
                if pay:
                    # decode payload JWT without verify
                    import base64
                    parts = pay.split(".")
                    if len(parts) == 3:
                        pad = parts[1] + "=="
                        decoded = json.loads(base64.urlsafe_b64decode(pad))
                        print("payload JWT decoded:", json.dumps(decoded, indent=2)[:500])
        except Exception as e:
            print("parse err:", e)
    except Exception as e:
        print("request err:", e)
    time.sleep(10)

print("\nTimed out - no messages arrived")
