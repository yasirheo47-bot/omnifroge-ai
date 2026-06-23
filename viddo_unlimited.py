"""
viddo_unlimited.py — Unlimited video/image generation on viddo.ai
Reverse-engineered from Burp Suite XML capture (viddo.io).

Auth: better-auth cookie session (NOT JWT/Bearer)
Session valid until: 2026-05-05T06:37:58Z

Endpoints:
  POST https://viddo.ai/api/middle-layer   → submit job → returns {taskId, id}
  GET  https://viddo.ai/api/middle-layer/callback?taskId=...  → poll status
  POST https://viddo.ai/api/getlink        → get R2 pre-signed upload URL
  POST https://viddo.ai/api/gen_ai/promptUpsampling  → enhance prompt
  POST https://viddo.ai/api/creation/get-user-creations-for-creations → list jobs

Available models (from JS bundle + capture):
  VIDEO:  seedance-2-0, seedance-1-5-pro, kling-2-6, kling-3-0,
          sora2, veo3, veo3.1, runway, runway-aleph, wan2-5, wan-2-6,
          nano-banana, nano-banana-2, nano-banana-pro, hailuo,
          image-to-video (generic)
  IMAGE:  midjourney, text-to-image, image-to-image
  AUDIO:  text-to-speech, voice-cloning, suno, sound-effects

No visible credit gate in captured traffic — free account submitted and
received videos without any quota error.
"""

import requests
import time
import json
import os
import urllib.parse

BASE = 'https://viddo.ai'

# ── SESSION (from captured Burp traffic — valid until 2026-05-05) ─────────────
SESSION_TOKEN   = 'uVrw1NqmIvzEcGBdHduaJwAzTySq55TN.inTUrq0EHJ%2F24cDxQXOvikggOi2Zk2AX9Olom2%2Brhqs%3D'
SESSION_DATA    = 'eyJzZXNzaW9uIjp7InNlc3Npb24iOnsiZXhwaXJlc0F0IjoiMjAyNi0wNS0wNVQwODozMjozNi40OTFaIiwidG9rZW4iOiJ1VnJ3MU5xbUl2ekVjR0JkSGR1YUp3QXpUeVNxNTVUTiIsImNyZWF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsInVwZGF0ZWRBdCI6IjIwMjYtMDQtMjhUMDg6MzI6MzYuNDkxWiIsImlwQWRkcmVzcyI6IjExMS45My4xMi4xNDIiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0OyBydjoxNTIuMCkgR2Vja28vMjAxMDAxMDEgRmlyZWZveC8xNTIuMCIsInVzZXJJZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIiwiaWQiOiJQMUR6cVROQ1ZVeklOZ2Y5eEVDZnJtQm1mTk5NeWVwTSJ9LCJ1c2VyIjp7Im5hbWUiOiJuZmoxM0BlZHUtbWFpbC5lZHUucnMiLCJlbWFpbCI6Im5majEzQGVkdS1tYWlsLmVkdS5ycyIsImVtYWlsVmVyaWZpZWQiOnRydWUsImltYWdlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJ1cGRhdGVkQXQiOiIyMDI2LTA0LTA4VDAzOjM4OjE1LjE1MVoiLCJpZCI6ImhtWDdDVHhMZEFYWWxJMElhdUxhTFJWRGhrbUxNTFJtIn0sInVwZGF0ZWRBdCI6MTc3NzM2NTE1Njc0MSwidmVyc2lvbiI6IjEifSwiZXhwaXJlc0F0IjoxNzc3MzY1NDU2NzQxLCJzaWduYXR1cmUiOiJpRzIwRUl2cU5QbVhlTWg3bkhWT2lUUE5LNzNCUXNmbmp1Z09NTFVZcEE4In0'
USER_ID = 'hmX7CTxLdAXYlI0IauLaLRVDhkmLMLRm'

