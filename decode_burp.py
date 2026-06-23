import base64, re, json

with open(r'c:\Users\ADMIN\Documents\rork.ak\newImagetoimage', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find image-generation/generate request bodies by scanning line by line
# Each "request base64" tag after a line containing image-generation/generate
found_gen = False
count = 0
for i, line in enumerate(lines):
    if 'image-generation/generate' in line and '<path>' in line:
        found_gen = True
    if found_gen and '<request base64="true">' in line:
        found_gen = False
        count += 1
        m = re.search(r'CDATA\[(.+?)\]\]', line)
        if not m:
            print(f"Call {count}: no CDATA on single line, skipping")
            continue
        try:
            raw = base64.b64decode(m.group(1)).decode('utf-8', errors='replace')
            body_start = raw.find('\r\n\r\n')
            body = raw[body_start+4:] if body_start != -1 else raw
            try:
                parsed = json.loads(body)
                # Truncate any base64 image data for readability
                def truncate_data(obj, max_len=80):
                    if isinstance(obj, dict):
                        return {k: truncate_data(v, max_len) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [truncate_data(i, max_len) for i in obj]
                    if isinstance(obj, str) and len(obj) > max_len:
                        return obj[:max_len] + f'...[{len(obj)} chars]'
                    return obj
                print(f"=== Call {count} (line {i+1}) ===")
                print(json.dumps(truncate_data(parsed), indent=2))
            except Exception:
                print(f"=== Call {count} (line {i+1}) - raw ===")
                print(body[:500])
        except Exception as e:
            print(f"Call {count} decode error: {e}")

