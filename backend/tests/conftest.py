import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database.connection import get_db_session
from app.models.base import Base
from app.config.settings import settings
import asyncio
from app.auth.security import get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.api_key import ApiKey
from app.models.service import Service, ServiceInstance
from app.models.rate_limit import RateLimitPolicy
from app.models.resilience import ResiliencePolicy

# Use an SQLite in-memory database for testing, or a separate test DB
# We define it per-test to support concurrent connections (no InterfaceError)
import uuid
from sqlalchemy.pool import StaticPool

@pytest_asyncio.fixture(scope="function", autouse=True)
async def isolated_test_env():
    import app.database.connection as db_conn
    from redis.asyncio import ConnectionPool
    from unittest.mock import AsyncMock
    import os
    
    # 1. Create fresh engine for this specific test's event loop
    db_file = f"{uuid.uuid4().hex}.db"
    test_db_url = f"sqlite+aiosqlite:///{db_file}"
    test_engine = create_async_engine(test_db_url, echo=False)
    
    # Configure the global session maker to use this engine
    original_bind = db_conn.async_session_maker.kw.get('bind')
    db_conn.async_session_maker.configure(bind=test_engine)
    
    # 2. Initialize tables in the fresh db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 3. Create fresh Redis ConnectionPool for this specific test's event loop
    pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
    original_pool = db_conn.redis_client.connection_pool
    db_conn.redis_client.connection_pool = pool
    
    await db_conn.redis_client.flushdb()
    
    # Prevent lifespan from closing the global redis client (since we share the wrapper object)
    if not isinstance(db_conn.redis_client.aclose, AsyncMock):
        db_conn.redis_client.aclose = AsyncMock()
    
    yield db_conn.async_session_maker
    
    # Teardown
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # Restore
    db_conn.async_session_maker.configure(bind=original_bind)
    db_conn.redis_client.connection_pool = original_pool

@pytest_asyncio.fixture(scope="function")
async def db_session(isolated_test_env):
    test_maker = isolated_test_env
    async with test_maker() as session:
        yield session

@pytest.fixture(scope="function")
def override_get_db(db_session):
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db_session] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def async_client(override_get_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session):
    user = User(email="test@example.com", hashed_password=get_password_hash("testpassword"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def auth_headers(async_client, test_user):
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


