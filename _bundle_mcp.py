"""
Find MCP server API endpoint and test zorq_sk_ key for generation.
Also look for npm package or GitHub repo for zorq-mcp-server.
"""
import re, requests, json, time

code = open('_bundle_latest.js', encoding='utf-8', errors='replace').read()

# Find full MCP page context
print("=== MCP server full page (2000 chars around ZORQ_TOKEN) ===")
idx = code.find('ZORQ_TOKEN')
print(code[max(0,idx-1000):idx+2000])

# Find API base URL
print("\n=== API endpoint patterns ===")
for pat in [r'api\.zorqai\.com', r'zorqai\.com/api', r'api\.zorq', r'/v1/generate', r'/api/generate']:
    for m in re.finditer(pat, code, re.I):
        ctx = code[max(0,m.start()-200):m.start()+300]
        print(f"  [{pat} @ {m.start()}] ...{ctx}...")

# Look for npm install zorq or github.com/zorq
print("\n=== npm/github references ===")
for pat in [r'npm.*zorq', r'zorq.*npm', r'github\.com.*zorq', r'zorq.*github', r'npx zorq', r'@zorq']:
    for m in re.finditer(pat, code, re.I):
        ctx = code[max(0,m.start()-100):m.start()+300]
        print(f"  [{pat} @ {m.start()}] ...{ctx}...")
