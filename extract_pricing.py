"""
Extract the full CreditCostByModel map and model list from the video-generator chunk.
"""
import asyncio, aiohttp, re

CHUNK_URL = "https://www.viewmax.io/_next/static/chunks/fe990f7183fe36d4.js"
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"}


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(CHUNK_URL, headers=HDRS) as r:
            text = await r.text()

    print(f"Chunk size: {len(text)//1024}KB\n")

    # Find CreditCostByModel definition
    idx = text.find("CreditCostByModel")
    if idx >= 0:
        snippet = text[max(0, idx-50):idx+2000]
        print("=== CreditCostByModel ===")
        print(snippet)
        print()

    # Also find CreditCost
    idx2 = text.find("CreditCost")
    while idx2 >= 0 and idx2 != idx:
        snippet2 = text[max(0, idx2-20):idx2+500]
        print(f"=== CreditCost at {idx2} ===")
        print(snippet2[:400])
        print()
        idx2 = text.find("CreditCost", idx2+1)
        if idx2 == text.find("CreditCostByModel"):
            break

    # Find all model names
    models = re.findall(r'"((?:Kling|Sora|Wan|Seedance|Hailuo|Dream|Lumia|Luma)[^"]{0,40})"', text)
    print(f"\n=== Model names found ===")
    for m in sorted(set(models)):
        print(f"  {m}")

    # Find multiplier validation
    mult_idx = text.find("multiplier")
    while mult_idx >= 0:
        snippet3 = text[max(0, mult_idx-50):mult_idx+300]
        print(f"\n=== multiplier at {mult_idx} ===")
        print(snippet3[:300])
        mult_idx = text.find("multiplier", mult_idx+1)
        if mult_idx > 50000:
            break

    # Look for any "free" or "trial" flags
    for term in ["freeGenerat", "trialGenerat", "promoCode", "bypassCredit", "skipCredit", "noCharge"]:
        if term.lower() in text.lower():
            idx_t = text.lower().find(term.lower())
            print(f"\n=== '{term}' found at {idx_t} ===")
            print(text[max(0, idx_t-100):idx_t+300])


asyncio.run(main())
