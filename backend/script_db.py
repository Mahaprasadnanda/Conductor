import asyncio
from app.database.connection import async_session_maker
from sqlalchemy import text

async def query():
    async with async_session_maker() as db:
        res = await db.execute(text('SELECT id, service_name, project_id, status FROM services'))
        print('Services:', res.all())

asyncio.run(query())
