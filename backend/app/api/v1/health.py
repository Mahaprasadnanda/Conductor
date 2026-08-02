from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.connection import get_db_session, get_redis

router = APIRouter()

@router.get("")
async def health_check(
    db: AsyncSession = Depends(get_db_session),
    redis=Depends(get_redis)
):
    # Check DB
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    
    # Check Redis
    redis_status = "ok"
    try:
        await redis.ping()
    except Exception:
        redis_status = "error"

    return {
        "status": "ok" if db_status == "ok" and redis_status == "ok" else "error",
        "database": db_status,
        "redis": redis_status,
    }
