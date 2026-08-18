import asyncio
from datetime import datetime, timezone
from typing import List
from app.core.logger import log
from app.services.analytics_service import AnalyticsService
from app.schemas.intelligence import Anomaly, Recommendation, IntelligenceOverview, SeverityEnum

class TrafficIntelligenceService:

    @staticmethod
    def _create_anomaly(
        anomaly_type: str,
        severity: SeverityEnum,
        current: float,
        baseline: float,
        unit: str = "",
        service_name: str = None,
        instance_id: str = None,
        explanation: str = "",
        recommendation: str = ""
    ) -> Anomaly:
        if baseline > 0:
            dev = ((current - baseline) / baseline) * 100
            deviation_str = f"+{dev:.0f}%" if dev >= 0 else f"{dev:.0f}%"
        else:
            deviation_str = "N/A"
            
        return Anomaly(
            anomaly_type=anomaly_type,
            severity=severity,
            service_name=service_name,
            instance_id=instance_id,
            current_value=round(current, 2),
            baseline_value=round(baseline, 2),
            deviation=deviation_str,
            detected_at=datetime.now(timezone.utc).isoformat(),
            explanation=explanation,
            recommendation=recommendation
        )

    @staticmethod
    def _create_recommendation(
        title: str,
        severity: SeverityEnum,
        reason: str,
        evidence: str,
        recommended_action: str,
        affected_service: str = None,
        affected_instance: str = None
    ) -> Recommendation:
        return Recommendation(
            title=title,
            severity=severity,
            reason=reason,
            evidence=evidence,
            recommended_action=recommended_action,
            affected_service=affected_service,
            affected_instance=affected_instance
        )

    @staticmethod
    async def analyze_traffic_spikes(svc_filter: str) -> List[Anomaly]:
        anomalies = []
        # Current traffic (last 5m) vs Baseline (last 1h)
        current_query = f"sum(rate(gateway_requests_total{{{svc_filter}}}[5m])) by (service_name)"
        baseline_query = f"avg_over_time(sum(rate(gateway_requests_total{{{svc_filter}}}[5m])) by (service_name)[1h:5m] offset 5m)"
        
        current_res = await AnalyticsService.query_prometheus(current_query)
        baseline_res = await AnalyticsService.query_prometheus(baseline_query)
        
        baselines = {}
        for b in baseline_res:
            svc = b.get("metric", {}).get("service_name")
            val = float(b["value"][1]) if b["value"][1] != "NaN" else 0.0
            if svc:
                baselines[svc] = val
                
        for c in current_res:
            svc = c.get("metric", {}).get("service_name")
            if not svc:
                continue
            curr = float(c["value"][1]) if c["value"][1] != "NaN" else 0.0
            base = baselines.get(svc, 0.0)
            
            # Spike if current > 1.5x baseline and current > 0.1 req/sec
            if curr > (base * 1.5) and curr > 0.1:
                sev = SeverityEnum.CRITICAL if curr > (base * 3) else SeverityEnum.WARNING
                anomalies.append(TrafficIntelligenceService._create_anomaly(
                    anomaly_type="Traffic Spike",
                    severity=sev,
                    current=curr,
                    baseline=base,
                    service_name=svc,
                    explanation=f"Traffic for {svc} is significantly higher than the 1h baseline.",
                    recommendation=f"Monitor backend capacity for {svc} and consider horizontal scaling."
                ))
        return anomalies

    @staticmethod
    async def analyze_error_spikes(svc_filter: str) -> List[Anomaly]:
        anomalies = []
        # Error rate (4xx|5xx)
        # We must protect against zero division in prometheus, but here we can just query errors and total separately
        err_curr_q = f"sum(rate(gateway_requests_total{{status_code=~'4..|5..',{svc_filter}}}[5m])) by (service_name)"
        tot_curr_q = f"sum(rate(gateway_requests_total{{{svc_filter}}}[5m])) by (service_name)"
        
        err_curr = await AnalyticsService.query_prometheus(err_curr_q)
        tot_curr = await AnalyticsService.query_prometheus(tot_curr_q)
        
        # Calculate baselines over 1h offset by 5m to avoid including the current spike
        err_base_q = f"avg_over_time(sum(rate(gateway_requests_total{{status_code=~'4..|5..',{svc_filter}}}[5m])) by (service_name)[1h:5m] offset 5m)"
        tot_base_q = f"avg_over_time(sum(rate(gateway_requests_total{{{svc_filter}}}[5m])) by (service_name)[1h:5m] offset 5m)"
        
        err_base = await AnalyticsService.query_prometheus(err_base_q)
        tot_base = await AnalyticsService.query_prometheus(tot_base_q)
        
        def to_dict(res):
            d = {}
            for r in res:
                svc = r.get("metric", {}).get("service_name")
                if svc:
                    d[svc] = float(r["value"][1]) if r["value"][1] != "NaN" else 0.0
            return d
            
        ec = to_dict(err_curr)
        tc = to_dict(tot_curr)
        eb = to_dict(err_base)
        tb = to_dict(tot_base)
        
        for svc in tc.keys():
            t_c = tc.get(svc, 0)
            e_c = ec.get(svc, 0)
            if t_c == 0:
                continue
            curr_rate = e_c / t_c
            
            t_b = tb.get(svc, 0)
            e_b = eb.get(svc, 0)
            base_rate = (e_b / t_b) if t_b > 0 else 0.0
            
            # Anomaly if current rate > baseline + 5% and current > 5%
            if curr_rate > (base_rate + 0.05) and curr_rate > 0.05:
                sev = SeverityEnum.CRITICAL if curr_rate > 0.20 else SeverityEnum.WARNING
                anomalies.append(TrafficIntelligenceService._create_anomaly(
                    anomaly_type="Error Spike",
                    severity=sev,
                    current=curr_rate * 100,
                    baseline=base_rate * 100,
                    service_name=svc,
                    explanation=f"Error rate for {svc} increased from {base_rate*100:.1f}% to {curr_rate*100:.1f}%.",
                    recommendation=f"Investigate upstream failures and check circuit breaker activity for {svc}."
                ))
        return anomalies

    @staticmethod
    async def analyze_latency_spikes(svc_filter: str) -> List[Anomaly]:
        anomalies = []
        curr_q = f"histogram_quantile(0.95, sum(rate(gateway_request_latency_seconds_bucket{{{svc_filter}}}[5m])) by (le, service_name))"
        base_q = f"avg_over_time(histogram_quantile(0.95, sum(rate(gateway_request_latency_seconds_bucket{{{svc_filter}}}[5m])) by (le, service_name))[1h:5m] offset 5m)"
        
        curr_res = await AnalyticsService.query_prometheus(curr_q)
        base_res = await AnalyticsService.query_prometheus(base_q)
        
        baselines = {}
        for b in base_res:
            svc = b.get("metric", {}).get("service_name")
            val = float(b["value"][1]) if b["value"][1] != "NaN" else 0.0
            if svc:
                baselines[svc] = val
                
        for c in curr_res:
            svc = c.get("metric", {}).get("service_name")
            if not svc:
                continue
            curr = float(c["value"][1]) if c["value"][1] != "NaN" else 0.0
            base = baselines.get(svc, 0.0)
            
            # Spike if P95 is 50% higher and > 100ms
            if curr > (base * 1.5) and curr > 0.1:
                sev = SeverityEnum.CRITICAL if curr > (base * 2.5) else SeverityEnum.WARNING
                anomalies.append(TrafficIntelligenceService._create_anomaly(
                    anomaly_type="Latency Spike",
                    severity=sev,
                    current=curr * 1000, # to ms
                    baseline=base * 1000,
                    service_name=svc,
                    explanation=f"P95 Latency for {svc} spiked to {curr*1000:.0f}ms.",
                    recommendation=f"Check backend instance health or external dependencies for {svc}."
                ))
        return anomalies

    @staticmethod
    async def analyze_rate_limits(svc_filter: str) -> List[Anomaly]:
        anomalies = []
        curr_q = f"sum(increase(gateway_rate_limit_hits_total{{{svc_filter}}}[5m])) by (service_name)"
        curr_res = await AnalyticsService.query_prometheus(curr_q)
        
        for c in curr_res:
            svc = c.get("metric", {}).get("service_name")
            if not svc:
                continue
            curr = float(c["value"][1]) if c["value"][1] != "NaN" else 0.0
            if curr > 10.0: # > 10 hits in 5m
                anomalies.append(TrafficIntelligenceService._create_anomaly(
                    anomaly_type="Rate-Limit Spike",
                    severity=SeverityEnum.WARNING,
                    current=curr,
                    baseline=0.0,
                    service_name=svc,
                    explanation=f"Rate limiting actively dropped {curr:.0f} requests for {svc} in the last 5 minutes.",
                    recommendation=f"Check if {svc} clients are retrying too aggressively."
                ))
        return anomalies

    @staticmethod
    async def analyze_circuit_breakers(svc_filter: str) -> List[Anomaly]:
        anomalies = []
        curr_q = f"max(gateway_circuit_breaker_state{{{svc_filter}}}) by (service_name)"
        curr_res = await AnalyticsService.query_prometheus(curr_q)
        
        for c in curr_res:
            svc = c.get("metric", {}).get("service_name")
            if not svc:
                continue
            state = float(c["value"][1]) if c["value"][1] != "NaN" else 0.0
            if state > 0.5: # 1.0 usually OPEN/HALF-OPEN depending on enum implementation
                state_str = "OPEN/HALF-OPEN"
                anomalies.append(TrafficIntelligenceService._create_anomaly(
                    anomaly_type="Circuit Breaker Risk",
                    severity=SeverityEnum.CRITICAL,
                    current=state,
                    baseline=0.0,
                    service_name=svc,
                    explanation=f"Circuit breaker for {svc} is in an elevated state ({state_str}).",
                    recommendation=f"Investigate immediate upstream failures causing the circuit to break for {svc}."
                ))
        return anomalies

    @staticmethod
    async def analyze_instance_imbalance(svc_filter: str) -> List[Anomaly]:
        anomalies = []
        # Calculate routing distribution
        q = f"sum(rate(gateway_lb_routing_total{{{svc_filter}}}[5m])) by (service_name, instance_id)"
        res = await AnalyticsService.query_prometheus(q)
        
        # Group by service
        svcs = {}
        for r in res:
            svc = r.get("metric", {}).get("service_name")
            inst = r.get("metric", {}).get("instance_id")
            val = float(r["value"][1]) if r["value"][1] != "NaN" else 0.0
            if svc and inst and val > 0:
                if svc not in svcs:
                    svcs[svc] = {}
                svcs[svc][inst] = val
                
        for svc, instances in svcs.items():
            if len(instances) > 1:
                total = sum(instances.values())
                if total > 0.1: # Needs some traffic
                    pcts = {k: v/total for k,v in instances.items()}
                    max_inst = max(pcts, key=pcts.get)
                    min_inst = min(pcts, key=pcts.get)
                    
                    if (pcts[max_inst] - pcts[min_inst]) > 0.2: # > 20% gap
                        anomalies.append(TrafficIntelligenceService._create_anomaly(
                            anomaly_type="Instance Imbalance",
                            severity=SeverityEnum.WARNING,
                            current=pcts[max_inst] * 100,
                            baseline=(1.0 / len(instances)) * 100,
                            service_name=svc,
                            instance_id=max_inst,
                            explanation=f"Instance {max_inst} is receiving {pcts[max_inst]*100:.1f}% of traffic (imbalanced).",
                            recommendation=f"Review load-balancer weights or instance health for {svc}."
                        ))
        return anomalies

    @staticmethod
    async def generate_overview(db, project_id: int) -> IntelligenceOverview:
        services = await AnalyticsService.get_project_services(db, project_id)
        if not services:
            return IntelligenceOverview(
                status="HEALTHY",
                active_anomaly_count=0,
                recent_anomalies=[],
                recommendations=[]
            )

        svc_id_regex = "|".join([str(s["id"]) for s in services])
        svc_filter = f'service_id=~"{svc_id_regex}"'

        anomalies = []
        try:
            results = await asyncio.gather(
                TrafficIntelligenceService.analyze_traffic_spikes(svc_filter),
                TrafficIntelligenceService.analyze_error_spikes(svc_filter),
                TrafficIntelligenceService.analyze_latency_spikes(svc_filter),
                TrafficIntelligenceService.analyze_rate_limits(svc_filter),
                TrafficIntelligenceService.analyze_circuit_breakers(svc_filter),
                TrafficIntelligenceService.analyze_instance_imbalance(svc_filter),
                return_exceptions=True
            )
            for res in results:
                if isinstance(res, list):
                    anomalies.extend(res)
                else:
                    log.error("intelligence_analysis_error", error=str(res))
        except Exception as e:
            log.error("intelligence_overview_error", error=str(e))

        # Build deterministic recommendations
        recs = []
        for a in anomalies:
            recs.append(TrafficIntelligenceService._create_recommendation(
                title=f"{a.anomaly_type} Resolution",
                severity=a.severity,
                reason=a.explanation,
                evidence=f"Current: {a.current_value}, Baseline: {a.baseline_value}, Dev: {a.deviation}",
                recommended_action=a.recommendation,
                affected_service=a.service_name,
                affected_instance=a.instance_id
            ))
            
        # Deduplicate recommendations by title + service
        unique_recs = {f"{r.title}-{r.affected_service}": r for r in recs}.values()

        # Determine status
        status = "HEALTHY"
        if any(a.severity == SeverityEnum.CRITICAL for a in anomalies):
            status = "CRITICAL"
        elif len(anomalies) > 0:
            status = "DEGRADED"

        # Sort anomalies by severity and time
        def sev_score(s):
            if s == SeverityEnum.CRITICAL: return 0
            if s == SeverityEnum.WARNING: return 1
            return 2
            
        sorted_anomalies = sorted(anomalies, key=lambda x: (sev_score(x.severity), x.anomaly_type))

        return IntelligenceOverview(
            status=status,
            active_anomaly_count=len(sorted_anomalies),
            recent_anomalies=sorted_anomalies,
            recommendations=list(unique_recs)
        )
