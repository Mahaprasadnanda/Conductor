import asyncio
from app.gateway.registry import ServiceRegistry
from app.gateway.cache import service_cache
from app.database.connection import async_session_maker
from sqlalchemy import select
from app.models.service import Service
from app.main import app

async def test():
    async with async_session_maker() as db:
        res = await db.execute(select(Service))
        services = res.scalars().all()
        service_cache.sync_from_db(list(services))
        
    await ServiceRegistry.run_health_checks()
    
    for svc in service_cache.list_all():
        print(f"Cache - {svc.get('service_name')}: {svc.get('status')}")

asyncio.run(test())
