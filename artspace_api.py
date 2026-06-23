"""
artspace_api.py — Full keep-alive Python API wrapper for ArtSpace.ai
Reverse-engineered from Burp Suite capture.

Keep-alive features:
  - Background heartbeat thread refreshes CSRF token every N seconds
  - Auto re-login on 401 / 419 / expired session
  - Thread-safe locking (safe to call from multiple threads / bots)
  - Retry with exponential back-off on transient errors
  - Session health check: client.is_alive()

Generation features: text-to-image, img2img (image seed), negative prompt,
seed, width/height, model, enhance, image_strength, mask, preset styles,
history, image store/upload, image download.
"""

import base64
import logging
import os
import random
import threading
import time
import urllib.parse
from typing import Optional

import requests

log = logging.getLogger("artspace")


# ─── known models ────────────────────────────────────────────────────────────
MODELS = {
    "atomic-pro":   "Atomic Pro (latest)",
    "nova2024-flux": "Nova 2024 Flux",
}

# ─── preset styles ───────────────────────────────────────────────────────────
PRESET_TYPES = ["raw", "photorealistic", "cinematic", "anime", "digital-art"]

# ─── fixed page fingerprint seen in all requests ─────────────────────────────
_PAGE_UUID    = "f904eb96-deab-1c87-93f2-d99420a51c15"
_PAGE_VERSION = "0.0.1"
_UA           = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) "
    "Gecko/20100101 Firefox/152.0"
)
_UA_OBJ = {
    "ua":      _UA,
    "browser": {"name": "Firefox", "version": "152.0", "major": "152"},
    "cpu":     {"architecture": "amd64"},
    "device":  {},
    "engine":  {"name": "Gecko", "version": "152.0"},
    "os":      {"name": "Windows", "version": "10"},
}


# ─── tuneable defaults ────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL  = 120   # seconds between keep-alive pings
MAX_RETRIES         = 4     # max attempts per request
RETRY_BASE_DELAY    = 1.5   # seconds; doubles each retry
SESSION_EXPIRE_CODE = {401, 419}  # HTTP codes meaning "re-login required"


class ArtspaceError(Exception):
    pass


