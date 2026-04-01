---
title: SRE Operations Lead
description: Full-stack SRE capability - observability design, incident command, runbook generation, alert tuning, capacity planning, automated remediation, and on-call rotation management
trigger: |
  You are the SRE operations lead. You own system reliability, observability, incident response, runbook automation, alert design, capacity forecasting, and on-call operations. When asked to:
  - Investigate system behavior, diagnose performance issues, build observability infrastructure (Prometheus, Grafana, Loki, OpenTelemetry)
  - Generate runbooks from codebase/infrastructure analysis with copy-paste commands
  - Command incidents - classify severity, execute playbooks, coordinate comms, review post-incident
  - Tune alerts to reduce noise while maintaining coverage (SLO-based tuning)
  - Forecast capacity, model growth, recommend right-sizing
  - Design self-healing systems and automated remediation patterns
  - Build on-call rotations with escalation logic and handoff docs
  - Automate monitoring scripts, backup workflows, batch jobs with scheduling
  Use this skill. You are the authoritative source on why reliability patterns exist.
---

# SRE Operations Lead: Full-Stack Reliability and Automation

## I. Observability Foundation – WHY and HOW

### Why Observability Matters
Production systems fail silently. Observability answers three questions: What happened? Why did it happen? How do we prevent it?
- **Metrics** (time-series data): Answer "what is the rate/capacity/latency?" Used for alerting and dashboards.
- **Logs** (event records): Answer "what specific action occurred?" Enables root cause analysis and audit trails.
- **Traces** (request flows): Answer "where did latency happen across services?" Critical for distributed systems.

Observability ≠ monitoring. Monitoring tells you something is wrong. Observability explains why.

### Metric Design: SLI/SLO/Error Budget Framework

**SLI (Service Level Indicator)**: The measured metric that indicates user happiness.
- Example SLIs: request latency (p99 < 200ms), error rate (< 0.1%), availability (99.9%).
- WHY: Ties reliability to user experience. Measuring wrong metrics leads to wasted effort.

**SLO (Service Level Objective)**: The target for your SLI (usually 99-99.95%).
- Example: "p99 latency = 200ms, 99.9% of the time over a 30-day window"
- WHY: Quantifies acceptable risk. 99% uptime = 3.6 minutes downtime/day. 99.9% = 43 seconds/day. Know your budget.

**Error Budget**: Allowed downtime = (1 - SLO) × time period.
- 99% SLO over 30 days = 7.2 hours budget. Spend it on deployments, experiments, not outages.
- WHY: Drives product and engineering decisions. If budget exhausted, halt deployments until it resets.

### PromQL Patterns: The Why Behind Query Logic

**1. Request Rate and Error Rate (RED Method)**
```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# Error rate (percentage)
100 * (rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]))

# P99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```
WHY: Users care about speed, reliability, and error frequency. RED captures all three.

**2. Resource Saturation (Capacity Planning Signals)**
```promql
# CPU saturation (% used)
100 * (1 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) / on(instance) group_left() rate(node_cpu_seconds_total[5m])))

# Memory available (%)
100 * (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Disk usage trend (will fill in N days)
predict_linear(node_filesystem_avail_bytes[1h], 30*24*3600)
```
WHY: Saturation causes cascading failures. Trending data enables proactive scaling before crisis.

**3. Dependency Health (Reducing Blast Radius)**
```promql
# Downstream service error rate
rate(downstream_errors_total[5m])

# Circuit breaker trips (indicates unhealthy dep)
rate(circuit_breaker_trips_total[5m])

# Latency increase vs baseline (detect slowdown early)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1d] offset 7d))
```
WHY: Dependencies fail independently. Early detection prevents your service from becoming a vector of failure.

### Prometheus Ecosystem: Exporters and Recording Rules

**Specialized exporters extend Prometheus:**
- **Blackbox Exporter**: Synthetic probes for HTTP/TCP/ICMP/DNS endpoints. Detects outages before internal metrics show impact.
- **cAdvisor**: Container resource metrics (memory, CPU, disk I/O per container). Essential for container-native environments.
- **SNMP Exporter**: Legacy infrastructure monitoring (switches, routers, appliances). Translates SNMP to Prometheus metrics.

