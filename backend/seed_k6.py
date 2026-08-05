import httpx
import asyncio

async def run():
    async with httpx.AsyncClient() as c:
        r1 = await c.post('http://localhost:8000/api/v1/services/', json={
            'service_name': 'test-k6',
            'base_url': 'http://localhost:8000',
            'authentication_mode': 'PUBLIC'
        })
        print("Service Status:", r1.status_code)
        print("Service Text:", r1.text)
        s_id = r1.json()['id']
        
        r2 = await c.post('http://localhost:8000/api/v1/rate-limits/', json={
            'service_id': s_id,
            'limit': 100,
            'window_seconds': 10,
            'algorithm': 'SLIDING_WINDOW_LOG',
            'enabled': True
        })
        print("Policy:", r2.json())

asyncio.run(run())
