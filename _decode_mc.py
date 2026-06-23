import base64

with open(r'c:\Users\ADMIN\Documents\rork.ak\motioncontrol', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find ALL ai-clone/generate calls
search = 'ai-clone/generate'
pos = 0
call_num = 0
while True:
    idx = content.find(search, pos)
    if idx < 0:
        break
    call_num += 1
    pos = idx + 1

    start = content.find('<request base64="true"><![CDATA[', idx)
    if start < 0:
        continue
    end = content.find(']]></request>', start)
    b64 = content[start+32:end].replace('\n','').replace('\r','').replace(' ','')
    try:
        decoded = base64.b64decode(b64 + '==').decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Call {call_num}: decode error {e}")
        continue

    # find JSON body after headers
    body_start = decoded.find('\r\n\r\n')
    if body_start < 0:
        body_start = decoded.find('\n\n')
    body = decoded[body_start:].strip() if body_start >= 0 else decoded

    print(f"\n{'='*60}")
    print(f"CALL #{call_num} to /api/ai-clone/generate")
    print(f"{'='*60}")
    print(body[:3000])

    # Also find the response
    resp_start = content.find('<response base64="true"><![CDATA[', idx)
    if resp_start > 0 and resp_start < content.find('</item>', idx):
        resp_end = content.find(']]></response>', resp_start)
        rb64 = content[resp_start+33:resp_end].replace('\n','').replace('\r','').replace(' ','')
        try:
            rdec = base64.b64decode(rb64 + '==').decode('utf-8', errors='replace')
            rbody_start = rdec.find('\r\n\r\n')
            if rbody_start < 0:
                rbody_start = rdec.find('\n\n')
            rbody = rdec[rbody_start:].strip() if rbody_start >= 0 else rdec
            print(f"\nRESPONSE:")
            print(rbody[:1000])
        except Exception:
            pass