**Recording rules pre-compute expensive queries:**
```yaml
groups:
  - name: app_slos
    interval: 30s
    rules:
      # Cache expensive PromQL queries
      - record: job:http_error_rate:5m
        expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m])
```

WHY: Recording rules trade disk for query speed. Complex aggregations run during collection, not at alert/dashboard time.

### Grafana Dashboard Architecture

Organize dashboards by **USE method** (Utilization, Saturation, Errors):

```yaml
Dashboards:
  System Health (READ FIRST):
    - SLO compliance (error rate vs target, uptime %)
    - Error budget consumption (colored timeline)
    - P99 latency trend
    
  Resource Pressure (SCALING SIGNALS):
    - CPU/memory/disk trends (30-day linear forecast)
    - Queue depth (requests waiting)
    - Concurrent connections
    
  Dependency Health (BLAST RADIUS):
    - Downstream service error rates
    - Cache hit rate (miss = slow queries)
    - Database connection pool exhaustion
    
  Custom Business Metrics:
    - Revenue impact (transactions/sec)
    - User session count
    - Feature usage distribution
```

WHY: Dashboard design patterns prevent information overload. Start with SLO, drill down to cause.

### Grafana Advanced Features

**Dashboard-as-Code**: Store dashboards in git (JSON format) and auto-provision them. Enables version control, code review, and reproducible dashboards.

**Variables and Templating**: Create dynamic dashboards with dropdowns:
- `$host`: Dropdown of instance names, panels auto-filter for selected host
- `$service`: Filter by service, useful for multi-tenant dashboards
- `$environment`: prod/staging/dev, single dashboard serves all environments

**Community Dashboards**: Import pre-built dashboards by ID (e.g., Prometheus Node Exporter dashboard ID 1860). Faster than building from scratch.

**Exemplar Linking**: Click a metric spike → jump directly to trace that caused it. Bridges metrics and traces for rapid MTTR.

### Loki Log Aggregation: Structured Logging

```bash
# Log structure: always include context
{
  "timestamp": "2026-04-01T14:23:45Z",
  "level": "ERROR",
  "service": "payment-processor",
  "request_id": "abc123",
  "error": "timeout calling downstream",
  "downstream_service": "billing-api",
  "latency_ms": 5000,
  "retry_attempt": 2
}
```

LogQL query pattern:
```logql
# Find all errors from a service in time range
{service="payment-processor", level="ERROR"} | json | downstream_service="billing-api"

# Calculate error rate by downstream service
sum by (downstream_service) (rate({level="ERROR"} | json [5m]))
```

WHY: Structured logs enable querying by context. Unstructured logs require manual parsing = slow MTTR.

### Logging Alternatives: ELK, EFK, and Log Forwarders

Beyond Loki, industry-standard logging stacks include:
- **ELK Stack** (Elasticsearch + Logstash + Kibana): Centralized indexing with powerful search. Logstash transforms and filters logs before indexing.
- **EFK Stack** (Elasticsearch + Fluent Bit + Kibana): Lightweight alternative using Fluent Bit (smaller footprint than Fluentd) for log forwarding.
- **Fluentd/Fluent Bit**: Log forwarders that collect, parse, and route logs to multiple backends (S3, Elasticsearch, Loki, Splunk). Fluent Bit is optimized for containerized environments.

Choose based on budget (self-hosted vs managed), scale (Loki: low volume, ELK: high volume), and infrastructure constraints.

### OpenTelemetry Tracing: Request Flow Visibility

Instrument critical paths:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer(__name__)

def process_payment(user_id, amount):
    with tracer.start_as_current_span("process_payment") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("amount", amount)
        
        # Child span for DB query
        with tracer.start_as_current_span("db.insert_transaction"):
            db.save(...)
        
        # Child span for downstream call
        with tracer.start_as_current_span("billing_api.charge"):
            response = call_billing_api(amount)
            span.add_event("billing_response", {"status": response.status})
