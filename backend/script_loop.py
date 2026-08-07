import asyncio
from app.gateway.registry import ServiceRegistry
from app.gateway.cache import service_cache
from app.main import app
import traceback

async def test():
    try:
        await ServiceRegistry.run_health_checks()
        print('run_health_checks completed successfully!')
        
        for svc in service_cache.list_all():
            print(f"Cache - {svc.get('service_name')}: {svc.get('status')}")
            
    except Exception as e:
        print('Exception in run_health_checks!')
        traceback.print_exc()

asyncio.run(test())
