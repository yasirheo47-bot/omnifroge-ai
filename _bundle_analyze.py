"""Bundle analysis: identityImageGeneration and referral reward"""
import re

code = open('_bundle_latest.js', encoding='utf-8', errors='replace').read()

print("=== identityImageGeneration full context ===")
idx = 0
while True:
    idx = code.find('identityImageGeneration', idx)
    if idx == -1: break
    print(f"\n--- @ {idx} ---")
    print(code[max(0, idx-200):idx+500])
    idx += 1

print("\n\n=== setReferredBy full context ===")
idx = 0
cnt = 0
while True:
    idx = code.find('setReferredBy', idx)
    if idx == -1: break
    cnt += 1
    print(f"\n--- @ {idx} ---")
    print(code[max(0, idx-300):idx+600])
    idx += 1
print(f"Total setReferredBy occurrences: {cnt}")

print("\n\n=== referral_window / referral_code / referred_by credit logic ===")
for pat in ['referral_window', 'referral_credits', 'referral_bonus', 
            'referee', 'referred_by.*credit', 'setReferredBy.*welcome',
            'credit.*referral', 'bonus.*referral', 'welcome.*credits.*refer',
            'credits_on_referral', 'signup_credits', 'welcome_credits']:
    for m in re.finditer(pat, code, re.I):
        ctx = code[max(0, m.start()-200):m.start()+400]
        print(f"\n[{pat} @ {m.start()}]")
        print(ctx)
        break  # just first match per pattern

print("\n\n=== generatePrompts context ===")
idx = 0
while True:
    idx = code.find('generatePrompts', idx)
    if idx == -1: break
    print(f"\n--- @ {idx} ---")
    print(code[max(0, idx-100):idx+300])
    idx += 1
