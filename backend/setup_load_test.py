import asyncio
from app.database.connection import async_session_maker
from app.models.service import Service, ServiceStatus
from app.models.resilience import ResiliencePolicy

async def setup():
    async with async_session_maker() as session:
        # Create service
        svc = Service(
            project_id=1,
            service_name='resilient_service',
            base_url='http://non-existent-domain-12345.com',
            status=ServiceStatus.HEALTHY,
            authentication_mode='DISABLED'
        )
        session.add(svc)
        await session.flush()
        
        # Create policy
        policy = ResiliencePolicy(
            service_id=svc.id,
            failure_threshold=5,
            recovery_timeout=10,
            half_open_requests=2,
            retry_attempts=1,
            request_timeout=2,
            fallback_enabled=True,
            fallback_response={'message': 'Fallback triggered by k6'}
        )
        session.add(policy)
        await session.commit()
        print('Setup complete')

if __name__ == '__main__':
    asyncio.run(setup())
