import base64, re, json

with open(r'c:\Users\ADMIN\Documents\rork.ak\sora2cons', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all generate POST request bodies
pattern = r'<method><!\[CDATA\[POST\]\]></method>.*?/generate.*?<request base64="true"><!\[CDATA\[(.*?)\]\]></request>'
matches = re.findall(pattern, content, re.DOTALL)
print(f'Found {len(matches)} generate POSTs\n')
for i, m in enumerate(matches):
    try:
        b64 = m.replace('\n','').replace('\r','').strip()
        decoded = base64.b64decode(b64).decode('utf-8', errors='replace')
        if '\r\n\r\n' in decoded:
            body = decoded.split('\r\n\r\n', 1)[1]
        else:
            body = decoded[-600:]
        print(f'--- Request {i+1} ---')
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, indent=2))
        except:
            print(body[:500])
        print()
    except Exception as e:
        print(f'--- Request {i+1} DECODE FAIL: {e} ---\n')
