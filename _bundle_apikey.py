"""Search bundle for API key usage patterns and Zorq API endpoints"""
import re

code = open('_bundle_latest.js', encoding='utf-8', errors='replace').read()

print("=== zorq_sk references ===")
for m in re.finditer(r'zorq_sk', code, re.I):
    ctx = code[max(0,m.start()-200):m.start()+400]
    print(f"[{m.start()}] ...{ctx}...")
    print()

print("\n=== API key authentication ===")
for pat in ['x-zorq-key', 'x-api-key', 'api[-_]key', 'apiKey', 'api_token', 'bearer.*zorq', 'zorq.*bearer']:
    for m in re.finditer(pat, code, re.I):
        ctx = code[max(0,m.start()-100):m.start()+300]
        print(f"  [{pat} @ {m.start()}] ...{ctx}...")

print("\n=== API endpoint URLs ===")
for pat in [r'api\.zorq', r'zorq.*api', r'/api/v', r'v1/generate', r'v1/image', r'v1/inference']:
    for m in re.finditer(pat, code, re.I):
        ctx = code[max(0,m.start()-100):m.start()+300]
        print(f"  [{pat} @ {m.start()}] ...{ctx}...")

print("\n=== manageAPIKey context ===")
for m in re.finditer(r'manageAPIKey|manage_api_key|apiKeys', code, re.I):
    ctx = code[max(0,m.start()-200):m.start()+500]
    print(f"[{m.start()}] ...{ctx}...")
    print()

print("\n=== Whop webhook processing context ===")
for m in re.finditer(r'whopWebhook|whop_webhook', code, re.I):
    ctx = code[max(0,m.start()-200):m.start()+500]
    print(f"[{m.start()}] ...{ctx}...")
    print()