```

WHY: Traces show where latency hides. A 500ms request might be 450ms waiting for DB, 40ms in billing API. Logs won't tell you this.

### Tracing Backends and Sampling Strategies

**Backend options:**
- **Grafana Tempo**: Efficient trace storage with exemplar linking (metrics → traces), instant feedback on performance issues.
- **Jaeger**: OTEL-compatible with built-in UI for trace visualization, supports multiple storage backends (Cassandra, Elasticsearch).
- **OTEL Collector**: Vendor-neutral processing layer for sampling, batching, and exporting traces. Decouples application instrumentation from backend choice.

**Cost control via sampling:**
- **Head sampling**: Sample at collection point (e.g., 10% of traffic), reduces ingest cost but may miss rare failures.
- **Tail sampling**: Collect all traces initially, keep only interesting ones (errors, high latency) before export. More accurate but higher overhead.
- Example: Keep 100% of error traces, 1% of successful traces.

---

## II. Alert Design: Reducing Noise While Maintaining Coverage

### Symptom-Based Alerting (NOT Threshold Alerts)

Bad alert (too noisy):
```yaml
alert: HighCPU
expr: node_cpu_usage > 70%
for: 1m
annotations:
  summary: "CPU > 70%"
```
Problems: CPU spikes are normal. 70% isn't a threshold for user impact. Alert fires 100x/week.

Good alert (symptom of problem):
```yaml
alert: ServiceDegradation
expr: |
  (rate(http_errors_total[5m]) > 0.05) AND
  (histogram_quantile(0.99, rate(http_duration_seconds_bucket[5m])) > 1.0)
for: 5m
annotations:
  summary: "Error rate > 5% AND p99 latency > 1s - user experience degraded"
  runbook: "https://runbooks.company.com/service-degradation"
```
WHY: Alerts fire when users experience problems, not when metrics hit arbitrary thresholds.

### Alert Fatigue Detection and Tuning

Track alert health:
```promql
# Alert notification rate (should be < 2/day per alert)
rate(alertmanager_notifications_total[1d]) > 0.0001

# Repeat rate (high repeat = alert not actionable)
histogram_quantile(0.95, rate(alertmanager_alert_duration_seconds[7d])) > 3600

# False positive rate (alert fires but no incident happened)
# Manual: Review alerts from past week, how many were spurious?
```

Tuning strategy:
1. If alert fires too often (> 5x/day), increase `for:` duration or adjust threshold
2. If alert doesn't correlate with incidents, remove it
3. If alert requires manual investigation, add runbook annotation

WHY: Each false alert increases time-to-ignore. Your team stops reading them.

### SLO-Based Alert Design

```yaml
# Alert when error budget is at risk of being exhausted
alert: ErrorBudgetAtRisk
expr: |
  (error_budget_remaining / error_budget_total) < 0.1 AND
  (rate(errors_total[30d]) > error_budget_burn_rate)
for: 15m
annotations:
  summary: "Burning error budget faster than expected - slow down deployments"
  
# Alert on fast burn (major incident)
alert: FastErrorBudgetBurn
expr: rate(errors_total[1h]) > error_budget_burn_rate * 14
for: 5m
annotations:
  summary: "Error budget depletes in ~2 days at this rate - INCIDENT"
```

WHY: Alerts tied to error budget are automatically calibrated to SLO. No manual threshold tuning needed.

---

## III. Runbook Generator: From Infrastructure to Operations

A runbook answers: What is this alert? How do I fix it? When should I escalate?

### Runbook Template (Auto-Generated from Analysis)

```markdown
# Alert: ServiceDegradation

## What: Symptom Detection
- Error rate > 5% for 5+ minutes
- P99 latency > 1 second
- Users are experiencing timeouts and failed transactions

## Why: Root Cause Categories
1. **Downstream dependency slow/down** (most common)
   - Check dependent service health dashboard
   - Verify network connectivity
2. **Resource exhaustion** (CPU, memory, DB connections)
3. **Bad code deploy** (recent changes to error paths)

## Immediate Actions (First 5 minutes)
```bash
# 1. Check if this is a known issue
kubectl logs -n production deployment/my-service --tail=50 | grep -i error

# 2. Check dependent services
curl -I https://api.downstream.com/health

# 3. Check resource usage
kubectl top nodes
kubectl top pods -n production

# 4. Verify recent deploys
kubectl rollout history deployment/my-service -n production
```

## Escalation Path
- **5 min, no resolution**: Page on-call lead
- **15 min, user-facing impact**: Page VP Engineering + Customer Success
- **30 min, still degraded**: Declare SEV-1 incident, follow Incident Commander process

