import base64, re, sys

src = sys.argv[1] if len(sys.argv) > 1 else 'image to vid'
data = open(src, encoding='utf-8').read()

# Get all URLs from XML
urls = re.findall(r'<url><!\[CDATA\[(.*?)\]\]>', data)
statuses = re.findall(r'<status>(\d+)</status>', data)
req_blobs = re.findall(r'<request base64="true"><!\[CDATA\[(.*?)\]\]>', data)
resp_blobs = re.findall(r'<response base64="true"><!\[CDATA\[(.*?)\]\]>', data)

out_file = sys.argv[2] if len(sys.argv) > 2 else '_xml_analysis.txt'
out = open(out_file, 'w', encoding='utf-8')

for i, url in enumerate(urls):
    req = base64.b64decode(req_blobs[i]).decode('utf-8', errors='replace') if i < len(req_blobs) else ''
    resp = base64.b64decode(resp_blobs[i]).decode('utf-8', errors='replace') if i < len(resp_blobs) else ''
    status = statuses[i] if i < len(statuses) else '?'

    out.write(f"\n{'='*60}\n")
    out.write(f"[{i}] STATUS:{status}  URL: {url}\n")
    body_start = req.find('\r\n\r\n')
    req_body = req[body_start+4:] if body_start != -1 else req[-300:]
    out.write(f"REQ BODY: {req_body[:400]}\n")
    resp_start = resp.find('\r\n\r\n')
    resp_body = resp[resp_start+4:resp_start+800] if resp_start != -1 else resp[-400:]
    out.write(f"RESP BODY: {resp_body}\n")

out.close()
print(f"Done. {len(urls)} items written to {out_file}")