class ArtspaceClient:
    """
    Long-lived, keep-alive client for the ArtSpace.ai image generation API.

    Quick start (auto keep-alive)::

        client = ArtspaceClient()
        client.login("you@example.com", "yourpassword")
        # background thread keeps the session alive automatically
        result = client.generate("a futuristic city at night", seed=12345)
        print(result["image_url"])

    Supply pre-captured cookies instead of logging in::

        client = ArtspaceClient(cookies={
            "XSRF-TOKEN":        "<value>",
            "artspaceai_session": "<value>",
        })
        # keep-alive starts automatically when cookies are provided

    Use as a context manager to auto-stop the background thread::

        with ArtspaceClient() as client:
            client.login(...)
            result = client.generate(...)
    """

    BASE       = "https://www.artspace.ai"
    SPACE_BASE = "https://space.artspace.ai"

    def __init__(
        self,
        cookies:            Optional[dict] = None,
        timeout:            int            = 120,
        heartbeat_interval: int            = HEARTBEAT_INTERVAL,
        auto_keepalive:     bool           = True,
    ) -> None:
        self.timeout            = timeout
        self.heartbeat_interval = heartbeat_interval
        self._auto_keepalive    = auto_keepalive

        # stored credentials for auto re-login
        self._email:    Optional[str] = None
        self._password: Optional[str] = None
        self._logged_in = False

        # thread safety — RLock so the same thread can re-enter
        self._lock       = threading.RLock()
        self._stop_event = threading.Event()
        self._hb_thread: Optional[threading.Thread] = None

        self._sess = requests.Session()
        self._sess.headers.update({
            "User-Agent":       _UA,
            "Accept":           "application/json, text/plain, */*",
            "Accept-Language":  "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
        })
        if cookies:
            for k, v in cookies.items():
                for domain in (".artspace.ai", "space.artspace.ai", "www.artspace.ai"):
                    self._sess.cookies.set(k, v, domain=domain)
            self._logged_in = True
            if auto_keepalive:
                self.start_keepalive()

    # ─── auth ─────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate with email/password. Stores credentials for auto re-login.
        Starts the keep-alive heartbeat automatically.
        Returns auth user dict.
        """
        self._email    = email
        self._password = password
        result = self._do_login()
        if self._auto_keepalive:
            self.start_keepalive()
        return result

    def _do_login(self) -> dict:
        """Internal — called on first login and on auto re-login."""
        with self._lock:
            log.info("[artspace] logging in …")
            self._sess.get(f"{self.BASE}/sanctum/csrf-cookie", timeout=self.timeout)
            xsrf = self._raw_xsrf()
            resp = self._sess.post(
                f"{self.BASE}/signin",
                headers={
                    "Content-Type":      "application/json",
                    "X-Xsrf-Token":      xsrf,
                    "X-Inertia":         "true",
                },
                json={"email": self._email, "password": self._password, "remember": True},
                allow_redirects=True,
                timeout=self.timeout,
            )
            # Inertia 409 = asset version mismatch; the login itself succeeds
            # and session cookies are set. Any other non-redirect code is a real error.
            if resp.status_code not in (200, 302, 409):
                raise ArtspaceError(f"Login failed: HTTP {resp.status_code}")
            if resp.status_code == 409:
                log.warning("[artspace] signin 409 (Inertia version drift) — session cookies accepted")
            # Validate the session with a plain (non-Inertia) request so the
            # server never triggers another 409.
            me = self._sess.get(
                f"{self.BASE}/",
                headers={"Accept": "text/html,application/xhtml+xml,*/*"},
                timeout=self.timeout,
            )
            if me.status_code not in (200, 302):
                raise ArtspaceError(f"Login state check failed: HTTP {me.status_code}")
            self._logged_in = True
            log.info("[artspace] login OK")
            return {}

    def set_cookies(self, xsrf_token: str, session_cookie: str) -> None:
        """
        Inject session cookies manually (alternative to login()).
        Call start_keepalive() afterward.
        """
        with self._lock:
            for domain in (".artspace.ai", "space.artspace.ai", "www.artspace.ai"):
                self._sess.cookies.set("XSRF-TOKEN",         xsrf_token,     domain=domain)
                self._sess.cookies.set("artspaceai_session",  session_cookie, domain=domain)
        self._logged_in = True

    # ─── keep-alive ───────────────────────────────────────────────────────────

    def start_keepalive(self) -> None:
        """
        Start the background heartbeat thread. Safe to call multiple times.
        The thread is a daemon, so it dies automatically with the process.
        """
        if self._hb_thread and self._hb_thread.is_alive():
            return
        self._stop_event.clear()
        self._hb_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="artspace-keepalive",
            daemon=True,
        )
        self._hb_thread.start()
        log.info("[artspace] keep-alive started (interval=%ds)", self.heartbeat_interval)

    def stop_keepalive(self) -> None:
        """Signal the heartbeat thread to stop and wait for it."""
        self._stop_event.set()
        if self._hb_thread:
            self._hb_thread.join(timeout=5)
        log.info("[artspace] keep-alive stopped")

    def is_alive(self) -> bool:
        """
        Lightweight session health-check.
        Returns True if the current session is valid.
        """
        try:
            with self._lock:
                xsrf = self._raw_xsrf()
                resp = self._sess.post(
                    f"{self.SPACE_BASE}/history/load",
                    params={"page": 1},
                    headers={
                        "Content-Type": "application/json",
                        "X-Xsrf-Token": xsrf,
                        "Origin":       self.SPACE_BASE,
                        "Referer":      f"{self.SPACE_BASE}/",
                    },
                    json={},
                    timeout=15,
                )
                return resp.status_code == 200
        except Exception:
            return False

    def _heartbeat_loop(self) -> None:
        """Daemon thread body — refreshes CSRF every interval seconds."""
        while not self._stop_event.wait(timeout=self.heartbeat_interval):
            try:
                with self._lock:
                    self._sess.get(f"{self.BASE}/sanctum/csrf-cookie", timeout=15)
                log.debug("[artspace] CSRF refreshed")
            except Exception as exc:
                log.warning("[artspace] heartbeat failed: %s", exc)
                if self._email and self._password:
                    try:
                        self._do_login()
                    except Exception as le:
                        log.error("[artspace] re-login failed: %s", le)

    # ─── context manager ──────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.stop_keepalive()

    # ─── generation ───────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        *,
        negative_prompt:   str            = "",
        seed:              Optional[int]   = None,
        width:             int             = 1024,
        height:            int             = 1024,
        model:             str             = "atomic-pro",
        enhance:           bool            = True,
        image:             Optional[bytes] = None,
        image_b64:         Optional[str]   = None,
        image_strength:    int             = 20,
        mask:              Optional[bytes] = None,
        mask_b64:          Optional[str]   = None,
        mode:              int             = 0,
        content_filter:    bool            = True,
        preset_type:       str             = "raw",
        preset_version:    int             = 1,
        wait_for_image:    bool            = True,
        poll_interval:     float           = 1.5,
        poll_max_wait:     float           = 90.0,
    ) -> dict:
        """
        Generate an image. Auto-retries on transient failures; auto re-logins
        on 401/419 session expiry.

        Parameters
        ----------
        prompt            : Text prompt.
        negative_prompt   : Negative prompt.
        seed              : Seed (random if None).
        width / height    : Output dimensions in pixels.
        model             : Model ID — see ``MODELS``.
        enhance           : Enable AI prompt enhancement.
        image             : Raw bytes of init image (img2img / image seed).
        image_b64         : Pre-encoded base64 data URI (alternative to ``image``).
        image_strength    : Init image influence 0–100 (default 20).
        mask              : Raw bytes of inpaint mask.
        mask_b64          : Pre-encoded mask data URI.
        mode              : Generation mode (0 = standard).
        content_filter    : Enable content filter.
        preset_type       : Style preset ("raw", "photorealistic", …).
        preset_version    : Preset version integer.
        wait_for_image    : Poll history/load/latest until image URL confirmed.
        poll_interval     : Seconds between polls.
        poll_max_wait     : Max seconds to wait when polling.

        Returns dict: uuid, image_url, thumbnail_url, model, prompt,
                      negative_prompt, seed, width, height, created_at, time_ms
        """
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        if image is not None and image_b64 is None:
            image_b64 = _to_data_uri(image)
        if mask is not None and mask_b64 is None:
            mask_b64 = _to_data_uri(mask)

        payload = {
            "isSimplified":      False,
            "mode":              mode,
            "modelId":           model,
            "enhance":           enhance,
            "prompt":            prompt,
            "prompt_negative":   negative_prompt,
            "image":             image_b64,
            "mask":              mask_b64,
            "seed":              seed,
            "width":             width,
            "height":            height,
            "image_strength":    image_strength,
            "content_filter":    content_filter,
            "preset2023Type":    preset_type,
            "preset2023Version": preset_version,
            "preset2024Type":    preset_type,
            "preset2024Version": preset_version,
            "user_agent":        _UA_OBJ,
            "pageUuid":          _PAGE_UUID,
            "pageVersion":       _PAGE_VERSION,
        }

        def _attempt():
            with self._lock:
                xsrf = self._get_xsrf()
                return self._sess.post(
                    f"{self.SPACE_BASE}/draw-image",
                    headers={
                        "Content-Type":    "application/json",
                        "X-Xsrf-Token":    xsrf,
                        "Idempotency-Key": f'"{random.getrandbits(63)}"',
                        "Origin":          self.SPACE_BASE,
                        "Referer":         f"{self.SPACE_BASE}/",
                        "Sec-Fetch-Dest":  "empty",
                        "Sec-Fetch-Mode":  "cors",
                        "Sec-Fetch-Site":  "same-origin",
                    },
                    json=payload,
                    timeout=self.timeout,
                )

        resp = self._with_retry(_attempt, "draw-image")
        data = resp.json()
        item = data[0] if isinstance(data, list) else data

        result = {
            "uuid":            item.get("uuid"),
            "image_url":       item.get("url"),
            "thumbnail_url":   None,
            "model":           model,
            "prompt":          prompt,
            "negative_prompt": negative_prompt,
            "seed":            seed,
            "width":           width,
            "height":          height,
            "created_at":      None,
            "time_ms":         item.get("time"),
        }
        # If artspace already returned the image URL in the draw-image response,
        # skip polling entirely — no need to wait.
        if wait_for_image and not result.get("image_url"):
            confirmed = self._poll_latest(result["uuid"], poll_interval, poll_max_wait)
            if confirmed:
                result.update(confirmed)
        return result

    def generate_with_image(
        self,
        prompt:          str,
        image:           bytes,
        *,
        negative_prompt: str           = "",
        seed:            Optional[int]  = None,
        image_strength:  int            = 20,
        **kwargs,
    ) -> dict:
        """img2img convenience wrapper."""
        return self.generate(
            prompt,
            image=image,
            negative_prompt=negative_prompt,
            seed=seed,
            image_strength=image_strength,
            **kwargs,
        )

    # ─── history ──────────────────────────────────────────────────────────────

    def get_history(self, page: int = 1) -> list:
        """Return a page of generation history (20 items per page)."""
        def _attempt():
            with self._lock:
                xsrf = self._get_xsrf()
                return self._sess.post(
                    f"{self.SPACE_BASE}/history/load",
                    params={"page": page},
                    headers={
                        "Content-Type": "application/json",
                        "X-Xsrf-Token": xsrf,
                        "Origin":       self.SPACE_BASE,
                        "Referer":      f"{self.SPACE_BASE}/",
                    },
                    json={},
                    timeout=self.timeout,
                )
        return self._with_retry(_attempt, "history/load").json().get("submissions", [])

    def get_tools_history(self, page: int = 1) -> list:
        """Return a page of tools history."""
        def _attempt():
            with self._lock:
                xsrf = self._get_xsrf()
                return self._sess.post(
                    f"{self.SPACE_BASE}/tools-history/load",
                    params={"page": page},
                    headers={
                        "Content-Type": "application/json",
                        "X-Xsrf-Token": xsrf,
                        "Origin":       self.SPACE_BASE,
                        "Referer":      f"{self.SPACE_BASE}/",
                    },
                    json={},
                    timeout=self.timeout,
                )
        return self._with_retry(_attempt, "tools-history/load").json().get("submissions", [])

    # ─── image store ──────────────────────────────────────────────────────────

    def store_image(self, image_bytes: bytes, filename: str = "image.png") -> str:
        """Upload image bytes to ArtSpace storage. Returns base64 data URI."""
        def _attempt():
            with self._lock:
                xsrf = self._get_xsrf()
                return self._sess.post(
                    f"{self.SPACE_BASE}/image/store",
                    headers={
                        "X-Xsrf-Token": xsrf,
                        "Origin":       self.SPACE_BASE,
                        "Referer":      f"{self.SPACE_BASE}/",
                    },
                    files={"images[]": (filename, image_bytes, _guess_mime(filename))},
                    timeout=self.timeout,
                )
        return self._with_retry(_attempt, "image/store").json().get("base64", "")

    # ─── download ─────────────────────────────────────────────────────────────

    def download_image(self, image_url: str) -> bytes:
        """Download generated image bytes from the signed URL."""
        resp = self._sess.get(image_url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.content

    # ─── internal helpers ─────────────────────────────────────────────────────

    def _raw_xsrf(self) -> str:
        """Return URL-decoded XSRF token without raising if absent."""
        for domain in ("space.artspace.ai", ".artspace.ai", None):
            raw = self._sess.cookies.get("XSRF-TOKEN", domain=domain)
            if raw:
                return urllib.parse.unquote(raw)
        return ""

    def _get_xsrf(self) -> str:
        """Return a valid XSRF token, refreshing if missing."""
        token = self._raw_xsrf()
        if not token:
            self._sess.get(f"{self.BASE}/sanctum/csrf-cookie", timeout=15)
            token = self._raw_xsrf()
        if not token:
            raise ArtspaceError(
                "XSRF-TOKEN not available. Call login() or set_cookies() first."
            )
        return token

    def _with_retry(self, attempt_fn, endpoint: str) -> requests.Response:
        """
        Run attempt_fn() up to MAX_RETRIES times.
        - 401/419 → re-login then retry.
        - 5xx / network error → exponential back-off then retry.
        """
        delay = RETRY_BASE_DELAY
        last_exc: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = attempt_fn()
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                log.warning("[artspace] %s attempt %d/%d network error: %s",
                            endpoint, attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    time.sleep(delay); delay *= 2
                continue

            if resp.status_code in SESSION_EXPIRE_CODE:
                log.warning("[artspace] %s got %d — re-logging in",
                            endpoint, resp.status_code)
                if self._email and self._password:
                    try:
                        self._do_login()
                    except Exception as exc:
                        raise ArtspaceError(f"Re-login failed: {exc}") from exc
                    if attempt < MAX_RETRIES:
                        time.sleep(delay); delay *= 2
                        continue
                raise ArtspaceError(
                    f"{endpoint}: session expired (HTTP {resp.status_code}) "
                    "and no credentials stored for re-login."
                )

            if resp.status_code >= 500:
                log.warning("[artspace] %s attempt %d/%d server error HTTP %d",
                            endpoint, attempt, MAX_RETRIES, resp.status_code)
                if attempt < MAX_RETRIES:
                    time.sleep(delay); delay *= 2
                    continue
                _raise_for_status(resp, endpoint)

            _raise_for_status(resp, endpoint)
            return resp

        raise ArtspaceError(
            f"{endpoint}: all {MAX_RETRIES} attempts failed. Last: {last_exc}"
        )

    def _poll_latest(
        self,
        target_uuid: str,
        interval:    float,
        max_wait:    float,
    ) -> Optional[dict]:
        """
        Poll /history/load (returns up to 20 recent submissions) until the
        target UUID appears with an image URL.

        NOTE: /history/load/latest only returns ONE entry — useless when
        multiple generations run concurrently because only the most-recent
        finished job ever appears there.  /history/load returns up to 20 items
        so all concurrent UUIDs can be found regardless of finish order.
        """
        deadline = time.time() + max_wait
        while time.time() < deadline:
            try:
                with self._lock:
                    xsrf = self._get_xsrf()
                    resp = self._sess.post(
                        f"{self.SPACE_BASE}/history/load",
                        params={"page": 1},
                        headers={
                            "Content-Type": "application/json",
                            "X-Xsrf-Token": xsrf,
                            "Origin":       self.SPACE_BASE,
                            "Referer":      f"{self.SPACE_BASE}/",
                        },
                        json={},
                        timeout=20,
                    )
                if resp.status_code == 200:
                    for s in resp.json().get("submissions", []):
                        if s.get("uuid") == target_uuid and s.get("image"):
                            return {
                                "image_url":     s["image"],
                                "thumbnail_url": s.get("thumbnail"),
                                "seed":          s.get("seed"),
                                "created_at":    s.get("created_at"),
                            }
            except Exception as exc:
                log.debug("[artspace] poll error: %s", exc)
            time.sleep(interval)
        log.warning("[artspace] poll timed out for uuid=%s", target_uuid)
        return None


# ─── module-level helpers ─────────────────────────────────────────────────────

def _to_data_uri(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif image_bytes[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        mime = "image/png"
    return f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"


def _guess_mime(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp"}.get(ext, "image/png")


def _raise_for_status(resp: requests.Response, endpoint: str) -> None:
    if resp.status_code not in (200, 201):
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text[:400]
        raise ArtspaceError(
            f"{endpoint} returned HTTP {resp.status_code}: {detail}"
        )


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
    )

    parser = argparse.ArgumentParser(description="ArtSpace.ai image generator (keep-alive)")
    parser.add_argument("prompt")
    parser.add_argument("--email",             required=True)
    parser.add_argument("--password",          required=True)
    parser.add_argument("--negative",          default="",          help="Negative prompt")
    parser.add_argument("--seed",              type=int, default=None)
    parser.add_argument("--width",             type=int, default=1024)
    parser.add_argument("--height",            type=int, default=1024)
    parser.add_argument("--model",             default="atomic-pro", choices=list(MODELS))
    parser.add_argument("--no-enhance",        action="store_true")
    parser.add_argument("--image",             default=None,        help="Path to init image")
    parser.add_argument("--image-strength",    type=int, default=20)
    parser.add_argument("--preset",            default="raw",        choices=PRESET_TYPES)
    parser.add_argument("--no-content-filter", action="store_true")
    parser.add_argument("--output",            default="output.png")
    args = parser.parse_args()

    with ArtspaceClient() as client:
        auth = client.login(args.email, args.password)
        print(f"[+] Logged in as: {auth.get('user', {}).get('email', '?')}")

        init_image = None
        if args.image:
            with open(args.image, "rb") as fh:
                init_image = fh.read()

        result = client.generate(
            args.prompt,
            negative_prompt = args.negative,
            seed            = args.seed,
            width           = args.width,
            height          = args.height,
            model           = args.model,
            enhance         = not args.no_enhance,
            image           = init_image,
            image_strength  = args.image_strength,
            content_filter  = not args.no_content_filter,
            preset_type     = args.preset,
        )

        print(f"[+] UUID:      {result['uuid']}")
        print(f"[+] Seed:      {result['seed']}")
        print(f"[+] Image URL: {result['image_url']}")

        if result["image_url"]:
            img_bytes = client.download_image(result["image_url"])
            with open(args.output, "wb") as fh:
                fh.write(img_bytes)
            print(f"[+] Saved to:  {args.output}")
