# Grafana Provisioning Patterns

Code-first provisioning. No UI clicks. `allowUiUpdates: false` always set.

---

## Pattern 1 — Docker Compose + Provisioning YAMLs (default)

```yaml
# docker-compose.yml — monitoring stack
# Requires: .env file with variables from .env.example
services:
  grafana:
    image: grafana/grafana:11.0.0
    volumes:
      - ./provisioning:/etc/grafana/provisioning:ro
      - ./dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH: /var/lib/grafana/dashboards/overview/home.json
      GF_AUTH_ANONYMOUS_ENABLED: "false"
    ports: ["3000:3000"]
    networks: [monitoring]
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.53.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./rules:/etc/prometheus/rules:ro
      - ./targets:/etc/prometheus/targets:ro
      - prometheus_data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=${PROMETHEUS_RETENTION:-90d}
      - --storage.tsdb.allow-overlapping-blocks
      - --web.enable-lifecycle        # enables POST /-/reload
      - --web.enable-admin-api
    ports: ["9090:9090"]
    networks: [monitoring]
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:v0.27.0
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    ports: ["9093:9093"]
    networks: [monitoring]
    restart: unless-stopped

  pushgateway:
    image: prom/pushgateway:v1.9.0
    ports: ["9091:9091"]
    networks: [monitoring]
    restart: unless-stopped

  blackbox-exporter:
    image: prom/blackbox-exporter:v0.25.0
    volumes:
      - ./blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    ports: ["9115:9115"]
    networks: [monitoring]
    restart: unless-stopped

volumes:
  grafana_data:
  prometheus_data:

networks:
  monitoring:
    enable_ipv6: false
```

```yaml
# provisioning/datasources/datasources.yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "15s"
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo

  - name: Loki
    type: loki
    uid: loki
    url: http://loki:3100
    editable: false
    jsonData:
      derivedFields:
        - matcherRegex: "traceID=(\\w+)"
          name: TraceID
          url: "${__value.raw}"
          datasourceUid: tempo

  - name: Tempo
    type: tempo
    uid: tempo
    url: http://tempo:3200
    editable: false
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
      tracesToMetrics:
        datasourceUid: prometheus
      serviceMap:
        datasourceUid: prometheus
```

```yaml
# provisioning/dashboards/default.yaml
apiVersion: 1
providers:
  - name: default
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false       # UI edits silently discarded — git is source of truth
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true  # subfolder name = Grafana folder name
```

---

## Pattern 2 — Grafana HTTP API (idempotent import)

```bash
# Import or overwrite a dashboard — safe to re-run in CI
GRAFANA_URL=http://<GRAFANA_HOST>:3000
GRAFANA_TOKEN=${GRAFANA_API_TOKEN}

curl -sf -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
  "${GRAFANA_URL}/api/dashboards/db" \
  -d @- <<EOF
{
  "dashboard": $(cat dashboards/node-overview.json),
  "folderId": 0,
  "overwrite": true,
  "message": "ci:$(git rev-parse --short HEAD)"
}
EOF

# Provision datasource via API
curl -sf -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
  "${GRAFANA_URL}/api/datasources" \
  -d '{
    "name":"Prometheus","type":"prometheus",
    "url":"http://<PROMETHEUS_HOST>:9090","access":"proxy","isDefault":true
  }'

# Hot-reload Prometheus config (no restart required)
curl -sf -X POST http://<PROMETHEUS_HOST>:9090/-/reload
```

---

## Pattern 3 — Grizzly CLI Deploy

```bash
# Install
go install github.com/grafana/grizzly/cmd/grr@latest

export GRAFANA_URL=http://<GRAFANA_HOST>:3000
export GRAFANA_TOKEN=${GRAFANA_API_TOKEN}

grr apply monitoring/            # deploy all resources
grr diff  monitoring/            # preview changes before apply
grr pull  Dashboard/uid-here     # pull existing UI dashboard to code
```

```yaml
# monitoring/dashboards/node-overview.yaml (Grizzly format)
apiVersion: grizzly.grafana.com/v1alpha1
kind: Dashboard
metadata:
  name: node-overview
  folder: Infrastructure
spec:
  title: Node Overview
  uid: node-overview
  panels: []   # paste full Grafana JSON panels array here
```

---

## Pattern 4 — Terraform grafana Provider

```hcl
# variables.tf
variable "grafana_url"           { type = string }
variable "grafana_service_token" { type = string, sensitive = true }
variable "prometheus_url"        { type = string, default = "http://prometheus:9090" }

terraform {
  required_providers {
    grafana = { source = "grafana/grafana", version = "~> 3.0" }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_service_token
}

resource "grafana_folder" "ai_monitoring" {
  title = "AI Monitoring"
}

resource "grafana_dashboard" "inference" {
  folder      = grafana_folder.ai_monitoring.id
  config_json = file("${path.module}/dashboards/inference-overview.json")
  overwrite   = true
  message     = "terraform apply"
}

resource "grafana_data_source" "prometheus" {
  type       = "prometheus"
  name       = "Prometheus"
  url        = var.prometheus_url
  is_default = true
  json_data_encoded = jsonencode({
    timeInterval = "15s"
    exemplarTraceIdDestinations = [
      { name = "traceID", datasourceUid = "tempo" }
    ]
  })
}
```
