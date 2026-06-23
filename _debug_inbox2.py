"""Debug: create gmail, sign up, poll via api.sonjj.com/v1/temp_gmail/inbox"""
import time, json, requests, base64
from zorq_farm import smailpro_create_gmail, _sm_gmail_init_session, signup, log
SMAILPRO_GMAIL_INBOX = "https://smailpro.com/app/inbox"

SONJJ_INBOX = "https://api.sonjj.com/v1/temp_gmail/inbox"

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

def decode_jwt_payload(token):
    try:
        parts = token.split(".")
        if len(parts) == 3:
            pad = parts[1] + "=="
            return json.loads(base64.urlsafe_b64decode(pad))
    except:
        pass
    return None

log("polling for 180s (also hitting api.sonjj.com)...")
deadline = time.time() + 180
cycle = 0
current_payload_jwt = None

while time.time() < deadline:
    cycle += 1
    try:
        r = sess.post(SMAILPRO_GMAIL_INBOX, json=payload, timeout=15)
        items = r.json()
        item = items[0] if items else {}

        # update payload JWT for sonjj call
        if item.get("payload"):
            current_payload_jwt = item["payload"]

        # check messages in /app/inbox response
        msgs = item.get("messages", [])
        if msgs:
            print(f"\n>>> MESSAGES in /app/inbox cycle {cycle}:", json.dumps(msgs, indent=2)[:3000])
            exit(0)

        # call api.sonjj.com with the payload JWT
        if current_payload_jwt:
            r2 = requests.get(SONJJ_INBOX, params={"payload": current_payload_jwt}, timeout=15)
            print(f"\n--- cycle {cycle} | sonjj HTTP {r2.status_code} ---")
            raw2 = r2.text[:2000]
            print(raw2)
            try:
                data2 = r2.json()
                # check for messages in sonjj response
                if isinstance(data2, dict):
                    msgs2 = data2.get("messages") or data2.get("data") or data2.get("items")
                    if msgs2:
                        print(f"\n>>> SONJJ MESSAGES cycle {cycle}:", json.dumps(msgs2, indent=2)[:3000])
                        exit(0)
                elif isinstance(data2, list) and data2:
                    print("sonjj returned list:", json.dumps(data2, indent=2)[:2000])
            except Exception as e:
                print("sonjj parse err:", e)
        else:
            print(f"cycle {cycle}: no payload JWT yet")

    except Exception as e:
        print(f"cycle {cycle} err:", e)

    time.sleep(10)

print("\nTimed out - no messages arrived")
