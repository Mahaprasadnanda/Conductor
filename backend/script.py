import asyncio
import traceback

# Import app to ensure all models and registries are initialized
from app.main import app
from app.gateway.cache import service_cache
from app.gateway.registry import ServiceRegistry
from app.models.service import ServiceStatus
from app.database.connection import async_session_maker
from app.repositories.service import service_repo
import structlog

log = structlog.get_logger()

async def debug_loop():
    try:
        service_data = {
            'service_id': 1,
            'service_name': 'demo',
            'base_url': 'http://host.docker.internal:9000',
            'health_check_path': '/health',
            'status': ServiceStatus.UNHEALTHY
        }
        service_cache.set('demo', service_data)
        
        result = await ServiceRegistry.check_health(service_data)
        print(f'check_health returned: {result}')
        
        service_name, new_status = result
        current_data = service_cache.get(service_name)
        
        print(f'current_data status: {current_data.get("status")}')
        print(f'new_status: {new_status}')
        
        if current_data and current_data.get('status') != new_status:
            print('Condition MET!')
            current_data['status'] = new_status
            service_cache.update_status(service_name, new_status)
            print('Cache updated!')
            
            async with async_session_maker() as db:
                db_service = await service_repo.get_by_name(db, service_name=service_name)
                if db_service:
                    print(f'DB service found! Current DB status: {db_service.status}')
                    db_service.status = new_status
                    db.add(db_service)
                    await db.commit()
                    print('DB committed!')
                    
                    # Verify DB
                    db_service_verify = await service_repo.get_by_name(db, service_name=service_name)
                    print(f'Verified DB status: {db_service_verify.status}')
                else:
                    print('DB service NOT found!')
        else:
            print('Condition NOT met!')
            
    except Exception as e:
        print(f'Exception: {e}')
        traceback.print_exc()

asyncio.run(debug_loop())
