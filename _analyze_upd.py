"""
_analyze_upd.py — Deep analysis of the 'upd' burp capture file.
Extracts: new templates, seedance limits, video/audio/image upload endpoints, payloads.
Run: python _analyze_upd.py
"""
import re, sys, json, os

BURP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upd")

print(f"[*] Reading {BURP_FILE} ...", flush=True)
with open(BURP_FILE, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8", "replace")
print(f"[*] Loaded {len(text):,} chars\n", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1. ALL /api/ endpoints
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("1. API ENDPOINTS")
print("=" * 70)
endpoints = {}
for m in re.finditer(r'(GET|POST|PUT|PATCH|DELETE) (/api/[^\s"\'<>]{2,120})', text):
    method, path = m.group(1), m.group(2).split("?")[0].rstrip("/")
    key = f"{method} {path}"
    endpoints[key] = endpoints.get(key, 0) + 1
for k, v in sorted(endpoints.items()):
    print(f"  {v:4d}x  {k}")
print(flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. TEMPLATES — every unique templateId / templateSlug / template value
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("2. TEMPLATES")
print("=" * 70)
tmpl_hits: dict[str, str] = {}

patterns = [
    r'"templateId"\s*:\s*"([^"]{3,80})"',
    r'"templateSlug"\s*:\s*"([^"]{3,80})"',
    r'"templateName"\s*:\s*"([^"]{3,80})"',
    r'"template"\s*:\s*"([^"]{3,80})"',
    r'"template_id"\s*:\s*"([^"]{3,80})"',
    r'"template_slug"\s*:\s*"([^"]{3,80})"',
    r'/templates?/([a-zA-Z0-9_\-]{3,60})',
    r'templateId=([a-zA-Z0-9_\-]{3,60})',
]
for pat in patterns:
    for m in re.finditer(pat, text, re.IGNORECASE):
        val = m.group(1)
        if val not in tmpl_hits:
            ctx = text[max(0, m.start()-100):m.end()+100].replace("\n", " ")
            tmpl_hits[val] = ctx

for val, ctx in sorted(tmpl_hits.items()):
    print(f"  {val!r}")
    print(f"    CTX: {ctx[:160]}")
print(f"\n  TOTAL unique templates: {len(tmpl_hits)}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. SEEDANCE — everything
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("3. SEEDANCE")
print("=" * 70)
seedance_hits = []
for m in re.finditer(r'.{0,300}seedance.{0,300}', text, re.IGNORECASE | re.DOTALL):
    chunk = m.group(0).replace("\n", " ").replace("\r", "")
    if chunk not in seedance_hits:
        seedance_hits.append(chunk)
        print(f"  {chunk[:300]}")
        print("  ---")
print(f"\n  TOTAL seedance hits: {len(seedance_hits)}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. VIDEO upload / generation endpoints + payloads
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("4. VIDEO UPLOAD / GENERATION PAYLOADS")
print("=" * 70)
video_pats = [
    r'video[_\-]?(?:upload|generate|generation|reference|ref)[^\n]{0,400}',
    r'multipart/form-data[^\n]{0,200}',
    r'"videos?"\s*:\s*\[[^\]]{0,500}\]',
    r'"videoUrl[s]?"\s*:\s*[^\n]{0,200}',
    r'"maxVideos?(?:ecs|Duration|Length|Seconds)?"\s*:\s*[^\n]{0,100}',
    r'"videoDuration"\s*:\s*[^\n]{0,100}',
    r'"maxDuration"\s*:\s*[^\n]{0,100}',
]
seen_v = set()
for pat in video_pats:
    for m in re.finditer(pat, text, re.IGNORECASE):
        chunk = m.group(0)[:300].replace("\n", " ")
        if chunk not in seen_v:
            seen_v.add(chunk)
            print(f"  {chunk}")
            print("  ---")
print(flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 5. AUDIO upload / limits
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("5. AUDIO UPLOAD / LIMITS")
print("=" * 70)
audio_pats = [
    r'"audio[s]?"\s*:\s*\[[^\]]{0,500}\]',
    r'"audioUrl[s]?"\s*:\s*[^\n]{0,200}',
    r'"maxAudio[^\n]{0,100}',
    r'audio[_\-]?(?:upload|reference|ref|limit)[^\n]{0,300}',
]
seen_a = set()
for pat in audio_pats:
    for m in re.finditer(pat, text, re.IGNORECASE):
        chunk = m.group(0)[:300].replace("\n", " ")
        if chunk not in seen_a:
            seen_a.add(chunk)
            print(f"  {chunk}")
            print("  ---")
print(flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 6. IMAGE upload limits
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("6. IMAGE UPLOAD / LIMITS")
print("=" * 70)
img_pats = [
    r'"image[s]?"\s*:\s*\[[^\]]{0,500}\]',
    r'"maxImages?"\s*:\s*[^\n]{0,100}',
    r'"imageUrl[s]?"\s*:\s*[^\n]{0,200}',
    r'image[_\-]?(?:upload|reference|ref|limit)[^\n]{0,300}',
]
seen_i = set()
for pat in img_pats:
    for m in re.finditer(pat, text, re.IGNORECASE):
        chunk = m.group(0)[:300].replace("\n", " ")
        if chunk not in seen_i:
            seen_i.add(chunk)
            print(f"  {chunk}")
            print("  ---")
print(flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 7. FULL JSON BODIES for POST /api/video-generation or seedance
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("7. FULL POST BODIES (video-generation / seedance)")
print("=" * 70)
body_pats = [
    r'POST /api/video-generation[^\n]{0,200}',
    r'POST /api/ai-clone[^\n]{0,200}',
    r'POST /api/seedance[^\n]{0,200}',
]
seen_b = set()
for pat in body_pats:
    for m in re.finditer(pat, text, re.IGNORECASE):
        # grab up to 1500 chars after the match (likely includes body)
        chunk = text[m.start():m.start()+1500].replace("\n", " | ")
        if m.group(0) not in seen_b:
            seen_b.add(m.group(0))
            print(f"  {chunk[:600]}")
            print("  ===")
print(flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# 8. Numeric limits (max, min, duration, seconds)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("8. NUMERIC LIMITS")
print("=" * 70)
limit_pats = [
    r'"max(?:Images?|Videos?|Audios?|Duration|Seconds?|Length|Files?|Count)"\s*:\s*\d+',
    r'"min(?:Duration|Seconds?|Length)"\s*:\s*\d+',
    r'"totalDuration"\s*:\s*\d+',
    r'"durationLimit"\s*:\s*\d+',
    r'"videoDuration"\s*:\s*\d+',
    r'"maxVideoSeconds"\s*:\s*\d+',
]
seen_l = set()
for pat in limit_pats:
    for m in re.finditer(pat, text, re.IGNORECASE):
        v = m.group(0)
        if v not in seen_l:
            seen_l.add(v)
            ctx = text[max(0,m.start()-80):m.end()+80].replace("\n", " ")
            print(f"  {v}")
            print(f"    CTX: {ctx[:160]}")

print("\n[*] Done.", flush=True)
