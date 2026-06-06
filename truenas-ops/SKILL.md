---
name: truenas-ops
description: "Use this when: set up an SMB or NFS share, my ZFS pool shows errors, automate dataset snapshots, replicate data to another NAS, fix dataset permissions for Docker containers, my share is not accessible, migrate TrueNAS CORE to SCALE, tune storage for media or databases, add a cloud backup destination, my disk is failing, expand or replace a drive in the pool, set up offsite replication, TrueNAS, ZFS, ix-applications, SCALE 24.10, docker on TrueNAS, pool health check, dataset record size, NAS API, container bind mount permissions"
---

# TrueNAS Operations

## Identity
You are a TrueNAS SCALE/CORE storage administrator. Treat data integrity as non-negotiable — ZFS is only as safe as the configuration around it. Never run deduplication on mechanical disks or small RAM systems.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Dataset layout | One dataset per service/stack | Granular snapshots and replication |
| Compression | lz4 general, zstd for media | CPU-efficient; zstd better ratio for cold data |
| Record size | 16K for DBs, 1M for media, 128K general | Matches I/O pattern to block size |
| ACL mode | posixacl + aclmode=passthrough | Container PUID/PGID compatibility |
| Snapshots | Automated via UI (Data Protection > Snapshots) | Consistent naming, retention policy |
| Scrubs | Monthly via UI scheduler | Detects silent corruption before it spreads |
| API auth | Bearer token (Settings > API Keys) | Never use root credentials in scripts |
| Replication | ZFS send/recv over SSH with dedicated repl user | Encrypted, incremental, crash-consistent |

## Decision Framework

### ZFS Record Size
- If PostgreSQL/MySQL dataset → 16K record size
- If media (video/photos) dataset → 1M record size
- If general app data → 128K record size
- Default → set BEFORE writing data (cannot change retroactively for existing data)

### Container Permissions
- If container runs with PUID/PGID → chown dataset to that UID:GID, chmod 750
- If SMB share needed alongside containers → use acltype=posixacl, aclmode=passthrough
- Default → PUID=1000, PGID=1000; never leave datasets owned by root for bind mounts

### Replication Strategy
- If same box, different pool → local ZFS send/recv or UI Replication Task
- If remote NAS, same network → push over SSH with key auth, no password
- If offsite backup → ZFS replication + cloud sync task (B2/S3) as second copy
- Default → recursive replication with 7-day nightly retention

### Version / Migration Path
- If TrueNAS CORE → SCALE migration → export config, replicate datasets, import on new system
- If SCALE upgrade → snapshot all pools first, read release notes
- Default → snapshot everything before any major operation

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Enable deduplication on spinning disks | Requires ~5GB RAM per 1TB; thrashes ARC | Use compression (lz4/zstd) instead |
| Root-owned bind-mount directories | Containers cannot write | chown -R PUID:PGID before first container start |
| Skip pre-upgrade snapshots | Upgrade bugs can corrupt datasets | Snapshot all pools + download config backup |
| Use RAIDZ1 with >4TB drives | Rebuild time exposes second disk failure | Use RAIDZ2 or mirrors for large drives |
| Change record size after data is written | Only affects new writes; mixed sizes hurt perf | Set record size on empty dataset |
| Ignore scrub errors | Corrupted sectors spread silently | Investigate and replace disk immediately |

## Quality Gates
- [ ] Each service has its own dataset with correct PUID:PGID ownership
- [ ] Automated snapshot task configured with retention policy
- [ ] Monthly scrub scheduled; last scrub shows 0 errors
- [ ] Replication task verified: remote dataset matches source
- [ ] SMART tests passing; no reallocated sectors on any disk
- [ ] Pool usage below 80% (ZFS performance degrades above 80%)

## Reference
```bash
zpool status <POOL>                          # pool health + resilver status
zfs list -r -t filesystem,snapshot <POOL>    # full dataset + snapshot tree
zfs snapshot <POOL>/<DS>@$(date +%Y%m%d)     # manual snapshot
zfs send -i <POOL>/<DS>@old <POOL>/<DS>@new | ssh repl@<IP> zfs recv <POOL>/<DS>
smartctl -a /dev/sdX                         # disk SMART data
midclt call sharing.smb.query | jq .         # list SMB shares via CLI
curl -H "Authorization: Bearer TOKEN" http://NAS_IP/api/v2.0/pool
```

---

## API Patterns

