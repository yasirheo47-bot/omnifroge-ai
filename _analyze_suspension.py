"""
Suspension system reverse engineering:
1. Bundle search: disabled field, suspend logic, ban triggers
2. What edge functions check/set disabled?
3. Any rate limiting / anomaly detection patterns
4. Admin suspend flow
5. What the recoverMyStuckMedia function might flag
"""
import re

code = open('_bundle_latest.js', encoding='utf-8', errors='replace').read()

sections = {
    'disabled field usage':       [r'disabled', r'is_disabled', r'\.disabled'],
    'suspend/ban logic':          [r'suspend', r'ban\b', r'block.*user', r'flag.*user'],
    'rate limit':                 [r'rate.?limit', r'too.?many', r'throttle', r'cooldown', r'per.?minute', r'per.?hour'],
    'abuse detection':            [r'abuse', r'fraud', r'anomal', r'suspicious', r'unusual.*activity'],
    'admin disable functions':    [r'adminDisable', r'adminBan', r'adminSuspend', r'disableUser', r'banUser'],
    'recover stuck guard':        [r'recoverMyStuck', r'recover.*abuse', r'recover.*limit'],
    'credit anomaly':             [r'credit.*limit', r'max.*credit', r'credit.*cap', r'credit.*abuse'],
    'security check fns':         [r'checkSecurity', r'securityCheck', r'detectAbuse', r'flagAccount'],
    'fingerprint / device':       [r'fingerprint', r'device_id', r'device_fingerprint'],
    'IP / geo block':             [r'ip.?address', r'ip.?block', r'geo.?block', r'country.?block'],
}

for section, patterns in sections.items():
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, code, re.I):
            ctx = code[max(0,m.start()-150):m.start()+300]
            if ctx not in hits:
                hits.append((m.start(), ctx))
    if hits:
        print(f"\n{'='*70}")
        print(f"=== {section.upper()} ===")
        for pos, ctx in hits[:4]:  # limit to 4 per section
            print(f"\n  [@ {pos}]")
            print(f"  ...{ctx}...")
