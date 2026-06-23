"""
Scrape viewmax.io app bundle for pricing constants, model list, and hidden API params.
"""
import asyncio, aiohttp, re, json

BASE = "https://www.viewmax.io"
HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept": "*/*",
}


async def fetch(session, url):
    async with session.get(url, headers=HDRS) as r:
        return r.status, await r.text()


async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Get the home page to find JS chunk URLs
        print("Fetching home page for JS bundle URLs...")
        status, html = await fetch(session, f"{BASE}/")
        if status != 200:
            print(f"Home page failed: {status}")
            return

        # Find all _next/static JS chunks
        chunks = re.findall(r'/_next/static/[^"\']+\.js', html)
        chunks = list(set(chunks))
        print(f"Found {len(chunks)} JS chunks in HTML")

        # Also look for buildManifest
        manifests = re.findall(r'/_next/static/[^"\']+manifest[^"\']*\.js', html)
        print(f"Found manifests: {manifests}")

        # Try to find the main app chunk that would have pricing
        # Usually the largest chunk or one containing "generate"
        target_chunks = []
        for c in chunks:
            if any(k in c for k in ["app", "page", "main", "chunk"]):
                target_chunks.append(c)

        # Also try the build manifest directly
        build_manifest_urls = [
            "/_next/static/chunks/pages/_app.js",
            "/_next/static/chunks/main.js",
            "/_next/static/chunks/webpack.js",
        ]

        # Search any chunk we find for pricing/model data
        keywords = ["multiplier", "creditCost", "costPer", "Kling", "Sora", "Seedance", "Wan",
                    "promo", "trial", "free", "generate", "model", "pricing", "credits"]

        print(f"\nSearching {len(chunks[:20])} chunks for pricing data...")
        for chunk_url in chunks[:20]:
            url = f"{BASE}{chunk_url}"
            s, text = await fetch(session, url)
            if s != 200:
                continue
            hits = []
            for kw in keywords[:8]:  # just the most relevant
                if kw.lower() in text.lower():
                    hits.append(kw)
            if hits:
                print(f"\n  {chunk_url[:80]} ({len(text)//1024}KB) — keywords: {hits}")
                # Find model/pricing related patterns
                # Look for model list
                model_matches = re.findall(r'"(?:Kling|Sora|Wan|Seedance|model)[^"]{0,50}"', text)
                if model_matches:
                    print(f"    Models found: {list(set(model_matches))[:15]}")
                # Look for credit cost patterns
                credit_matches = re.findall(r'credit[A-Za-z]*[\s:=]+[\d.]+', text[:50000], re.I)
                if credit_matches:
                    print(f"    Credit patterns: {list(set(credit_matches))[:10]}")
                # Look for multiplier validation
                mult_matches = re.findall(r'multiplier[^;]{0,200}', text[:50000], re.I)
                if mult_matches:
                    print(f"    Multiplier logic: {mult_matches[:3]}")

        # Try to access the video-generator page's specific chunk
        print("\nFetching video-generator page for its specific chunks...")
        s2, html2 = await fetch(session, f"{BASE}/tools/video-generator")
        chunks2 = re.findall(r'/_next/static/[^"\']+\.js', html2)
        new_chunks = set(chunks2) - set(chunks)
        print(f"  New chunks on video-generator page: {len(new_chunks)}")
        for c in list(new_chunks)[:10]:
            url = f"{BASE}{c}"
            s, text = await fetch(session, url)
            if s != 200:
                continue
            if any(kw.lower() in text.lower() for kw in ["multiplier", "Kling", "model", "creditCost"]):
                print(f"\n  {c[:80]} ({len(text)//1024}KB)")
                # Deep search
                for pattern in [r'"model"[^}]{0,500}', r'multiplier[^;,)]{0,300}',
                                  r'creditCost[^;,)]{0,200}', r'"Kling[^"]{0,50}"']:
                    matches = re.findall(pattern, text[:100000], re.I)
                    if matches:
                        print(f"    {pattern[:30]}: {matches[:2]}")


asyncio.run(main())
