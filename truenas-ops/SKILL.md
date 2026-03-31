---
name: truenas-ops
description: "Use this skill whenever the user wants to manage, configure, troubleshoot, or automate anything on TrueNAS SCALE or CORE. Triggers include: any mention of 'TrueNAS', 'SCALE', 'CORE', 'ZFS', 'zpool', 'dataset', 'snapshot', 'replication', 'scrub', 'smart test', 'jail', 'plugin', 'NAS API', 'middleware', 'TrueNAS app', 'ix-applications', 'storage pool', 'SMB share', 'NFS export', 'iSCSI', 'rsync task', 'cloud sync', 'TrueNAS migration', 'backup NAS', 'NAS audit', or any reference to network-attached storage administration. Also use when the user is deploying Docker containers on TrueNAS SCALE 24.10+, managing datasets or permissions for containerized services, writing shell scripts that interact with TrueNAS APIs, or planning a migration between TrueNAS instances. If someone mentions 'my NAS' or 'home server storage' in a context that implies ZFS or TrueNAS, use this skill."
---

# TrueNAS Operations

## Overview

This skill helps you manage TrueNAS SCALE and CORE systems: administer storage pools and datasets, deploy containerized workloads, automate tasks via the REST API, replicate data, and troubleshoot common issues. TrueNAS provides enterprise-grade ZFS storage with web-based management, making it ideal for self-hosted services, backup targets, and network-attached storage.

## TrueNAS API Patterns

**Base URL and Authentication**

All API calls use the REST API at `http://<NAS_IP>/api/v2.0/`. Authenticate with a Bearer token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer <API_KEY>" http://<NAS_IP>/api/v2.0/system/info
```

Generate an API key in the UI: Settings > API Keys > Create.

**Common Endpoints**

- `GET /system/info` – system status, version, uptime
- `GET /pool` – list pools with usage
- `GET /dataset` – list datasets with properties
- `GET /sharing/smb` – SMB share configuration
- `POST /sharing/smb` – create SMB share
- `GET /container` – list containers (SCALE 24.10+)
- `GET /service` – service status (ssh, nfs, smb, etc.)

**Python Example**

```python
import requests

API_KEY = "<API_KEY>"
NAS_IP = "<NAS_IP>"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Check pool usage
response = requests.get(f"http://{NAS_IP}/api/v2.0/pool", headers=headers)
pools = response.json()
for pool in pools:
    print(f"{pool['name']}: {pool['allocated']} / {pool['size']}")
```

## ZFS Operations

**Pool Status**

Check pool health and degradation:

```bash
zpool status <POOL_NAME>
zpool list -v  # verbose allocation view
```

Why: Identifies failing drives, resilver activity, and vdev state before they become critical.

**Dataset Creation for Containers**

Create datasets with PUID/PGID-aware permissions:

```bash
zfs create -o mountpoint=/mnt/<POOL>/<DATASET> \
  -o aclmode=passthrough -o aclinherit=passthrough \
  <POOL>/<DATASET>
chown <PUID>:<PGID> /mnt/<POOL>/<DATASET>
chmod 750 /mnt/<POOL>/<DATASET>
```

Why: Containers run as non-root users; separate permissions prevent privilege escalation and data leakage.

**Snapshot Management**

Create automated snapshots with consistent naming:

```bash
zfs snapshot <POOL>/<DATASET>@$(date +%Y%m%d_%H%M%S)
zfs list -t snapshot  # list all snapshots
zfs rollback <POOL>/<DATASET>@<SNAP_NAME>  # restore to snapshot
```

Automate via cron:

```bash
0 2 * * * zfs snapshot <POOL>/<DATASET>@nightly_$(date +\%Y\%m\%d)
```

Why: Snapshots enable recovery from accidental deletion or corruption; naming by date aids retention policy enforcement.

**Scrub Scheduling**

Run monthly scrubs to verify data integrity:

```bash
zpool scrub <POOL_NAME>
zpool status | grep -i scrub  # monitor progress
```

Schedule via UI: Storage > Scrub Tasks > Add. Why: Detects silent data corruption before it spreads.

## Dataset Best Practices

**Layout Pattern for Self-Hosted Services**

Separate datasets per stack to isolate data and enable granular snapshots:

```
<POOL>
├── docker/
│   ├── stacks/  (bind mounts to individual stacks)
│   └── images/  (Docker image storage)
├── data/
│   ├── nextcloud/
│   ├── postgres/
│   └── media/
└── backups/
```

Why: Granular datasets allow independent snapshot/replication policies and simplify migration.

**Permission Model**

Use POSIX mode with ACLs for clarity:

```bash
zfs set aclmode=passthrough acltype=posixacl <POOL>/<DATASET>
```

Avoid common pitfall: Do NOT use root-owned directories for container bind mounts. Set explicit PUID/PGID ownership.

**Compression and Record Size**

Tailor settings to workload:

```bash
# Databases: smaller record size, fast compression
zfs set recordsize=16K compression=lz4 <POOL>/postgres

# Media storage: large record size, high compression
zfs set recordsize=1M compression=zstd <POOL>/media