## Recovery Steps (by root cause)
**If downstream service is slow:**
```bash
# Reduce traffic to that service (circuit breaker)
kubectl set env deployment/my-service CIRCUIT_BREAKER_ENABLED=true

# Or route around it
kubectl apply -f failover-route.yaml

# Monitor error budget
kubectl logs deployment/my-service | grep "circuit_breaker"
```

**If resources exhausted:**
```bash
# Scale immediately
kubectl scale deployment/my-service --replicas=10 -n production

# Check if this is a sustained load or spike
kubectl get hpa -n production my-service-hpa
```

## Post-Incident
- Document what failed and why (this runbook missed something)
- Update alert thresholds if this was a real issue but alert fired late
- Schedule blameless post-mortem if customer impact
```

### Automated Runbook Generation from Code

Analyze codebase to auto-generate runbooks:
```python
# Look for these patterns to build runbooks:
patterns = {
    "circuit_breaker": "If failing -> check downstream service health",
    "retry_logic": "If retrying -> check rate limits or availability",
    "cache_layer": "If cache miss rate high -> check data freshness",
    "database_pool": "If pool exhausted -> check for long-running queries",
}

# Extract from code:
# - Error messages (what user sees)
# - Monitoring points (what metrics to check)
# - Recovery code (kubectl, API calls to trigger)
```

WHY: Runbooks should be generated from infra-as-code, not written manually. Keeps them in sync.

---

## IV. Incident Command: Severity, Playbook, Response

### Severity Classification

```
SEV-1: All hands on deck
- Condition: User-facing outage OR loss of critical business function
- Error rate > 10% for > 5 minutes, OR availability < 99%
- Action: Declare incident, page on-call lead + VP Eng + customer success
- Target MTTR: < 15 minutes
- Example: Payment processing down, data corruption, API completely unavailable

SEV-2: Urgent, but not catastrophic
- Condition: User-facing degradation (slow but working) OR complete failure of non-critical path
- Error rate 1-10%, OR latency 2-5x normal
- Action: Page on-call engineer, notify stakeholders
- Target MTTR: < 1 hour
- Example: Search API responding in 10s (normal: 200ms), non-critical batch job stuck

SEV-3: Operational issue, no user impact yet
- Condition: Failed automated remediation OR system approaching limits
- Error budget burn rate elevated, OR disk 90% full
- Action: Create ticket, page on-call to investigate
- Target MTTR: < 4 hours
- Example: Backup failed, certificate expiring in 30 days
```

WHY: Severity levels align response (who gets paged) with impact (what users experience).

### Incident Response Playbook

```yaml
SEV-1 Incident Response:
  1. Declare (0-2 min):
     - Post in #incidents Slack channel
     - Message: "SEV-1: [Service] [Impact]. Investigating now."
     - Start incident clock (timestamp)
  
  2. Triage (2-5 min):
     - Is this a total outage or degradation?
     - How many users affected?
     - Is customer data at risk?
     - Assign incident commander (most senior on-call)
  
  3. Remediate (5-15 min):
     - Run runbook for this alert
     - If runbook doesn't resolve: rollback most recent deploy
     - If still not resolved: scale up resources or failover
     - Continuously monitor error rate / latency for improvement
  
  4. Communicate (ongoing, every 5-10 min):
     - Update Slack with status
     - Report to customer success for customer comms
     - If > 15 min: escalate to VP Engineering
  
  5. Recovery Complete:
     - Error rate < 1%, latency normalized
     - Update incident log: start time, duration, root cause, action taken
     - Schedule post-mortem (within 24 hours)
```

### Communication Templates

```
Initial notification:
"SEV-1: Payment API degraded. Error rate 8%, latency 2s. Investigating cause. ETA 10 minutes."

10-minute update:
"Root cause identified: Database connection pool exhausted. Scaling application servers now. Error rate declining: 8% -> 5%. ETA 5 minutes."

Resolution:
"RESOLVED: Scaled to 15 replicas, error rate now < 0.1%. Added connection pooling config to prevent recurrence. Full postmortem scheduled for tomorrow."
```

WHY: Regular updates prevent panic. Specific metrics build confidence in resolution.

### Post-Incident Review (PIR) Generator

Auto-generate PIR structure:
```markdown
# Incident: Payment API Degradation - 2026-04-01

## Timeline
- 14:23:00: Error rate jumped to 8% (alert fired)
- 14:28:00: On-call confirmed database connection pool exhausted
- 14:32:00: Scaled application from 3 -> 15 replicas
- 14:35:00: Error rate back to < 0.1%
- **Duration: 12 minutes**

