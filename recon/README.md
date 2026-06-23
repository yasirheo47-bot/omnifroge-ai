# Viewmax.io Mission Recon

Original mission: map viewmax.io platform surface for integration.

## Run

```bash
pip install httpx
python3 recon/viewmax_mission.py
```

Output: `recon/MISSION_REPORT.json`

## What it does

- Probes all API endpoints found in legacy 16may tooling
- Tests public pages and redirect behavior
- Classifies each endpoint: exists / auth-required / not found
- Documents tech stack (Next.js, Vercel, better-auth cookies)

## Auth cookies (for authenticated phase)

- `__Secure-better-auth.session_token`
- `__Secure-better-auth.session_data`
- `vm_vid`

Set these via env vars for phase 2 — never commit real values.