# General purpose: balanced defaults
zfs set recordsize=128K compression=lz4 <POOL>/general
```

Why: Record size impacts I/O pattern efficiency; compression saves space and bandwidth but costs CPU.

## Docker Compose on SCALE 24.10+

**Stack Directory Convention**

Store docker-compose files in datasets:

```
/mnt/<POOL>/stacks/<stack-name>/
├── docker-compose.yml
├── .env                    # secrets (restrict permissions to 0600)
└── data/                   # separate dataset for persistent volumes
```

**Bind Mount Patterns**

Reference datasets in compose:

```yaml
services:
  app:
    image: myapp:latest
    volumes:
      - /mnt/<POOL>/data/app:/app/data:rw
    environment:
      - PUID=1000
      - PGID=1000
    user: "1000:1000"
```

Why: Explicit paths allow snapshots and replication of application data independently.

**GPU Passthrough**

Enable Intel QSV or NVIDIA GPU:

```yaml
services:
  transcoder:
    image: jellyfin:latest
    devices:
      - /dev/dri:/dev/dri  # Intel iGPU
    environment:
      - JELLYFIN_PublishedServerUrl=http://<NAS_IP>:8096
```

## Migration & Backup Workflows

**Pre-Migration Audit Checklist**

Document everything before migrating:

```bash
# Export system config
# UI: System > General > Download Config

# List all pools, datasets, snapshots
zpool list
zfs list -r -t filesystem,snapshot

# Export share configs
midclt call sharing.smb.query | jq .
midclt call sharing.nfs.query | jq .

# Backup cron jobs
crontab -l

# Export API keys (download via UI)
```

Why: Prevents data loss and service interruption during cutover.

**Dataset Replication (Local)**

Replicate to backup pool:

```bash
zfs send <POOL>/<DATASET>@snap | zfs receive <BACKUP_POOL>/<DATASET>
```

Automate incremental replication:

```bash
zfs send -i <POOL>/<DATASET>@old <POOL>/<DATASET>@new | \
  zfs receive <BACKUP_POOL>/<DATASET>
```

**Remote Replication**

Over SSH with dedicated replication user:

```bash
# Create replication user on remote NAS
# UI: Accounts > Users > Add, shell=/usr/bin/false

# Set up SSH key auth, then replicate:
zfs send <POOL>/<DATASET>@snap | \
  ssh repl@<REMOTE_NAS_IP> zfs receive <POOL>/<DATASET>
```

**Box-to-Box Migration**

1. Download system config from old NAS
2. Replicate all datasets to new NAS (or migrate drives physically)
3. Import config on new NAS
4. Verify shares and services are accessible
5. Update DNS/IPs pointing to new NAS

## Replication Patterns

**Local Replication (Same Box, Different Pool)**

Use replication tasks for automation:

```bash
# Via API
curl -X POST http://<NAS_IP>/api/v2.0/replication \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{
    "name": "pool_to_backup",
    "direction": "push",
    "source_datasets": ["<POOL>/<DATASET>"],
    "target_dataset": "<BACKUP_POOL>",
    "recursive": true,
    "retention": {"nightly": 7}
  }'
```

**Remote Replication**

Configure via UI: Data Protection > Replication Tasks. Why: Push vs. pull tradeoffs—push is simpler; pull is more secure if the source is compromised.

## Monitoring & Alerts

**Health Check Script**

```bash
#!/bin/bash
API_KEY="<API_KEY>"
NAS_IP="<NAS_IP>"

# Check pool status
status=$(curl -s -H "Authorization: Bearer $API_KEY" \
  http://$NAS_IP/api/v2.0/pool | jq '.[0].status')

if [ "$status" != '"HEALTHY"' ]; then
  echo "ALERT: Pool status is $status"
fi

# Check disk temps
zpool status | grep -i temp
```

**Metrics to Monitor**

- Pool usage (alert at 80%, 90%)
- Disk temperatures (alert >50°C)
- Scrub completion and errors
- Replication lag (remote tasks)
- Service availability (SSH, SMB, API)

## Troubleshooting

**Dataset Permissions After Migration**

Symptom: containers cannot write to bind-mounted datasets.

Fix:

```bash
zfs set aclmode=passthrough <POOL>/<DATASET>
chown -R <PUID>:<PGID> /mnt/<POOL>/<DATASET>
chmod -R 750 /mnt/<POOL>/<DATASET>
```

**Container Mount Failures**

Debug with:

```bash
docker logs <CONTAINER_ID>
mount | grep <DATASET>
ls -la /mnt/<POOL>/<DATASET>
```

**Networking After Upgrade**

SCALE upgrades may reset interfaces. Verify:

```bash
ip addr show
cat /etc/netplan/*.yaml
midclt call interfaces.query | jq .
```

**Key Debug Commands**

```bash
zpool status <POOL>           # pool health
zfs list -r <POOL>            # dataset hierarchy
smartctl -a /dev/sd<X>        # disk SMART data
systemctl status middleware    # API service health
journalctl -u middleware -n 50 # API logs
```
