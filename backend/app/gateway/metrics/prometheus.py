from prometheus_client import Counter, Histogram, Gauge

class PrometheusManager:
    # Counters
    gateway_requests_total = Counter(
        "gateway_requests_total",
        "Total requests processed by the gateway",
        ["project_id", "service_name", "service_id", "method", "status_code"]
    )
    
    gateway_lb_routing_total = Counter(
        "gateway_lb_routing_total",
        "Total requests routed to a specific instance",
        ["project_id", "service_name", "service_id", "instance_id", "strategy"]
    )
    
    gateway_rate_limit_hits_total = Counter(
        "gateway_rate_limit_hits_total",
        "Total requests rejected by rate limiting",
        ["project_id", "service_name", "service_id"]
    )
    
    gateway_retries_total = Counter(
        "gateway_retries_total",
        "Total number of request retries",
        ["project_id", "service_name", "service_id"]
    )
    
    gateway_proxy_errors_total = Counter(
        "gateway_proxy_errors_total",
        "Total number of proxy errors",
        ["project_id", "service_name", "service_id", "error_type"]
    )
    
    # Histograms
    gateway_request_latency_seconds = Histogram(
        "gateway_request_latency_seconds",
        "Total latency of the request including gateway overhead",
        ["project_id", "service_name", "service_id"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0]
    )
    
    gateway_upstream_latency_seconds = Histogram(
        "gateway_upstream_latency_seconds",
        "Latency of the upstream service excluding gateway overhead",
        ["project_id", "service_name", "service_id"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0]
    )
    
    gateway_middleware_execution_seconds = Histogram(
        "gateway_middleware_execution_seconds",
        "Execution time of specific gateway middlewares",
        ["middleware_name"],
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
    )
    
    # Gauges
    gateway_active_connections = Gauge(
        "gateway_active_connections",
        "Active connections currently held by instances",
        ["project_id", "service_name", "service_id", "instance_id"]
    )
    
    gateway_circuit_breaker_state = Gauge(
        "gateway_circuit_breaker_state",
        "State of the circuit breaker (0=CLOSED, 1=HALF_OPEN, 2=OPEN)",
        ["project_id", "service_name", "service_id"]
    )
    
    gateway_inflight_requests = Gauge(
        "gateway_inflight_requests",
        "Number of requests currently inflight within the gateway"
    )
    
    gateway_services_registered = Gauge(
        "gateway_services_registered",
        "Current number of registered services"
    )
    
    gateway_instances_registered = Gauge(
        "gateway_instances_registered",
        "Current number of healthy service instances"
    )

prometheus_manager = PrometheusManager()
