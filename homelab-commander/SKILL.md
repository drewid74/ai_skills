---
name: homelab-commander
description: >-
  Universal homelab infrastructure specialist. Docker self-hosting, TrueNAS ZFS
  operations, Proxmox VM/LXC management, K3s Kubernetes with FluxCD, 3-2-1
  backup strategy, blue-green deployments, internal DNS (Pi-hole/Technitium),
  VLAN design, Home Assistant + MQTT, and cross-platform migration planning.
triggers:
  - "set up homelab service stack"
  - "deploy Docker Compose with TrueNAS"
  - "configure Proxmox or K3s"
  - "plan 3-2-1 backup strategy"
  - "migrate between Docker and K3s"
  - "set up internal DNS split-horizon"
  - "design home automation with Home Assistant"
  - "troubleshoot homelab networking or storage"
  - "generate network topology diagram"
tags: [homelab, docker, proxmox, k3s, truenas, zfs, backup, dns, vlan, home-assistant, mqtt]
author: next-gen
---

# Homelab Commander

## Identity

Production-grade homelab specialist. Always explain WHY behind patterns. Pin image tags, use soft NFS mounts, implement 3-2-1 backup before declaring any service "deployed." Every service gets a healthcheck and reverse proxy TLS.

## Stack Defaults

| Layer | Default | Notes |
|-------|---------|-------|
| Containers | Docker Compose + Dockge UI | Pin tags, no `:latest` |
| Hypervisor | Proxmox | VMs for Windows/full-OS; LXC for Linux density |
| Kubernetes | K3s + FluxCD | Lightweight GitOps |
| Storage | TrueNAS Scale + ZFS | NFS v4 exports per dataset |
| NFS options | `vers=4,soft,timeo=180,bg,tcp` | Soft = no hang if NAS down |
| Reverse proxy | Traefik v3 | Label-based routing, auto TLS |
| DNS | Pi-hole + Technitium | Split-horizon, wildcard records |
| Backup | 3-2-1 rule | 3 copies, 2 media types, 1 offsite |
| Secrets | `.env` git-ignored | Or Docker secrets / Sealed Secrets |

## Decision Framework

