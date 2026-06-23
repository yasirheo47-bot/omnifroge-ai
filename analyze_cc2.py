import json, re

items = json.load(open('cc_extracted.json', encoding='utf-8'))

# Find POST /references body
for it in items:
    if it['method'] == 'POST' and '/references' in it['url']:
        print("=== POST /references REQUEST BODY ===")
        # Extract just the JSON body from raw HTTP
        req = it['request']
        # Find JSON part (after double newline)
        parts = req.split('\r\n\r\n', 1)
        if len(parts) > 1:
            print("BODY:", parts[1][:3000])
        else:
            parts = req.split('\n\n', 1)
            if len(parts) > 1:
                print("BODY:", parts[1][:3000])
        print("=== RESPONSE ===")
        resp = it['response']
        parts = resp.split('\r\n\r\n', 1)
        if len(parts) > 1:
            print("BODY:", parts[1][:3000])
        else:
            parts = resp.split('\n\n', 1)
            if len(parts) > 1:
                print("BODY:", parts[1][:3000])
        print()

# Find generate calls with references
print("\n\n=== GENERATE CALLS WITH REFERENCES ===")
for it in items:
    if '/generate' in it['url']:
        req = it['request']
        parts = req.split('\r\n\r\n', 1)
        body = parts[1] if len(parts) > 1 else req.split('\n\n',1)[-1]
        if 'reference' in body.lower() or 'klingElement' in body:
            print("REQUEST BODY:")
            print(body[:3000])
            resp = it['response']
            parts = resp.split('\r\n\r\n', 1)
            rbody = parts[1] if len(parts) > 1 else resp.split('\n\n',1)[-1]
            print("RESPONSE BODY:")
            print(rbody[:2000])
            print("---")