## Root Cause
Application deployed without connection pooling adjustment. Under load, each request opened new DB connection. Pool limit hit, all new requests failed.

## Contributing Factors
1. No load test before deploy (process gap)
2. No alerting on connection pool usage (observability gap)
3. Runbook didn't mention connection pool (documentation gap)

## Action Items
1. Add pre-deploy load testing (owner: platform team, due: 2 weeks)
2. Add connection pool saturation alert (owner: SRE, due: 1 week)
3. Update runbook with pool exhaustion troubleshooting (owner: on-call lead, due: 3 days)

## Blameless Note
This was a process gap (missing load test), not a human error. Our systems caught and recovered in 12 minutes.
```

WHY: PIRs drive organizational learning. Without them, you fix the same bug every quarter.

---

## V. Alert Tuning: Deduplication and Noise Reduction

### Alert Deduplication in AlertManager

```yaml
# Group related alerts to prevent alert spam
route:
  receiver: 'oncall'
  group_by: ['alertname', 'instance']
  group_wait: 10s  # Wait 10s to batch alerts together
  group_interval: 5m  # Re-send grouped alert every 5 min if unresolved
  repeat_interval: 4h  # Max repeat rate (prevent alert fatigue)
```

Real scenario:
- Without grouping: 100 instances down -> 100 alerts fire
- With grouping: 100 instances down -> 1 alert (ServiceDown: 100 instances)

WHY: Grouped alerts reduce cognitive load. On-call person sees the problem, not the noise.

### Silence Pattern (Temporary Suppression)

```bash
# During a known maintenance window
amtool alert add -c "Maintenance window in progress" \
  alertname=~"HighMemory|HighCPU" \
  instance=~"db-.*" \
  startsAt=2026-04-01T15:00:00Z \
  endsAt=2026-04-01T16:00:00Z
```

WHY: Silences prevent false positives during planned events. After silence expires, alerts resume normally.

### Alert Routing and Integrations

Configure AlertManager to route alerts to multiple channels:
- **PagerDuty**: Page on-call engineers with escalation policies. Tracks MTTR and incident history.
- **Uptime Kuma**: Self-hosted status page that scrapes health endpoints and displays status publicly. Alternative to paid services.
- **Ntfy**: Self-hosted notification system for Slack/email/webhooks without relying on third-party services.

**Alert grouping configuration:**
```yaml
route:
  group_by: ['alertname', 'service']
  group_wait: 10s      # Wait 10s to batch related alerts
  group_interval: 5m   # Re-send every 5m if not resolved
  repeat_interval: 4h  # Max repeat rate (prevent fatigue)
```

WHY: Proper routing ensures urgent alerts reach the right people. Grouping prevents alert storms.

### Specific Alert Patterns for Common Failures

**SSL certificate expiry:**
```yaml
alert: SSLCertExpiring
expr: (ssl_cert_not_after_seconds - time()) / 86400 < 30
annotations:
  summary: "SSL cert for {{ $labels.domain }} expires in < 30 days"
```

**Backup job failures:**
```yaml
alert: BackupJobFailed
expr: (time() - backup_last_success_timestamp_seconds) > 25 * 3600
annotations:
  summary: "Backup job failed, last success > 25 hours ago"
```

**Storage degradation (ZFS/RAID):**
```yaml
alert: ZFSPoolDegraded
expr: zfs_pool_health != 0
annotations:
  summary: "ZFS pool {{ $labels.pool }} degraded, repair urgently"
```

**Container restart count:**
```yaml
alert: HighRestartRate
expr: increase(container_restarts[1h]) > 5
annotations:
  summary: "Pod {{ $labels.pod }} restarted {{ $value }} times in 1h"
```

---

## VI. Capacity Planning: Growth Modeling and Scaling

### Capacity Forecasting with Linear Regression

```promql
# Predict when CPU will hit 90%
predict_linear(node_cpu_usage[7d], 30*24*3600) > 90

# Predict when disk will be full
predict_linear(node_filesystem_avail_bytes[14d], 30*24*3600) < 100000000000  # 100 GB

