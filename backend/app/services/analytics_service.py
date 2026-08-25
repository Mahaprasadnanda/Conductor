import httpx
import json
import os
from datetime import datetime, timezone, timedelta
from app.database.connection import redis_client
from app.core.logger import log

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
GRAFANA_CLOUD_USERNAME = os.getenv("GRAFANA_CLOUD_USERNAME")
GRAFANA_CLOUD_API_KEY = os.getenv("GRAFANA_CLOUD_API_KEY")

class AnalyticsService:
    @staticmethod
    def _get_auth():
        if GRAFANA_CLOUD_USERNAME and GRAFANA_CLOUD_API_KEY:
            return httpx.BasicAuth(username=GRAFANA_CLOUD_USERNAME, password=GRAFANA_CLOUD_API_KEY)
        return None

    @staticmethod
    async def query_prometheus(query: str) -> dict:
        """Execute an instant query against Prometheus."""
        try:
            async with httpx.AsyncClient(timeout=3.0, auth=AnalyticsService._get_auth()) as client:
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
            async with httpx.AsyncClient(timeout=3.0, auth=AnalyticsService._get_auth()) as client:
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
    async def get_project_services(db, project_id: int) -> list[dict]:
        from sqlalchemy.future import select
        from app.models.service import Service
        res = await db.execute(select(Service.id, Service.service_name).where(Service.project_id == project_id))
        return [{"id": row.id, "service_name": row.service_name} for row in res.all()]

    @staticmethod
    async def get_overview(db, project_id: int, time_range: str = "1h", service_name: str = None) -> dict:
        from sqlalchemy.future import select
        from app.models.service import Service, ServiceInstance, ServiceStatus
        
        # Count healthy services belonging to the project
        res_svc = await db.execute(select(Service).where(Service.project_id == project_id))
        services = res_svc.scalars().all()
        
        if service_name:
            services = [s for s in services if s.service_name == service_name]
            
        healthy_services_count = len([s for s in services if s.status == ServiceStatus.HEALTHY])
        
        service_ids = [s.id for s in services]
        
        # Count healthy instances belonging to these services
        if service_ids:
            res_inst = await db.execute(
                select(ServiceInstance)
                .where(ServiceInstance.service_id.in_(service_ids))
                .where(ServiceInstance.status == ServiceStatus.HEALTHY)
            )
            instances = res_inst.scalars().all()
            healthy_instances_count = len(instances)
            
            # Add implicit instances for external services (base_url configured)
            # that are HEALTHY but have no explicit ServiceInstance records.
            for service in services:
                if service.status == ServiceStatus.HEALTHY and service.base_url:
                    has_instances = any(inst.service_id == service.id for inst in instances)
                    if not has_instances:
                        healthy_instances_count += 1
        else:
            healthy_instances_count = 0
            
        if not service_ids:
            return {
                "active_connections": 0.0,
                "healthy_instances": 0.0,
                "healthy_services": 0.0,
                "total_requests": 0.0,
                "requests_per_second": 0.0,
                "error_rate": 0.0,
                "p95_latency": 0.0
            }

        svc_id_regex = "|".join([str(sid) for sid in service_ids])
        svc_filter = f'project_id="{project_id}",service_id=~"{svc_id_regex}"'

        # Fetch overview stats scoped to the project
        active_conns = await AnalyticsService.query_prometheus(f"sum(gateway_active_connections{{{svc_filter}}})")
        requests_total = await AnalyticsService.query_prometheus(f"sum(increase(gateway_requests_total{{{svc_filter}}}[{time_range}]))")
        req_sec = await AnalyticsService.query_prometheus(f"sum(rate(gateway_requests_total{{{svc_filter}}}[{time_range}]))")
        error_rate = await AnalyticsService.query_prometheus(
            f"sum(rate(gateway_requests_total{{status_code=~'5..',{svc_filter}}}[{time_range}])) / sum(rate(gateway_requests_total{{{svc_filter}}}[{time_range}]))"
        )
        p95_latency = await AnalyticsService.query_prometheus(
            f"histogram_quantile(0.95, sum(rate(gateway_request_latency_seconds_bucket{{{svc_filter}}}[{time_range}])) by (le))"
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
            "healthy_instances": float(healthy_instances_count),
            "healthy_services": float(healthy_services_count),
            "total_requests": extract_val(requests_total),
            "requests_per_second": round(extract_val(req_sec), 2),
            "error_rate": round(extract_val(error_rate) * 100, 2), # percentage
            "p95_latency": round(extract_val(p95_latency), 4)
        }

    @staticmethod
    async def get_timeseries(db, project_id: int, time_range: str = "1h", service_name: str = None) -> dict:
        services = await AnalyticsService.get_project_services(db, project_id)
        if not services:
            return {"traffic": [], "p50_latency": [], "p95_latency": [], "error_rate": []}
            
        service_names = [s["service_name"] for s in services]
        
        if service_name:
            if service_name not in service_names:
                return {"traffic": [], "p50_latency": [], "p95_latency": [], "error_rate": []}
            # Find the ID for this specific service name
            specific_id = next((s["id"] for s in services if s["service_name"] == service_name), None)
            svc_filter_str = f'project_id="{project_id}",service_id="{specific_id}"'
        else:
            svc_id_regex = "|".join([str(s["id"]) for s in services])
            svc_filter_str = f'project_id="{project_id}",service_id=~"{svc_id_regex}"'

        start, end, step = AnalyticsService.get_time_params(time_range)
        
        # Ensure we use a rate window large enough to cover the step. We use max(5m, step) effectively, 
        # but 5m is a good safe minimum for short intervals.
        rate_window = "5m"
        if time_range == "24h":
            rate_window = "15m"
            
        traffic_query = f"sum(rate(gateway_requests_total{{{svc_filter_str}}}[{rate_window}]))"
        p50_query = f"histogram_quantile(0.50, sum(rate(gateway_request_latency_seconds_bucket{{{svc_filter_str}}}[{rate_window}])) by (le))"
        p95_query = f"histogram_quantile(0.95, sum(rate(gateway_request_latency_seconds_bucket{{{svc_filter_str}}}[{rate_window}])) by (le))"
        
        # In PromQL if service_name is used, we need proper filter: 
        status_err_filter = f'status_code=~"5..",{svc_filter_str}'
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
    async def get_recent_requests(db, project_id: int, limit: int = 50) -> list:
        services = await AnalyticsService.get_project_services(db, project_id)
        if not services:
            return []
        try:
            items = await redis_client.lrange("gateway:recent_requests", 0, 200)
            parsed = [json.loads(i) for i in items]
            filtered = [req for req in parsed if req.get("project_id") == project_id]
            return filtered[:limit]
        except Exception as e:
            log.error("recent_requests_fetch_error", project_id=project_id, error=str(e))
            return []

    @staticmethod
    async def get_recent_errors(db, project_id: int, limit: int = 50) -> list:
        services = await AnalyticsService.get_project_services(db, project_id)
        if not services:
            return []
        try:
            items = await redis_client.lrange("gateway:recent_errors", 0, 200)
            parsed = [json.loads(i) for i in items]
            filtered = [err for err in parsed if err.get("project_id") == project_id]
            return filtered[:limit]
        except Exception as e:
            log.error("recent_errors_fetch_error", project_id=project_id, error=str(e))
            return []
