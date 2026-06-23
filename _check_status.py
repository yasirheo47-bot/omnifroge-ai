import asyncio, aiohttp

EMAIL = "quicken-jolt-crave@duck.com"
PASSWORD = "quicken-jolt-crave@duck.com"
BASE = "https://www.viewmax.io"
HDRS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": BASE,
    "Referer": BASE + "/",
}

async def main():
    jar = aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(cookie_jar=jar) as s:
        await s.post(f"{BASE}/api/auth/sign-in/email",
                     json={"email": EMAIL, "password": PASSWORD, "rememberMe": True},
                     headers=HDRS)
        async with s.get(f"{BASE}/api/me", headers=HDRS) as r:
            d = await r.json()
            svc = next((x for x in d.get("subscription",{}).get("services",[]) if x["type"]=="AI_CREDITS"),{})
            print(f"used: {svc.get('used')} / max: {svc.get('max')}  purchased: {d.get('purchasedCredits')}")
        async with s.get(f"{BASE}/api/video-generation/list?page=1&pageSize=20", headers=HDRS) as r:
            d = await r.json()
            items = d.get("items", d.get("data", d.get("videos", [])))
            print("Recent videos:")
            for v in items[:20]:
                print(f"  {v.get('id','-')[:24]}  status={v.get('status','?'):<12}  model={v.get('model','?')}")

asyncio.run(main())
