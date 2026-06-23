import requests, json

TOK = "8688029430:AAFvF12f1XiEzvNcfdqjQdOV2rru9ZcbrSg"
BASE = f"https://api.telegram.org/bot{TOK}"

# Get last update id
r = requests.get(f"{BASE}/getUpdates?limit=100&timeout=0")
d = r.json()
updates = d.get("result", [])
print(f"Pending updates: {len(updates)}")
if updates:
    for u in updates:
        print(f"  #{u['update_id']}  from={u.get('message',{}).get('from',{}).get('username','?')}  text={u.get('message',{}).get('text','?')[:40]}")
    last_id = updates[-1]["update_id"]
    # Acknowledge all — set offset to last+1
    r2 = requests.get(f"{BASE}/getUpdates?offset={last_id+1}&timeout=0")
    print(f"\nAcknowledged all up to #{last_id}")
    print(f"Queue now: {r2.json()}")
else:
    print("Queue is empty — bot should receive fresh updates now")

# Also check getWebhookInfo
wh = requests.get(f"{BASE}/getWebhookInfo").json()
print(f"\nWebhook: {wh['result']}")
