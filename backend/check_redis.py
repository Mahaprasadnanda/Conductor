import asyncio, json
from app.database.connection import redis_client

async def run():
    items = await redis_client.lrange('gateway:recent_errors', 0, 5)
    print([json.loads(i) for i in items])

asyncio.run(run())