```
IF deploying new service:
  → Pin image tag (semver)
  → Bind data volume to TrueNAS NFS dataset
  → Add healthcheck
  → Add Traefik labels + TLS
  → Add Uptime Kuma monitor

IF choosing VM vs LXC:
  → VM: Windows, GPU passthrough, full OS, kernel differences
  → LXC: Linux microservices, K3s nodes, maximize density

IF adding storage:
  → One TrueNAS dataset per service (independent snapshot/quota)
  → Mount: vers=4,soft,timeo=180,bg,tcp

IF backup:
  → Snapshots: 7 daily, 4 weekly, 12 monthly (ZFS)
  → Replicate to local USB (weekly rotation)
  → Offsite: S3 GLACIER monthly
  → Test restore monthly — untested backups don't exist

IF migrating Docker → K3s:
  → Export data first (safety)
  → kompose convert to generate Kubernetes manifests
  → Add PVC for NFS storage
  → Deploy alongside, verify data, cutover traffic, monitor
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| `:latest` image tags | Pinned semantic version (e.g., `v1.2.3`) |
| Hard NFS mounts | `soft,timeo=180,bg` — prevents system hang on NAS disconnect |
| NFSv3 | `vers=4` — stronger security and performance |
| Secrets in compose YAML | `.env` (git-ignored) or Docker secrets |
| No healthcheck | `healthcheck: test: [CMD, curl, -f, http://localhost/health]` |
| No backup | 3-2-1 before first production traffic |
| Containers on host root disk | Bind to TrueNAS NFS datasets |

## Quality Gates

- [ ] All image tags pinned (no `:latest`)
- [ ] All persistent data on TrueNAS NFS (not container layer)
- [ ] Healthchecks defined for critical services
- [ ] Traefik routes with TLS (`certresolver: letsencrypt`)
- [ ] 3-2-1 backup implemented and restore tested
- [ ] Uptime Kuma monitoring all public-facing services
- [ ] DNS records in Pi-hole for all internal services

→ See `truenas-ops` for ZFS CLI, TrueNAS API automation  
→ See `proxmox-k3s-infra` for VM templates, GPU passthrough, FluxCD GitOps  
→ See `docker-selfhost` for base compose networking patterns  
→ See `deploy-pipeline` for deploy + ZFS snapshot + health check + rollback scripts

---

## I. Docker Compose Template

```yaml
version: '3.8'

services:
  app:
    image: myapp:v1.2.3          # Never :latest
    container_name: myapp
    restart: unless-stopped
    environment:
      DB_HOST: db
      DB_PASS: ${DB_PASS}        # From .env (git-ignored)
    volumes:
      - /mnt/nas/myapp:/app/data
      - /etc/localtime:/etc/localtime:ro
    networks:
      - internal
      - web
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      traefik.enable: "true"
      traefik.http.routers.myapp.rule: "Host(`myapp.home.local`)"
      traefik.http.routers.myapp.tls.certresolver: "letsencrypt"
      traefik.http.services.myapp.loadbalancer.server.port: "8080"

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      retries: 5

volumes:
  db_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=<NAS_IP>,vers=4,soft,timeo=180,bg,tcp
      device: ":/<POOL>/docker/db_data"

networks:
  internal:
    driver: bridge
  web:
    external: true
```

## II. TrueNAS NFS Mounts

```bash
# Mount NFS (soft — critical for system stability)
mkdir -p /mnt/nas/docker/{myapp,postgres,media}
mount -t nfs -o vers=4,soft,timeo=180,bg,tcp <NAS_IP>:/<POOL>/docker /mnt/nas/docker

# Persist in /etc/fstab:
<NAS_IP>:/<POOL>/docker /mnt/nas/docker nfs vers=4,soft,timeo=180,bg,tcp 0 0
```

## III. Dataset Hierarchy

```
<POOL_NAME>
├── docker/
│   ├── app_data/
│   ├── postgres_data/
│   └── media_data/
├── home/
│   ├── photos/
│   └── documents/
└── backup/
    ├── external_usb/
    └── remote_replica/
```

Each dataset has independent snapshot schedule, quota, and ACLs.

## IV. 3-2-1 Backup

```bash
# Snapshot schedule (cron)
0 2 * * *   zfs snapshot -r tank@daily_$(date +\%Y\%m\%d)
0 3 * * 0   zfs snapshot -r tank@weekly_$(date +\%Y\%m\%d)

# Expire old snapshots
zfs destroy -r tank@daily_20260320

# Offsite to S3 GLACIER
SNAP="backup_$(date +%Y%m%d)"
zfs snapshot tank/docker@$SNAP
zfs send tank/docker@$SNAP | gzip > /tmp/$SNAP.zfs.gz
aws s3 cp /tmp/$SNAP.zfs.gz s3://my-backups/homelab/ \
  --sse=AES256 --storage-class=GLACIER
rm /tmp/$SNAP.zfs.gz
```

### Monthly Restore Test

```bash
zfs recv tank_restore < /backup/latest.zfs
# Verify data
psql -h localhost -U postgres -d testdb -c "SELECT COUNT(*) FROM users;"
# Compare checksum to known-good baseline
pg_dump testdb | sha256sum > /tmp/restored.txt
diff /tmp/restored.txt /root/prod_baseline.txt && echo "PASS" || echo "FAIL"
```

## V. Proxmox VM vs LXC

| Aspect | VM | LXC |
|--------|-----|-----|
| Boot time | 30–60s | 1–2s |
| Overhead | Full OS | Shared kernel |
| Isolation | Hypervisor boundary | Process-level |
| Use case | Windows, GPU, testing | Linux services, K3s nodes |

```bash
# Create Docker host VM from template
qm clone 100 201 --name docker-node-01 --full
qm set 201 --cores 8 --memory 16384 --net0 virtio,bridge=vmbr0
qm start 201
ssh root@<VM_IP>
curl -fsSL https://get.docker.com | sh
```

## VI. K3s + FluxCD GitOps

```bash
# Install K3s control plane
curl -sfL https://get.k3s.io | sh -

# Add worker nodes
curl -sfL https://get.k3s.io | \
  K3S_URL=https://<CONTROL_PLANE_IP>:6443 \
  K3S_TOKEN=<TOKEN> sh -

# Bootstrap FluxCD
flux bootstrap github \
  --owner=<GITHUB_USER> \
  --repository=homelab-gitops \
  --branch=main \
  --path=clusters/k3s-homelab \
  --personal
```

## VII. Internal DNS

```bash
# Pi-hole in Docker
docker run -d --name pihole \
  -p 53:53/udp -p 53:53/tcp \
  -e TZ=America/Chicago \
  -e WEBPASSWORD=${PIHOLE_PASS} \
  -v pihole_dnsmasq:/etc/dnsmasq.d \
  -v pihole_config:/etc/pihole \
  pihole/pihole:latest
```

**Pi-hole UI → Settings → Local DNS:** Add `*.home.local → <REVERSE_PROXY_IP>` (wildcard)

**Split-horizon:** Internal: `app.example.com → 192.168.1.50` | External: `app.example.com → <PUBLIC_IP>`

## VIII. VLAN Design

```
VLAN 100: Management (Proxmox, NAS, switches) — default-deny inbound
VLAN 200: Docker/Apps (services containers)   — controlled access
VLAN 300: IoT (sensors, smart devices)        — no LAN access, DNS+time only
VLAN 400: Guest                               — internet only
```

```bash
# Proxmox VLAN-aware bridge (/etc/network/interfaces)
auto vmbr0
iface vmbr0 inet static
  address <MGMT_IP>/24
  bridge-ports eno1
  bridge-stp off
  bridge-vlan-aware yes
  bridge-vids 2-4094

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1

# UFW inter-VLAN rules (allow App VLAN → Management)
ufw route allow in on vmbr0.200 out on vmbr0.100 \
  from 192.168.200.0/24 to 192.168.100.0/24
```

## IX. Home Automation: HA + MQTT + ESPHome

```yaml
services:
  mqtt:
    image: eclipse-mosquitto:2
    restart: unless-stopped
    ports: ["1883:1883", "9001:9001"]
    volumes:
      - mosquitto_data:/mosquitto/data
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf

  homeassistant:
    image: homeassistant/home-assistant:latest
    restart: unless-stopped
    environment:
      TZ: America/Chicago
    volumes:
      - ha_data:/config
      - /etc/localtime:/etc/localtime:ro
    ports: ["8123:8123"]
    depends_on: [mqtt]
```

**ESPHome** (YAML-driven firmware for ESP32): auto-generates HA device discovery, no C++ required.

**Automation pattern (temperature-based fan):**
```yaml
automation:
  - alias: "Fan on hot"
    trigger:
      platform: numeric_state
      entity_id: sensor.living_room_temperature
      above: 24
    action:
      service: switch.turn_on
      entity_id: switch.living_room_fan
```

## X. Blue-Green Deployment

```bash
#!/bin/bash
# Run green stack, smoke test, switch Traefik, keep blue for rollback
GREEN_PORT=8081
docker-compose -f docker-compose.green.yml -p myapp_green up -d

# Wait for green healthy
for i in {1..30}; do
  curl -sf "http://localhost:$GREEN_PORT/health" && break || sleep 2
done

# Run smoke tests
npm run smoke-test -- "http://localhost:$GREEN_PORT" || {
  docker-compose -f docker-compose.green.yml -p myapp_green down
  exit 1
}

# Cutover (update Traefik backend label)
sed -i "s/server.port: .*/server.port: $GREEN_PORT/" docker-compose.green.yml
docker-compose -f docker-compose.green.yml -p myapp_green up -d

echo "Green live. Blue available 30min for rollback."
sleep 1800
docker-compose -f docker-compose.blue.yml -p myapp_blue down
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Container fails, "permission denied" | Wrong UID on NFS share | Set `user: <PUID>:<PGID>`; match TrueNAS share ACL |
| NFS mount hangs system | Hard mount | Always use `soft,timeo=180,bg` |
| OOM Killed | Insufficient memory | Add `--memory=2g`; check `docker stats` |
| K3s node NotReady | CNI plugin missing | `helm install cilium cilium/cilium` |
| Proxmox high I/O wait | Storage bottleneck | Move to SSD; `zpool status` for health |
| ZFS space full | Too many old snapshots | `zfs destroy -r tank@daily_YYYYMMDD` |
| S3 sync fails | Expired credentials | `aws sts get-caller-identity`; refresh token |
| Pi-hole not resolving | Upstream DNS down | Set fallback: Settings → DNS → Custom upstream |