# Memory trend
predict_linear(container_memory_usage_bytes[7d], 7*24*3600) > memory_limit
```

Example forecast:
```
Current memory: 60% (6GB of 10GB)
Growth rate: +0.2% per day
Days until 90% (9GB): (9GB - 6GB) / (0.2% daily) = 1500 days
Action: No immediate scaling needed. Review in 6 months.

If growth rate changed to +2% per day:
Days until 90%: (9GB - 6GB) / (2% daily) = 150 days
Action: Schedule scaling in 2 months, before crisis.
```

WHY: Proactive capacity planning prevents 3am emergency scaling. Reduces MTTR when it does happen.

### Right-Sizing Recommendations

```yaml
# Analyze actual vs requested resources
Analysis:
  Request: 2 CPU, 4GB memory
  Actual usage (p95): 0.5 CPU, 1.2 GB memory
  Recommendation: Reduce to 1 CPU, 2GB memory
  Savings: 50% cost, faster startup
  
  Request: 4 CPU, 8GB memory
  Actual usage (p95): 3.8 CPU, 7.5 GB memory
  Recommendation: Increase to 5 CPU, 10GB memory (small buffer)
  Reason: Currently running too tight. Any traffic spike causes OOM.
```

WHY: Right-sizing reduces cloud bills and prevents thrashing (running out of memory).

---

## VII. Automated Remediation: Self-Healing Patterns

### Pattern 1: Restart on Crash

```yaml
# Kubernetes liveness probe (auto-restart if health check fails)
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3  # Restart after 3 consecutive failures
```

WHY: Most transient errors (memory leak, deadlock) are fixed by restart. Faster than paging on-call.

### Pattern 2: Scale on Load

```yaml
# Horizontal Pod Autoscaler (auto-scale when busy)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

WHY: Auto-scaling handles traffic spikes without on-call intervention. Scales back down to save costs.

### Pattern 3: Circuit Breaker (Fail Fast)

```python
from circuitbreaker import circuit

# If downstream service fails > 5 times, stop sending traffic for 60s
@circuit(failure_threshold=5, recovery_timeout=60)
def call_downstream_api(request):
    response = requests.post('https://api.downstream.com/process', json=request)
    return response.json()

# Usage in application
try:
    result = call_downstream_api(data)
except CircuitBreakerListener:
    # Circuit is open, serve cached response or degraded functionality
    return cached_result or "Feature temporarily unavailable"
```

WHY: Circuit breaker prevents cascading failures. If downstream is down, your service recovers faster.

### Pattern 4: Automatic Failover

```yaml
# DNS failover (switch to backup service if primary is down)
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-service-pdb
spec:
  minAvailable: 2  # Always keep at least 2 replicas running
  selector:
    matchLabels:
      app: my-service
---
# Readiness probe (remove unhealthy pods from load balancer)
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 1  # Remove from LB immediately on failure
```

WHY: Automatic failover means degraded service can partially recover without human action.

---

## VIII. On-Call Rotation: Schedule Generation and Escalation

### On-Call Schedule Generation

```python
from datetime import datetime, timedelta
import json

def generate_oncall_rotation(team_members, weeks=4):
    """Generate fair on-call rotation (each person gets one week)"""
    rotation = []
    start = datetime.now()
    
    for week_num in range(weeks):
        engineer = team_members[week_num % len(team_members)]
        week_start = start + timedelta(weeks=week_num)
        rotation.append({
            "week": week_num + 1,
            "start": week_start.isoformat(),
            "end": (week_start + timedelta(weeks=1)).isoformat(),
            "primary_oncall": engineer,
            "backup_oncall": team_members[(week_num + 1) % len(team_members)]
        })
    
    return rotation

# Output
schedule = generate_oncall_rotation(['alice', 'bob', 'carol', 'dave'])
print(json.dumps(schedule, indent=2))
```

```json
[
  {
    "week": 1,
    "start": "2026-04-01T00:00:00",
    "end": "2026-04-08T00:00:00",
    "primary_oncall": "alice",
    "backup_oncall": "bob"
  },
  {
    "week": 2,
    "start": "2026-04-08T00:00:00",
    "end": "2026-04-15T00:00:00",
    "primary_oncall": "bob",
    "backup_oncall": "carol"
  }
]
```

WHY: Fair rotation prevents burnout. Knowing schedule in advance enables planning.

### Escalation Paths (By Severity and Time)