```bash
# All calls use Bearer token auth
curl -H "Authorization: Bearer <API_KEY>" http://<NAS_IP>/api/v2.0/system/info

# Key endpoints:
# GET  /pool               — list pools with usage
# GET  /dataset            — list datasets with properties
# GET  /sharing/smb        — SMB share configuration
# POST /sharing/smb        — create SMB share
# GET  /service            — service status
```

```python
import requests

headers = {"Authorization": f"Bearer {API_KEY}"}
pools = requests.get(f"http://{NAS_IP}/api/v2.0/pool", headers=headers).json()
for pool in pools:
    print(f"{pool['name']}: {pool['allocated']} / {pool['size']}")
```

## ZFS Operations

```bash
# Dataset creation with container-compatible permissions
zfs create -o mountpoint=/mnt/<POOL>/<DATASET> \
  -o aclmode=passthrough -o aclinherit=passthrough \
  <POOL>/<DATASET>
chown <PUID>:<PGID> /mnt/<POOL>/<DATASET>
chmod 750 /mnt/<POOL>/<DATASET>

# Record size + compression tuning (set BEFORE writing data)
zfs set recordsize=16K compression=lz4 <POOL>/postgres
zfs set recordsize=1M  compression=zstd <POOL>/media
zfs set recordsize=128K compression=lz4 <POOL>/general

# Snapshot management
zfs snapshot <POOL>/<DS>@$(date +%Y%m%d_%H%M%S)
zfs list -t snapshot
zfs rollback <POOL>/<DS>@<SNAP_NAME>

# Monthly scrub
zpool scrub <POOL>; zpool status | grep scrub
```

## Dataset Layout

```
<POOL>
├── docker/
│   ├── stacks/     # one subdir per compose stack
│   └── images/     # Docker image storage
├── data/
│   ├── nextcloud/
│   ├── postgres/
│   └── media/
└── backups/
```

## Docker Compose on SCALE 24.10+

> For full Docker Compose patterns, health checks, and GPU passthrough, see `docker-selfhost`.

Key TrueNAS-specific requirements:
- Store stacks under `/mnt/<POOL>/stacks/<stack-name>/`
- `.env` permissions must be `0600` (restrict to owner)
- Always set explicit `PUID`/`PGID` and `user: "1000:1000"` in compose
- Bind mount paths must reference `/mnt/<POOL>/...`, not symlinks

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

## Replication

```bash
# Local (same box, different pool)
zfs send <POOL>/<DS>@snap | zfs receive <BACKUP_POOL>/<DS>

# Incremental local
zfs send -i <POOL>/<DS>@old <POOL>/<DS>@new | zfs receive <BACKUP_POOL>/<DS>

# Remote over SSH (dedicated replication user, key auth)
zfs send <POOL>/<DS>@snap | ssh repl@<REMOTE_NAS_IP> zfs receive <POOL>/<DS>
```

## Migration Checklist

```bash
# 1. Export system config: UI → System > General > Download Config
# 2. Document current state:
zpool list
zfs list -r -t filesystem,snapshot
midclt call sharing.smb.query | jq .
midclt call sharing.nfs.query | jq .
crontab -l
# 3. Replicate all datasets to new system
# 4. Import config on new system
# 5. Verify shares, services, and container mounts
# 6. Update DNS/IPs pointing to new NAS
```

## Monitoring Health Check

```bash
#!/bin/bash
status=$(curl -s -H "Authorization: Bearer $API_KEY" \
  http://$NAS_IP/api/v2.0/pool | jq '.[0].status')
[ "$status" != '"HEALTHY"' ] && echo "ALERT: Pool $status"

# Local checks
zpool status | grep -E "(DEGRADED|FAULTED|OFFLINE|REMOVED|UNAVAIL)"
smartctl -a /dev/sdX | grep -i reallocated
```

Alert thresholds: pool usage >80%, disk temp >50°C, any SMART reallocated sectors.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Container can't write to dataset | `chown -R PUID:PGID /mnt/<POOL>/<DS>` + set `aclmode=passthrough` |
| Container mount failures | `docker logs <ID>`, `mount | grep <DS>`, `ls -la /mnt/<POOL>/<DS>` |
| Networking after SCALE upgrade | `ip addr show`, `midclt call interfaces.query | jq .` |
| Scrub shows errors | Replace failing disk immediately; resilver before removing old disk |
| SMB share not accessible | `midclt call sharing.smb.query | jq .`; verify ACL and service status |
