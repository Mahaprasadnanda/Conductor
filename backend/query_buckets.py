import asyncio
import httpx
import urllib.parse

async def run():
    query = 'gateway_request_latency_seconds_bucket'
    url = f"http://prometheus:9090/api/v1/query?query={urllib.parse.quote(query)}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            for r in data.get("data", {}).get("result", []):
                print(r["metric"], r["value"])
        except Exception as e:
            print("Failed:", e)

asyncio.run(run())
