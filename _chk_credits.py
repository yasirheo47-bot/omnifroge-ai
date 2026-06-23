import json, sys
sys.path.insert(0, '.')
from zorq_unlimited import ZorqClient

accounts = json.load(open('zorq_farm_accounts.json'))
total = 0
for acc in accounts:
    try:
        c = ZorqClient(acc['access_token'], acc['refresh_token'])
        credits = c.get_credits()
        total += credits
        print(f"#{acc['idx']}  {acc['email']:<35}  credits={credits}")
    except Exception as e:
        print(f"#{acc['idx']}  {acc['email']:<35}  ERROR: {e}")
print(f"\nTOTAL: {total}")