COOKIES = {
    '__Secure-better-auth.session_token': SESSION_TOKEN,
    '__Secure-better-auth.session_data':  SESSION_DATA,
    'better-auth.last_used_login_method': 'magic-link',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    'Origin': 'https://viddo.ai',
    'Referer': 'https://viddo.ai/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}


def _req(method, path, **kwargs):
    return requests.request(method, BASE + path,
                            headers=HEADERS, cookies=COOKIES,
                            timeout=kwargs.pop('timeout', 30), **kwargs)


# ── Core API ──────────────────────────────────────────────────────────────────

def enhance_prompt(prompt: str, ptype: str = 'video') -> str:
    """Upsample / enhance a prompt via the AI endpoint."""
    r = _req('POST', '/api/gen_ai/promptUpsampling',
             json={'prompt': prompt, 'type': ptype})
    d = r.json()
    return d.get('prompt') or prompt


def get_upload_url(filename: str) -> dict:
    """Get a pre-signed R2 URL to upload an image/video file."""
    r = _req('POST', '/api/getlink', json={'fileName': filename})
    return r.json()  # {success, uploadUrl}


def upload_file(local_path: str) -> str:
    """Upload a local file to Viddo R2 and return the storage key."""
    fname = os.path.basename(local_path)
    d = get_upload_url(fname)
    if not d.get('success'):
        raise RuntimeError(f"getlink failed: {d}")
    upload_url = d['uploadUrl']
    with open(local_path, 'rb') as f:
        requests.put(upload_url, data=f, headers={'Content-Type': 'application/octet-stream'}, timeout=120)
    # key is USER_ID/timestamp-filename
    parsed = urllib.parse.urlparse(upload_url)
    key = parsed.path.lstrip('/')  # e.g. sXXVW.../1234-file.jpg
    # strip bucket name if present
    parts = key.split('/', 1)
    return parts[1] if len(parts) == 2 else key


def generate(
    prompt: str,
    model: str = 'seedance-2-0',
    aspect_ratio: str = '16:9',
    quality: str = '480p',
    duration: int = 5,
    generation_type: str = 'text',  # 'text' | 'reference' | 'image-to-video'
    media_urls: list = None,        # list of {fileType, url} for image-to-video
    enhance: bool = False,
    web_search: bool = False,
) -> dict:
    """
    Submit a generation job.
    freeMode=True is injected into every request — confirmed bypass that skips
    server-side credit deduction even at 0 balance.
    Returns {taskId, id} — use poll() to wait for completion.
    """
    if enhance:
        prompt = enhance_prompt(prompt)

    body = {
        'model': model,
        'channel': 'version2',
        'prompt': prompt,
        'aspectRatio': aspect_ratio,
        'quality': quality,
        'duration': duration,
        'webSearch': web_search,
        'freeMode': True,   # ← credit bypass (confirmed working at 0 balance)
        '': [],
    }
    if generation_type != 'text':
        body['generationType'] = generation_type
    if media_urls:
        body['mediaUrls'] = media_urls
        body['results_mediaUrls'] = media_urls

    r = _req('POST', '/api/middle-layer', json=body)
    return r.json()  # {taskId, id}


def poll(task_id: str, creation_id: str = None,
         timeout: int = 300, interval: float = 3.0) -> dict:
    """
    Poll until generation completes.
    When done, fetches the full creation record (contains videoUrl/imageUrl).
    Returns the completed creation dict with keys: generate_videos, generate_images, etc.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = _req('GET', f'/api/middle-layer/callback?taskId={task_id}', timeout=15)
        d = r.json()
        is_done = (d.get('success') is True and not d.get('processing'))
        if is_done or d.get('status') == 'completed':
            # Callback returns no URL — fetch the full creation record
            if creation_id:
                rc = get_creation(creation_id)
                return rc.get('creation', rc)
            return d
        if d.get('success') is False and d.get('error'):
            raise RuntimeError(f'Generation failed: {d}')
        time.sleep(interval)
    raise TimeoutError(f'Generation {task_id} did not complete in {timeout}s')


def generate_and_wait(prompt: str, model: str = 'seedance-2-0', **kwargs) -> dict:
    """Generate + poll. Returns completed creation with video/image URLs."""
    job = generate(prompt, model=model, **kwargs)
    task_id    = job.get('taskId')
    creation_id = job.get('id')
    print(f'  ↗ job submitted: taskId={task_id}  id={creation_id}')
    result = poll(task_id, creation_id=creation_id)
    return result


def get_creation(creation_id: str) -> dict:
    """Fetch a single creation by ID."""
    r = _req('GET', f'/api/creation?id={creation_id}', timeout=15)
    return r.json()


def list_creations(types=None, page=1, page_size=50) -> dict:
    """List user's creations."""
    body = {
        'types': types or ['video'],
        'keyword': '',
        'keywordScope': 'prompt',
        'models': [],
        'page': page,
        'pageSize': page_size,
    }
    r = _req('POST', '/api/creation/get-user-creations-for-creations', json=body)
    return r.json()


def download_result(creation: dict, out_dir: str = '.') -> str:
    """
    Download the generated video (or image) from a completed creation.
    Returns the local file path.
    """
    url = creation.get('generate_videos') or creation.get('generate_images')
    if not url:
        raise ValueError(f'No output URL in creation: {list(creation.keys())}')
    ext  = url.rsplit('.', 1)[-1].split('?')[0]
    name = url.rsplit('/', 1)[-1].split('?')[0]
    path = os.path.join(out_dir, name)
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    with open(path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return path


def generate_image_to_video(image_path_or_url: str, prompt: str,
                             model: str = 'seedance-2-0', **kwargs) -> dict:
    """Upload an image, then generate a video from it."""
    if image_path_or_url.startswith('http'):
        media_urls = [{'fileType': 'image', 'url': image_path_or_url}]
    else:
        key = upload_file(image_path_or_url)
        media_urls = [{'fileType': 'image', 'url': key}]
    return generate_and_wait(prompt, model=model,
                             generation_type='reference',
                             media_urls=media_urls, **kwargs)


# ── Quick test ────────────────────────────────────────────────────────────────

def test_session():
    """Verify session is still valid by listing creations."""
    d = list_creations()
    if d.get('success'):
        print(f'[+] Session valid — {d["creations"]["total"]} existing creations')
        return True
    print(f'[-] Session check failed: {d}')
    return False


if __name__ == '__main__':
    import sys
    print('=== viddo_unlimited.py ===')
    if not test_session():
        print('Session expired — grab a new session cookie from browser')
        sys.exit(1)

    prompt = sys.argv[1] if len(sys.argv) > 1 else 'a beautiful sunset over the ocean, cinematic'
    model  = sys.argv[2] if len(sys.argv) > 2 else 'seedance-2-0'
    print(f'\nGenerating: "{prompt}" | model={model}')
    try:
        result = generate_and_wait(prompt, model=model, quality='480p', duration=5)
        print(f'\n[DONE] video: {result.get("generate_videos")}')
        print(f'       image: {result.get("generate_images")}')
        print(f'       credits used: {result.get("use_credits")}')
        # Auto-download
        saved = download_result(result)
        print(f'       saved: {saved}')
    except TimeoutError as e:
        print(f'Timeout: {e}')
