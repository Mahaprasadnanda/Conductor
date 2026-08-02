from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis
from app.config.settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_db_session():
    async with async_session_maker() as session:
        yield session

def get_redis():
    return redis_client
