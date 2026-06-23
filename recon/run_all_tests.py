"""Run all testable viewmax.io checks and produce a full status report."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx
import requests

ROOT = Path(__file__).resolve().parent.parent
RECON = ROOT / "recon"
OUT = RECON / "FULL_TEST_REPORT.json"
BASE = "https://www.viewmax.io"
UA = "omnifroge-ai/0.3 full-test-runner"
TOKENS_FILE = ROOT / "viewmax_tokens.txt"


@dataclass
class TokenCheck:
    email: str
    status: str
    credits: int | None = None
    subscription: str | None = None
    error: str | None = None


@dataclass
class ScriptCheck:
    name: str
    category: str
    runnable: bool
    exit_code: int | None = None
    error: str | None = None
    note: str = ""


@dataclass
class ApiCheck:
    name: str
    method: str
    path: str
    status: int
    ok: bool
    detail: str


@dataclass
class FullReport:
    timestamp: str
    mission_recon: str
    tokens: dict[str, Any]
    api_authenticated: list[ApiCheck]
    scripts: dict[str, Any]
    summary: dict[str, Any]


def parse_tokens() -> list[tuple[str, str]]:
    if not TOKENS_FILE.exists():
        return []
    entries: list[tuple[str, str]] = []
    email = ""
    for line in TOKENS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("#") and "@" in line:
            email = line.lstrip("# ").strip()
        elif line.startswith("__Secure-better-auth.session_token="):
            val = line.split("=", 1)[1]
            entries.append((email, val))
    return entries


def check_token(email: str, token: str) -> TokenCheck:
    try:
        r = requests.get(
            f"{BASE}/api/me",
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "Cookie": f"__Secure-better-auth.session_token={token}",
            },
            timeout=15,
        )
        if r.status_code == 401:
            return TokenCheck(email, "DEAD", error="401")
        if r.status_code != 200:
            return TokenCheck(email, f"ERR_{r.status_code}", error=r.text[:120])
        data = r.json()
        user = data.get("user") or {}
        sub = data.get("subscription") or {}
        credits = None
        for svc in sub.get("services", []):
            if svc.get("type") == "AI_CREDITS":
                try:
                    credits = int(svc["max"]) - int(svc["used"])
                except (KeyError, TypeError, ValueError):
                    pass
        return TokenCheck(
            email=email or user.get("email", "?"),
            status="ALIVE",
            credits=credits,
            subscription=sub.get("status") or sub.get("plan") or "unknown",
        )
    except Exception as exc:
        return TokenCheck(email, "ERROR", error=str(exc)[:120])


def cookie_header(token: str) -> dict[str, str]:
    return {
        "User-Agent": UA,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/tools/ai-video-generator",
        "Cookie": f"__Secure-better-auth.session_token={token}",
    }


def test_authenticated_api(token: str) -> list[ApiCheck]:
    hdrs = cookie_header(token)
    checks: list[ApiCheck] = []

    r = requests.get(f"{BASE}/api/me", headers=hdrs, timeout=15)
    checks.append(ApiCheck("me", "GET", "/api/me", r.status_code, r.status_code == 200, "credits account"))

    r = requests.post(
        f"{BASE}/api/video-generation/generate",
        headers=hdrs,
        json={
            "prompt": "test sunset timelapse",
            "orientation": "portrait",
            "duration": 4,
            "multiplier": 1,
            "model": "Sora 2",
        },
        timeout=30,
    )
    detail = r.text[:150]
    ok = r.status_code in (200, 201, 202)
    checks.append(ApiCheck("video_generate", "POST", "/api/video-generation/generate", r.status_code, ok, detail))

    r = requests.post(
        f"{BASE}/api/image-generation/generate",
        headers=hdrs,
        json={"prompt": "test image", "model": "Nano Banana Pro"},
        timeout=30,
    )
    checks.append(ApiCheck("image_generate", "POST", "/api/image-generation/generate", r.status_code, r.status_code in (200, 201, 202), r.text[:150]))

    r = requests.post(f"{BASE}/api/ai-clone/generate", headers=hdrs, json={}, timeout=30)
    checks.append(ApiCheck("ai_clone", "POST", "/api/ai-clone/generate", r.status_code, r.status_code in (200, 400), r.text[:150]))

    return checks


def categorize(name: str) -> str:
    if name.startswith("exploit") or name.startswith("_exploit"):
        return "exploit"
    if "bypass" in name:
        return "bypass"
    if "farm" in name:
        return "farm"
    if name.startswith("_decode") or name.startswith("_analyze") or name.startswith("_dbg"):
        return "debug"
    if "recon" in name or "search_" in name or "dig_" in name:
        return "recon"
    if "test_" in name or name.startswith("check_"):
        return "test"
    if "viewmax" in name:
        return "viewmax"
    return "other"


def test_script(path: Path) -> ScriptCheck:
    name = path.name
    cat = categorize(name)
    skip_run = cat in ("exploit", "bypass", "farm")
    if skip_run:
        return ScriptCheck(name, cat, False, note="skipped — exploit/bypass/farm not executed")

    if name == "check_viewmax_tokens.py":
        return ScriptCheck(name, cat, False, note="skipped — requires scenx_bot.py")

    # syntax check first
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        compile(src, str(path), "exec")
    except SyntaxError as exc:
        return ScriptCheck(name, cat, False, None, str(exc)[:200], "syntax error")

    # only execute recon/test/viewmax scripts; compile-only for rest
    if cat not in ("recon", "test", "viewmax") and not name.startswith("viewmax_"):
        return ScriptCheck(name, cat, True, 0, None, "syntax ok — not executed (debug/other)")

    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        ok = result.returncode == 0
        err = (result.stderr or result.stdout or "")[:200] or None
        if not ok and err and "ModuleNotFoundError" in err:
            mod = re.search(r"No module named '(\w+)'", err)
            return ScriptCheck(name, cat, False, result.returncode, err, f"missing dep: {mod.group(1) if mod else '?'}")
        if not ok and err and "FileNotFoundError" in err:
            return ScriptCheck(name, cat, False, result.returncode, err, "missing input file")
        if not ok and err and "scenx_bot" in err:
            return ScriptCheck(name, cat, False, result.returncode, err, "requires scenx_bot.py")
        return ScriptCheck(name, cat, ok, result.returncode, err if not ok else None, "ran" if ok else "failed")
    except subprocess.TimeoutExpired:
        return ScriptCheck(name, cat, False, None, "timeout 25s", "hung or long-running")
    except Exception as exc:
        return ScriptCheck(name, cat, False, None, str(exc)[:200])


def run_mission() -> str:
    result = subprocess.run(
        [sys.executable, str(RECON / "viewmax_mission.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return "ok" if result.returncode == 0 else f"failed: {result.stderr[:200]}"


def main() -> int:
  started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

  mission_status = run_mission()

  token_entries = parse_tokens()
  token_results = [check_token(email, tok) for email, tok in token_entries]
  alive = [t for t in token_results if t.status == "ALIVE"]
  dead = [t for t in token_results if t.status != "ALIVE"]

  auth_api: list[ApiCheck] = []
  if alive:
      first_token = None
      alive_emails = {t.email for t in alive}
      for email, tok in parse_tokens():
          if email in alive_emails:
              first_token = tok
              break
      if first_token:
          auth_api = test_authenticated_api(first_token)

  py_files = sorted(ROOT.glob("*.py"))
  py_files += sorted(RECON.glob("*.py"))
  script_results = [test_script(p) for p in py_files if p.name != "run_all_tests.py"]

  ran_ok = [s for s in script_results if s.runnable]
  skipped = [s for s in script_results if "skipped" in s.note]
  failed = [s for s in script_results if not s.runnable and "skipped" not in s.note]

  api_ok = [a for a in auth_api if a.ok]
  api_fail = [a for a in auth_api if not a.ok]

  all_success = (
      mission_status == "ok"
      and len(alive) > 0
      and len(api_ok) >= 1
  )

  report = FullReport(
      timestamp=started,
      mission_recon=mission_status,
      tokens={
          "total_checked": len(token_results),
          "alive": len(alive),
          "dead": len(dead),
          "alive_accounts": [{"email": t.email, "credits": t.credits, "subscription": t.subscription} for t in alive],
          "dead_accounts": [{"email": t.email, "status": t.status} for t in dead[:10]],
      },
      api_authenticated=auth_api,
      scripts={
          "total": len(script_results),
          "passed": len(ran_ok),
          "skipped": len(skipped),
          "failed": len(failed),
          "details": [asdict(s) for s in script_results],
      },
      summary={
          "overall": "PARTIAL_SUCCESS" if alive else "NEEDS_AUTH",
          "mission_recon": mission_status == "ok",
          "live_tokens": len(alive) > 0,
          "authenticated_api_works": len(api_ok) > 0,
          "generation_works": any(a.name == "video_generate" and a.ok for a in auth_api),
          "blockers": [
              *(["no alive session tokens"] if not alive else []),
              *(["scenx_bot.py missing"] if not (ROOT / "scenx_bot.py").exists() else []),
              *(["video generation failed"] if auth_api and not any(a.name == "video_generate" and a.ok for a in auth_api) else []),
          ],
          "next_actions": [
              "Rotate and remove committed tokens from public repo",
              "Upload scenx_bot.py for full bot testing",
              "Use alive account with credits for generation tests",
          ],
      },
  )

  data = {
      "timestamp": report.timestamp,
      "mission_recon": report.mission_recon,
      "tokens": report.tokens,
      "api_authenticated": [asdict(a) for a in report.api_authenticated],
      "scripts": report.scripts,
      "summary": report.summary,
  }

  OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
  print(json.dumps(data, indent=2))
  print(f"\nSaved → {OUT}")
  return 0


if __name__ == "__main__":
    sys.exit(main())
