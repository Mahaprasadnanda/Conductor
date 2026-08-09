import httpx
import json
from datetime import datetime, timezone, timedelta
from app.database.connection import redis_client
from app.core.logger import log

PROMETHEUS_URL = "http://prometheus:9090"

class AnalyticsService:
    @staticmethod
    async def query_prometheus(query: str) -> dict:
        """Execute an instant query against Prometheus."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
                res.raise_for_status()
                return res.json().get("data", {}).get("result", [])
        except Exception as e:
            log.error("prometheus_query_error", query=query, error=str(e))
            return []

    @staticmethod
    async def query_prometheus_range(query: str, start: str, end: str, step: str) -> dict:
        """Execute a range query against Prometheus."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query_range", 
                    params={"query": query, "start": start, "end": end, "step": step}
                )
                res.raise_for_status()
                return res.json().get("data", {}).get("result", [])
        except Exception as e:
            log.error("prometheus_query_range_error", query=query, error=str(e))
            return []

    @staticmethod
    def get_time_params(time_range: str) -> tuple[str, str, str]:
        """Convert a time range string (e.g. '5m', '1h') to start, end, step."""
        end_time = datetime.now(timezone.utc)
        
        minutes_map = {
            "5m": (5, "15s"),
            "15m": (15, "30s"),
            "1h": (60, "1m"),
            "6h": (360, "5m"),
            "24h": (1440, "15m")
        }
        
        mins, step = minutes_map.get(time_range, (60, "1m"))
        start_time = end_time - timedelta(minutes=mins)
        
        # Prometheus API expects unix timestamp (seconds)
        return str(start_time.timestamp()), str(end_time.timestamp()), step

    @staticmethod
    async def get_overview() -> dict:
        # Fetch overview stats
        active_conns = await AnalyticsService.query_prometheus("sum(gateway_active_connections)")
        healthy_instances = await AnalyticsService.query_prometheus("gateway_instances_registered")
        services_registered = await AnalyticsService.query_prometheus("gateway_services_registered")
        requests_total = await AnalyticsService.query_prometheus("sum(gateway_requests_total)")
        req_sec = await AnalyticsService.query_prometheus("sum(rate(gateway_requests_total[5m]))")
        error_rate = await AnalyticsService.query_prometheus(
            "sum(rate(gateway_requests_total{status_code=~'4..|5..'}[5m])) / sum(rate(gateway_requests_total[5m]))"
        )
        p95_latency = await AnalyticsService.query_prometheus(
            "histogram_quantile(0.95, sum(rate(gateway_request_latency_seconds_bucket[5m])) by (le))"
        )
        
        def extract_val(res, default=0.0):
            if res and len(res) > 0 and len(res[0].get("value", [])) > 1:
                val = res[0]["value"][1]
                if val == "NaN":
                    return default
                return float(val)
            return default

        return {
            "active_connections": extract_val(active_conns),
            "healthy_instances": extract_val(healthy_instances),
            "healthy_services": extract_val(services_registered), # Simplify mapping
            "total_requests": extract_val(requests_total),
            "requests_per_second": round(extract_val(req_sec), 2),
            "error_rate": round(extract_val(error_rate) * 100, 2), # percentage
            "p95_latency": round(extract_val(p95_latency), 4)
        }

    @staticmethod
    async def get_timeseries(time_range: str = "1h", service_name: str = None) -> dict:
        start, end, step = AnalyticsService.get_time_params(time_range)
        
        # Ensure we use a rate window large enough to cover the step. We use max(5m, step) effectively, 
        # but 5m is a good safe minimum for short intervals.
        rate_window = "5m"
        if time_range == "24h":
            rate_window = "15m"
            
        service_filter = f'{{service_name="{service_name}"}}' if service_name else ""
        
        traffic_query = f"sum(rate(gateway_requests_total{service_filter}[{rate_window}]))"
        p50_query = f"histogram_quantile(0.50, sum(rate(gateway_request_latency_seconds_bucket{service_filter}[{rate_window}])) by (le))"
        p95_query = f"histogram_quantile(0.95, sum(rate(gateway_request_latency_seconds_bucket{service_filter}[{rate_window}])) by (le))"
        
        # In PromQL if service_name is used, we need proper filter: 
        status_err_filter = f'status_code=~"4..|5..",service_name="{service_name}"' if service_name else 'status_code=~"4..|5.."'
        error_query = f"sum(rate(gateway_requests_total{{{status_err_filter}}}[{rate_window}]))"

        traffic_res = await AnalyticsService.query_prometheus_range(traffic_query, start, end, step)
        p50_res = await AnalyticsService.query_prometheus_range(p50_query, start, end, step)
        p95_res = await AnalyticsService.query_prometheus_range(p95_query, start, end, step)
        error_res = await AnalyticsService.query_prometheus_range(error_query, start, end, step)

        def map_series(res):
            if res and len(res) > 0:
                # Format: [ [unix_time, "value"], ... ]
                return [{"timestamp": r[0], "value": float(r[1]) if r[1] != "NaN" else 0.0} for r in res[0].get("values", [])]
            return []

        return {
            "traffic": map_series(traffic_res),
            "p50_latency": map_series(p50_res),
            "p95_latency": map_series(p95_res),
            "error_rate": map_series(error_res)
        }

    @staticmethod
    async def get_recent_requests(limit: int = 50) -> list:
        try:
            items = await redis_client.lrange("gateway:recent_requests", 0, limit - 1)
            return [json.loads(i) for i in items]
        except Exception:
            return []

    @staticmethod
    async def get_recent_errors(limit: int = 50) -> list:
        try:
            items = await redis_client.lrange("gateway:recent_errors", 0, limit - 1)
            return [json.loads(i) for i in items]
        except Exception:
            return []
