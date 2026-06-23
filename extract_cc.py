import xml.etree.ElementTree as ET
import base64, gzip, zlib, json, re

TARGET_KEYWORDS = [
    b"character", b"Character", b"consistency", b"Consistency",
    b"subject", b"Subject", b"reference", b"Reference",
    b"asset", b"Asset", b"location", b"Location",
    b"ai-clone", b"charRef", b"char_ref", b"subjectRef",
    b"subject-ref", b"imageRef", b"image-ref",
]

def decode_body(raw):
    if not raw:
        return b""
    try:
        data = base64.b64decode(raw)
    except Exception:
        return raw.encode() if isinstance(raw, str) else raw
    try:
        return gzip.decompress(data)
    except Exception:
        pass
    try:
        return zlib.decompress(data)
    except Exception:
        pass
    return data

results = []
count = 0
path = r"CharacterConsistencyAndObjectA d lLocation"

context = ET.iterparse(path, events=("end",))
for event, elem in context:
    if elem.tag != "item":
        continue
    count += 1
    url     = (elem.findtext("url") or "").strip()
    method  = (elem.findtext("method") or "").strip()
    req_raw = elem.findtext("request") or ""
    res_raw = elem.findtext("response") or ""

    req_body = decode_body(req_raw)
    res_body = decode_body(res_raw)

    combined = req_body + res_body
    if any(kw in combined for kw in TARGET_KEYWORDS):
        if "/api/" in url or "viewmax" in url:
            results.append({
                "url": url,
                "method": method,
                "request": req_body[:5000].decode("utf-8", errors="replace"),
                "response": res_body[:8000].decode("utf-8", errors="replace"),
            })
    elem.clear()
    if count % 50000 == 0:
        print(f"  scanned {count} items, {len(results)} matches...", flush=True)

print(f"\nDone. Total items: {count}, matched: {len(results)}")

with open("cc_extracted.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("Written to cc_extracted.json")