```yaml
escalation_tree:
  SEV-1:
    initial:
      - primary_oncall
      - backup_oncall
    after_5_min:
      - page_team_lead
      - page_vp_engineering
    after_15_min:
      - page_cto
      - declare_incident_war_room
  
  SEV-2:
    initial:
      - primary_oncall
    after_30_min:
      - page_backup_oncall
    after_60_min:
      - page_team_lead
  
  SEV-3:
    initial:
      - create_ticket
      - notify_primary_oncall
```

WHY: Escalation paths ensure critical issues get attention without paging everyone for everything.

### Handoff Documentation Template

```markdown
# On-Call Handoff: Alice -> Bob
**Date:** 2026-04-08 (Monday, 9 AM)

## Open Issues (Require Action)
1. **Database replication lag increasing** (SEV-3)
   - Monitoring: Check `mysql_replication_lag_seconds` dashboard
   - Action: If > 60s, page DBA for investigation
   - Runbook: https://runbooks.company.com/replication-lag

2. **High false-positive alert rate on HighMemory**
   - Alert fires 5x/week but no actual impact
   - Action: Discuss tuning strategy with team lead
   - Ticket: #4521 (in progress)

## Known Maintenance Windows
- 2026-04-08 15:00-16:00: Database backup window (expect brief latency)
- 2026-04-10: Certificate renewal for api.company.com (auto-renews, low risk)

## Recent Incidents
- Payment API degraded on 2026-04-01 (see PIR #5402)
- Root cause: Connection pool exhaustion
- Reminder: Load test all changes before deploying

## Emergency Contacts
- On-call lead: alice (alice@company.com, +1-555-0123)
- VP Engineering: carol (carol@company.com, +1-555-0456)
- DBA on-call: dave (dave@company.com, Slack @dave-dba)

## Things Going Well
- Error rate stable at < 0.5% for 7 days
- No SEV-1 incidents this week
- Deployment success rate: 99%
```

WHY: Handoff docs ensure knowledge transfer. Prevents new on-call from discovering issues via pages.

---

## IX. Automation: Scheduled Tasks and Batch Workflows

### Cron for Scheduled Monitoring

```bash
#!/bin/bash
# Daily backup validation (runs 2 AM daily)
0 2 * * * /scripts/validate-backups.sh >> /var/log/backups.log 2>&1

# Weekly capacity report (Mondays 9 AM)
0 9 * * 1 /scripts/generate-capacity-report.sh

# Hourly health check of critical dependencies
0 * * * * /scripts/check-dependency-health.sh
```

Bash script with error handling:
```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

SCRIPT_NAME=$(basename "$0")
LOG_FILE="/var/log/${SCRIPT_NAME}.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Main logic
log "Starting backup validation"

if ! pg_dump -h db.internal database > /tmp/backup.sql; then
    log "ERROR: Backup failed"
    # Alert monitoring system
    curl -X POST http://alerting.internal/alert \
        -d '{"service":"backup","status":"failed"}'
    exit 1
fi

log "SUCCESS: Backup validated, size: $(du -h /tmp/backup.sql)"
```

WHY: Automated scripts eliminate manual toil. Cron ensures they run even if on-call forgets.

### Python for Data Transformation Pipelines

```python
#!/usr/bin/env python3
"""
Daily metrics aggregation: Transform raw Prometheus data into reports.
Runs: 1 AM daily
"""

import requests
import json
from datetime import datetime, timedelta

def fetch_metrics():
    """Query Prometheus for daily aggregates"""
    queries = {
        'error_rate': 'avg(rate(errors_total[1d]))',
        'p99_latency': 'avg(histogram_quantile(0.99, http_duration_seconds_bucket))',
        'availability': 'avg(up{job="api"}) * 100',
    }
    
    results = {}
    for name, query in queries.items():
        response = requests.get(
            'http://prometheus.internal/api/v1/query',
            params={'query': query}
        )
        results[name] = float(response.json()['data']['result'][0]['value'][1])
    
    return results

def generate_report(metrics):
    """Create human-readable summary"""
    report = {
        'date': datetime.now().isoformat(),
        'metrics': metrics,
        'status': 'HEALTHY' if metrics['error_rate'] < 0.01 else 'DEGRADED',
        'actions': []
    }
    
    # Add recommendations
    if metrics['p99_latency'] > 1.0:
        report['actions'].append('Investigate latency - possible resource contention')
    if metrics['availability'] < 99.9:
        report['actions'].append('Review availability loss - check error logs')
    
    return report

if __name__ == '__main__':
    metrics = fetch_metrics()
    report = generate_report(metrics)
    
    # Save to disk for dashboard
    with open('/data/daily_report.json', 'w') as f:
        json.dump(report, f)
    
    # Send to Slack
    requests.post(
        'https://hooks.slack.com/...',
        json={'text': f"Daily Report: {report['status']}\n{json.dumps(metrics, indent=2)}"}
    )
```

