import asyncio
import httpx
from app.models.service import ServiceStatus

async def main():
    url = "http://localhost:8000/metrics" # We know this works and returns 200
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url)
            print("Status Code:", response.status_code)
            if 200 <= response.status_code < 300:
                print("Returning HEALTHY")
            else:
                print("Returning UNHEALTHY")
        except Exception as e:
            print("Exception:", type(e), e)
            print("Returning UNHEALTHY")

asyncio.run(main())
