import asyncio
from sqlalchemy import select
from app.models.rate_limit import RateLimitPolicy, RateLimitAlgorithm
from app.models.service import Service
from app.database.connection import async_session_maker

async def main():
  async with async_session_maker() as db:
    res = await db.execute(select(Service).where(Service.service_name=='texas'))
    svc = res.scalars().first()
    if not svc:
      print('No texas svc')
      return
    res = await db.execute(select(RateLimitPolicy).where(RateLimitPolicy.service_id==svc.id))
    rl = res.scalars().first()
    if not rl:
      print('Creating new rate limit for texas')
      rl = RateLimitPolicy(service_id=svc.id, limit=5, window_seconds=60, algorithm=RateLimitAlgorithm.FIXED_WINDOW)
      db.add(rl)
      await db.commit()
    else:
      print('Updating existing rate limit for texas')
      rl.limit = 5
      rl.window_seconds = 60
      await db.commit()
    print('Done!')

asyncio.run(main())