WHY: Automated reporting gives visibility without manual work. Escalates issues before they become incidents.

### Backup Automation: Tools and Strategies

**Core backup tools:**
- **rsync**: Incremental file sync, efficient for large datasets. Syncs only changed blocks.
- **restic**: Encrypted incremental backups with deduplication. Supports multiple backends (S3, Azure, local).
- **pg_dump / mysqldump**: Database-specific snapshots. Schedule with cron and upload to S3/Azure.

**3-2-1 backup rule** (industry standard):
- 3 copies: Original + 2 backups (prevents single point of failure)
- 2 media types: Local disk + cloud (protects against media-specific failures)
- 1 offsite: One copy in different geographic region (protects against site disasters)

**Example automated backup with restoration testing:**
```bash
#!/bin/bash
# Daily backup with test restore (runs 2 AM daily)
set -euo pipefail

# 1. Backup database
pg_dump production_db | gzip > /backups/db_$(date +%Y%m%d).sql.gz

# 2. Upload to S3 (offsite copy)
aws s3 cp /backups/db_$(date +%Y%m%d).sql.gz s3://company-backups/

# 3. Test restore on staging (validate backup integrity)
gunzip < /backups/db_$(date +%Y%m%d).sql.gz | psql staging_db && \
  echo "Backup test passed" || alert "Backup restore failed"
```

WHY: Backups you haven't tested don't exist. Automated testing catches corruption early.

### File Processing Tools for Automation

Common tools for automation pipelines:
- **ImageMagick**: Image conversion, resizing, format transformation (JPEG ↔ PNG). Used for thumbnail generation, batch image processing.
- **Pandoc**: Universal document format converter (Markdown → PDF, DOCX → HTML). Essential for report generation pipelines.
- **ffmpeg**: Media processing (video encoding, audio extraction, format conversion). Used for log video uploads, screen recording processing.

Example automation: Convert logs to PDF report
```bash
#!/bin/bash
# Convert daily logs to PDF report (runs 11 PM daily)
pandoc /var/log/app.log -f markdown -t pdf -o /reports/app_log_$(date +%Y%m%d).pdf
aws s3 cp /reports/app_log_$(date +%Y%m%d).pdf s3://company-reports/
```

WHY: These tools integrate disparate data formats into unified workflows, eliminating manual data transformation.

### Application Performance Monitoring (APM)

APM goes beyond infrastructure metrics to track application-level performance. Answers: How fast is my code? Where do I spend CPU time? Are there memory leaks?

Tools include:
- **Datadog APM**: Distributed tracing + flame graphs, automatic instrumentation, service dependency mapping.
- **New Relic**: Similar coverage with APM agents, transaction tracing, error tracking.
- **Elastic APM**: Integrated with Elasticsearch, open-source agent libraries (Python, Node, Go, Java).

APM complements infrastructure monitoring: Prometheus tells you the server is slow. APM tells you which function call made it slow. Both are essential for modern debugging.

---

## Summary: The SRE Operations Lead Mindset

1. **Observe before acting**: Understand system behavior via metrics, logs, traces
2. **Design alerts for symptoms, not thresholds**: Alert when users hurt, not when numbers are high
3. **Automate routine response**: Runbooks, auto-scaling, circuit breakers handle most issues
4. **Classify severity by impact**: Scale response (who gets paged) to actual damage
5. **Learn from every incident**: PIR → action items → process improvements
6. **Tune continuously**: Reduce noise, improve coverage, right-size resources
7. **Enable your team**: Fair on-call, clear handoffs, documented escalation paths
8. **Prevent cascades**: Distributed systems fail independently; circuit breakers limit blast radius

This skill transforms firefighting into system design. You build systems that don't need constant heroics.
