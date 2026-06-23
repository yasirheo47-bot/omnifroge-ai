"""
test_refund.py — standalone credit-refund verification
Logs in fresh, fires 1 gen (5s portrait), polls to completion, fires webhook refund, prints before/after credits.
"""

import time
import json
import requests

BASE   = "https://www.viewmax.io"
EMAIL  = "quicken-jolt-crave@duck.com"
PASSW  = "quicken-jolt-crave@duck.com"

# ── helpers ──────────────────────────────────────────────────────────────────

def _hdrs(token=None):
    h = {
        "Content-Type": "application/json",
        "Accept":       "application/json",
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin":       "https://www.viewmax.io",
        "Referer":      "https://www.viewmax.io/",
    }
    if token:
        h["Cookie"] = token
    return h


def login():
    r = requests.post(
        f"{BASE}/api/auth/sign-in/email",
        headers=_hdrs(),
        json={"email": EMAIL, "password": PASSW, "rememberMe": True},
        timeout=15,
    )
    print(f"[login] status={r.status_code}")
    cookie = r.cookies.get("__Secure-better-auth.session_token")
    if not cookie:
        # try set-cookie header manually
        for h, v in r.headers.items():
            if "set-cookie" in h.lower() and "session_token" in v:
                cookie = v.split("=", 1)[1].split(";")[0]
                break
    if cookie:
        token = f"__Secure-better-auth.session_token={cookie}"
        print(f"[login] ✅ got token: {token[:60]}...")
        return token
    print(f"[login] ❌ no cookie found. resp: {r.text[:300]}")
    return None


def get_me(token):
    """GET /api/me — returns full subscription data including AI_CREDITS."""
    r = requests.get(f"{BASE}/api/me", headers=_hdrs(token), timeout=10)
    try:
        return r.json()
    except Exception:
        return {}


def get_credits(data):
    """Extract remaining AI_CREDITS from /api/me response (max - used)."""
    try:
        services = (data.get("subscription") or {}).get("services", [])
        for svc in services:
            if svc.get("type") == "AI_CREDITS":
                remaining = int(svc["max"]) - int(svc["used"])
                return remaining, f"AI_CREDITS({svc['max']}-{svc['used']})"
    except Exception:
        pass
    return -1, "unknown"


def fire_gen(token):
    payload = {
        "model":       "Kling 3.0 Pro",
        "prompt":      "a calm ocean wave",
        "duration":    5,
        "orientation": "portrait",
        "multiplier":  1,
        "audio":       True,
    }
    r = requests.post(
        f"{BASE}/api/video-generation/generate",
        headers=_hdrs(token),
        json=payload,
        timeout=20,
    )
    print(f"[gen] status={r.status_code}  body={r.text[:300]}")
    try:
        d = r.json()
        ids = d.get("generationIds", [])
        gen_id = ids[0] if ids else (d.get("id") or d.get("generationId"))
        return gen_id
    except Exception:
        return None


def poll_until_done(gen_id, token, timeout=300, interval=8):
    print(f"[poll] polling gen_id={gen_id}")
    deadline = time.time() + timeout
    elapsed  = 0
    while time.time() < deadline:
        time.sleep(interval)
        elapsed += interval
        try:
            r = requests.post(
                f"{BASE}/api/video-generation/check-sora-status",
                headers=_hdrs(token),
                json={"generationId": gen_id},
                timeout=15,
            )
            gen    = r.json().get("generation", {})
            status = gen.get("status", "?")
            prog   = gen.get("progress", 0)
            print(f"[poll] t={elapsed}s  status={status}  progress={prog}%")
            if status == "succeeded":
                url = gen.get("videoUrl", "")
                print(f"[poll] ✅ done  videoUrl={url[:80]}")
                return url
            if status == "failed":
                print(f"[poll] ❌ failed: {gen.get('error', '')}")
                return None
        except Exception as e:
            print(f"[poll] error: {e}")
    print("[poll] ❌ timed out")
    return None


def get_sora_task_id(gen_id, token):
    for attempt in range(6):
        try:
            r = requests.get(
                f"{BASE}/api/video-generation/status",
                headers=_hdrs(token),
                params={"ids": gen_id},
                timeout=10,
            )
            gens = r.json().get("generations", [])
            for g in gens:
                tid = g.get("soraTaskId")
                if tid:
                    print(f"[task_id] ✅ soraTaskId={tid}")
                    return tid
            print(f"[task_id] attempt {attempt+1}: not found yet  resp={r.text[:120]}")
        except Exception as e:
            print(f"[task_id] error: {e}")
        time.sleep(3)
    return None


def fire_webhook_refund(sora_task_id):
    r = requests.post(
        f"{BASE}/api/video-generation/webhook",
        headers={
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Origin":       "https://www.viewmax.io",
            "Referer":      "https://www.viewmax.io/",
        },
        json={"id": sora_task_id, "status": "failed"},
        timeout=15,
    )
    print(f"[webhook] status={r.status_code}  body={r.text[:200]}")
    try:
        ok = r.json().get("success", False)
        return ok
    except Exception:
        return False


# ── main flow ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(f"  Credit Refund Test — {EMAIL}")
    print("=" * 60)

    # 1. login
    token = login()
    if not token:
        return

    # 2. check credits before
    print("\n--- BEFORE gen ---")
    before_data = get_me(token)
    credits_before, field = get_credits(before_data)
    print(f"[credits] field='{field}'  before={credits_before}")

    # 3. fire generation
    print("\n--- firing generation ---")
    gen_id = fire_gen(token)
    if not gen_id:
        print("❌ failed to get gen_id, aborting")
        return
    print(f"[gen] gen_id={gen_id}")

    # quick credits snapshot right after firing
    mid_data = get_me(token)
    credits_mid, _ = get_credits(mid_data)
    print(f"[credits] after fire (before refund): {credits_mid}")

    # 4. poll to completion
    print("\n--- polling ---")
    video_url = poll_until_done(gen_id, token)
    if not video_url:
        print("❌ video didn't complete — still trying refund anyway")

    # 5. get soraTaskId
    print("\n--- fetching soraTaskId ---")
    sora_task_id = get_sora_task_id(gen_id, token)
    if not sora_task_id:
        print("❌ couldn't get soraTaskId — can't refund")
        return

    # 6. fire refund webhook
    print("\n--- firing refund webhook ---")
    ok = fire_webhook_refund(sora_task_id)
    print(f"[webhook] success={ok}")

    # 7. credits after
    time.sleep(2)
    print("\n--- AFTER refund ---")
    after_data = get_me(token)
    credits_after, _ = get_credits(after_data)

    # 8. verdict
    print("\n" + "=" * 60)
    print(f"  RESULT:")
    print(f"    credits before gen : {credits_before}")
    print(f"    credits after fire : {credits_mid}")
    print(f"    credits after refund: {credits_after}")
    diff = credits_after - credits_mid if credits_mid >= 0 and credits_after >= 0 else "?"
    print(f"    delta (refunded)   : {diff}")
    print(f"    video URL          : {(video_url or '')[:80]}")
    print("=" * 60)


if __name__ == "__main__":
    main()
