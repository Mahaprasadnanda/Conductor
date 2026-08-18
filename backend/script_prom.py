import asyncio
from app.services.analytics_service import AnalyticsService
async def query():
    res = await AnalyticsService.query_prometheus('gateway_request_latency_seconds_bucket')
    print(res)
asyncio.run(query())
