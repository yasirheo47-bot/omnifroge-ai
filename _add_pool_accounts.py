"""
_add_pool_accounts.py
Run ONCE to login all new Viewmax accounts and inject them into scenx_state.json.
Safe to run while the bot is stopped. Does NOT touch existing tokens / sessions / keys.
Usage:  python _add_pool_accounts.py
"""

import json, os, re, time
import requests

STATE_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenx_state.json")
VMX_BASE    = "https://www.viewmax.io"
GAP_SECS    = 5   # seconds between each login attempt

# ── Accounts to add ──────────────────────────────────────────────────────────
# (email, password)
ACCOUNTS = [
    # push.tg accounts — all share the same password
    ("o978c04@push.tg",    "Hamza@12@@"),
    ("g0d6d96@push.tg",    "Hamza@12@@"),
    ("b2871b1@push.tg",    "Hamza@12@@"),
    ("s7b8tg7@push.tg",    "Hamza@12@@"),
    ("hd8f0e7@push.tg",    "Hamza@12@@"),
    ("c5d3fef@push.tg",    "Hamza@12@@"),
    # edu-mail accounts — password == email
    ("nxx06@edu-mail.edu.rs",  "nxx06@edu-mail.edu.rs"),
    ("lwt46@edu-mail.edu.pl",  "lwt46@edu-mail.edu.pl"),
    ("sjm96@tempedumail.me",   "sjm96@tempedumail.me"),
]

# ─────────────────────────────────────────────────────────────────────────────

def _esc(s): return s[:40]

def _vmx_login(email: str, password: str):
    """Login to Viewmax and return (cookie_string, None) or (None, error_str)."""
    try:
        s = requests.Session()
        r = s.post(
            f"{VMX_BASE}/api/auth/sign-in/email",
            json={"email": email, "password": password, "callbackURL": "/dashboard"},
            headers={
                "Content-Type": "application/json",
                "Accept":       "application/json, */*",
                "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/124.0.0.0 Safari/537.36",
                "Origin":       VMX_BASE,
                "Referer":      f"{VMX_BASE}/login",
            },
            allow_redirects=True,
            timeout=25,
        )
        # 1. Session cookies (populated after redirect chain)
        for c in s.cookies:
            if "__Secure-better-auth.session_token" in c.name:
                return f"__Secure-better-auth.session_token={c.value}", None
        # 2. Raw Set-Cookie header fallback
        raw_sc = r.headers.get("Set-Cookie", "")
        m = re.search(r"__Secure-better-auth\.session_token=([^;]+)", raw_sc)
        if m:
            return f"__Secure-better-auth.session_token={m.group(1)}", None
        # 3. Surface a useful error message
        if r.status_code not in (200, 302):
            try:
                body = r.json()
                err  = body.get("message") or body.get("error") or str(body)[:200]
            except Exception:
                err = r.text[:200]
            return None, f"HTTP {r.status_code}: {err}"
        return None, "Login succeeded but no session cookie returned"
    except Exception as exc:
        return None, str(exc)


def load_state():
    if not os.path.exists(STATE_FILE):
        print(f"  ⚠  state file not found at {STATE_FILE} — will create fresh")
        return {}
    with open(STATE_FILE, encoding="utf-8-sig") as f:
        return json.load(f)


def save_state(data: dict):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, STATE_FILE)
    print(f"  💾  state saved → {STATE_FILE}")


def main():
    print("\n" + "═" * 56)
    print("  🌐  ScenX — Bulk Pool Account Injector")
    print("═" * 56)
    print(f"  Accounts to process : {len(ACCOUNTS)}")
    print(f"  Gap between logins  : {GAP_SECS}s")
    print("═" * 56 + "\n")

    state = load_state()

    # Load existing extras so we don't double-add
    existing_tokens: list = state.get("extra_pool_tokens", [])
    existing_accs:   list = state.get("vmx_accounts", [])

    existing_tok_set   = set(existing_tokens)
    existing_email_set = {a["email"] for a in existing_accs}

    added    = []
    skipped  = []
    failed   = []

    for i, (email, password) in enumerate(ACCOUNTS):
        print(f"  [{i+1:02d}/{len(ACCOUNTS)}]  {email}")

        if email in existing_email_set:
            print(f"           ⏭  already in vmx_accounts — skipping")
            skipped.append(email)
            if i < len(ACCOUNTS) - 1:
                time.sleep(GAP_SECS)
            continue

        tok, err = _vmx_login(email, password)

        if tok:
            short = f"…{tok[-20:]}"
            print(f"           ✅  login OK  →  {short}")
            # Add token to extra_pool_tokens if not already there
            if tok not in existing_tok_set:
                existing_tokens.append(tok)
                existing_tok_set.add(tok)
            # Add to vmx_accounts (credentials for auto-relogin)
            existing_accs.append({"email": email, "password": password, "token": tok})
            existing_email_set.add(email)
            added.append(email)
        else:
            print(f"           ❌  FAILED  →  {err}")
            failed.append((email, err))

        if i < len(ACCOUNTS) - 1:
            print(f"           ⏳  waiting {GAP_SECS}s...\n")
            time.sleep(GAP_SECS)

    # Merge back into state — preserve everything else untouched
    state["extra_pool_tokens"] = existing_tokens
    state["vmx_accounts"]      = existing_accs
    save_state(state)

    print("\n" + "═" * 56)
    print(f"  ✅  Added   : {len(added)}")
    print(f"  ⏭  Skipped : {len(skipped)}")
    print(f"  ❌  Failed  : {len(failed)}")
    if failed:
        print("\n  Failed accounts:")
        for email, err in failed:
            print(f"    • {email}  →  {err}")
    print("\n  Pool extra_pool_tokens now has:")
    print(f"    {len(existing_tokens)} token(s) stored in state")
    print("\n  ✨  Restart the bot to load all new tokens into rotation.")
    print("═" * 56 + "\n")


if __name__ == "__main__":
    main()
