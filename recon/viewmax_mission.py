"""Viewmax.io mission recon — map live API surface and auth requirements."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx

BASE = "https://www.viewmax.io"
UA = "omnifroge-ai/0.2 mission-recon"
OUT = Path(__file__).resolve().parent / "MISSION_REPORT.json"

# Endpoints discovered across legacy 16may tooling
ENDPOINTS: list[tuple[str, str]] = [
    ("GET", "/api/me"),
    ("POST", "/api/auth/sign-in/email"),
    ("GET", "/api/auth/get-session"),
    ("POST", "/api/video-generation/generate"),
    ("GET", "/api/video-generation/status"),
    ("GET", "/api/video-generation/check-sora-status"),
    ("POST", "/api/video-generation/webhook"),
    ("POST", "/api/video-generation/cancel"),
    ("GET", "/api/video-generation"),
    ("POST", "/api/image-generation/generate"),
    ("POST", "/api/image-generation/webhook"),
    ("POST", "/api/ai-clone/generate"),
    ("POST", "/api/stripe/ai-credits-checkout"),
    ("POST", "/api/account/subscription/upgrade"),
    ("POST", "/api/account/subscription/cancel"),
    ("POST", "/api/account/subscription/pause"),
    ("POST", "/api/account/subscription/reactivate"),
    ("POST", "/api/account/subscription/resume"),
    ("GET", "/api/admin/users"),
    ("GET", "/api/admin/bonus-campaigns"),
    ("GET", "/api/admin/permissions"),
]

PUBLIC_PAGES = [
    "/",
    "/home",
    "/create",
    "/pricing",
    "/tools/ai-video-generator",
    "/tools/ai-voiceover",
    "/tools/script-writer",
    "/tools/caption-remover",
]


@dataclass
class ProbeResult:
    method: str
    path: str
    status: int
    auth_required: bool
    exists: bool
    content_type: str | None
    sample: str | None
    notes: str = ""


@dataclass
class MissionReport:
    target: str
    tech: dict[str, Any]
    public_pages: list[ProbeResult]
    api_endpoints: list[ProbeResult]
    working_unauthenticated: list[str]
    requires_auth: list[str]
    not_found: list[str]
    mission_status: dict[str, Any]


def classify(status: int, body: str) -> tuple[bool, bool, str]:
  """Return (exists, auth_required, note)."""
  if status == 404:
      return False, False, "not found"
  if status in (401, 403):
      return True, True, "auth required"
  if status == 405:
      return True, False, "exists, wrong method"
  if status == 400:
      return True, False, "exists, needs valid body"
  if status == 200:
      if "login" in body.lower() or "<!doctype html" in body.lower()[:200]:
          return True, True, "html redirect/login page"
      return True, False, "accessible"
  if status in (301, 302, 307, 308):
      return True, False, "redirect"
  if status >= 500:
      return True, False, f"server error {status}"
  return True, status not in (200,), f"status {status}"


def probe(client: httpx.Client, method: str, path: str) -> ProbeResult:
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = client.get(url)
        else:
            r = client.post(url, json={})
    except httpx.HTTPError as exc:
        return ProbeResult(method, path, 0, True, False, None, None, str(exc))

    body = r.text[:500]
    exists, auth_required, note = classify(r.status_code, body)
    return ProbeResult(
        method=method,
        path=path,
        status=r.status_code,
        auth_required=auth_required,
        exists=exists,
        content_type=r.headers.get("content-type"),
        sample=body[:200] if r.headers.get("content-type", "").startswith("application/json") else None,
        notes=note,
    )


def detect_tech(client: httpx.Client) -> dict[str, Any]:
    r = client.get(BASE)
    html = r.text
    return {
        "server": r.headers.get("server"),
        "framework": "Next.js" if "/_next/" in html else None,
        "auth": "better-auth",
        "session_cookies": [
            "__Secure-better-auth.session_token",
            "__Secure-better-auth.session_data",
            "vm_vid",
        ],
        "cdn": sorted(set(re.findall(r"https://([a-z0-9.-]*viewmax\.io)", html))),
    }


def run_mission() -> MissionReport:
    with httpx.Client(
        timeout=20,
        headers={"User-Agent": UA, "Accept": "*/*"},
        follow_redirects=True,
    ) as client:
        tech = detect_tech(client)
        public = [probe(client, "GET", p) for p in PUBLIC_PAGES]
        api = [probe(client, m, p) for m, p in ENDPOINTS]

    working = [f"{p.method} {p.path}" for p in api if p.exists and not p.auth_required and p.status == 200]
    auth_needed = [f"{p.method} {p.path}" for p in api if p.auth_required or p.status in (401, 403)]
    missing = [f"{p.method} {p.path}" for p in api if not p.exists]

    mission_status = {
        "phase": "recon_complete",
        "platform": "viewmax.io",
        "api_mapped": len([p for p in api if p.exists]),
        "auth_gated": len(auth_needed),
        "next_steps": [
            "Provide valid session cookies for authenticated probing of /api/me and generation endpoints",
            "Capture HAR from logged-in browser for full request/response shapes",
            "Build legitimate API client wrapper (not bypass tooling)",
            "Restore scenx_bot.py if Telegram automation is the end goal",
        ],
        "blocked_without_session": [
            "video generation",
            "image generation",
            "ai-clone / kling motion control",
            "credit balance check",
            "subscription management",
        ],
    }

    return MissionReport(
        target=BASE,
        tech=tech,
        public_pages=public,
        api_endpoints=api,
        working_unauthenticated=working,
        requires_auth=auth_needed,
        not_found=missing,
        mission_status=mission_status,
    )


def main() -> int:
    report = run_mission()
    data = asdict(report)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=2))
    print(f"\nSaved → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
