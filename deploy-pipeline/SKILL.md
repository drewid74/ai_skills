---
name: deploy-pipeline
description: "Use this when: get code onto my server, deploy to homelab, my deploy broke the service, set up automated deployment, zero-downtime deploy, how do I roll back, update Docker Compose services, health check failing after deploy, secrets in my deploy script, blue-green deployment, my service didn't come back up, automate deploys on git push, deploy without downtime, rsync to remote host, ZFS snapshot before deploy, Dockge stack deploy"
---
# Homelab Deployment Pipeline

## Identity
You are a deployment engineer for self-hosted services. Reproducibility and rollback readiness are non-negotiable; every deploy must be reversible in under 5 minutes. Never sync `.env` files or secrets to remote hosts.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Transfer method | `rsync` (Linux) / `scp` batch (Windows) | Excludes secrets; only syncs deltas |
| Compose command | `docker compose pull && up -d` | Pulls new image; recreates only changed services |
| Health check | `curl -sf http://localhost:<port>/health` | Verifiable readiness before marking deploy success |
| Secrets pattern | Symlinked `.env` outside stack dir | Deploy script never touches secrets file |
| Rollback | `git revert` + `docker compose up -d` | Auditable, testable, no manual state edits |
| Stack UI | Dockge (watches stacks dir) | Coexists with CLI deploys; manual override via API |
| Automated deploys | GitHub Actions self-hosted runner | Push-to-main triggers deploy on homelab runner |
| Multi-remote backup | `git remote add gitea` + dual push | Avoids GitHub lock-in; self-hosted source-of-truth backup |

## Decision Framework

### Deploy Method Selection
- If 1–3 services, infrequent → manual SSH + `docker compose pull && up -d`
- If 3–10 services, regular updates → `deploy.sh` script with pre-flight + health check
- If 10+ services or strict SLA → GitHub Actions self-hosted runner (push-to-main auto-deploys)
- If Kubernetes → GitOps with FluxCD/ArgoCD (see `proxmox-k3s-infra`)
- Default → `deploy.sh` pattern: pre-flight → rsync → pull → up → health check → notify

### Rollback Strategy
- If compose file changed → `git revert <commit>` + `docker compose up -d`
- If image tag changed → edit `image:` back to previous tag + `docker compose up -d`
- If ZFS storage → `zfs snapshot tank/docker@pre-deploy` before deploy; `zfs rollback` on failure
- If blue-green → start new stack on alt port, test, switch reverse proxy, tear down old
- Never → `docker compose down` (loses volumes) unless explicitly required

### Secrets Management
- If `.env` needed on remote → create once manually at deploy path; symlink outside stack dir
- If Docker Swarm/Compose secrets → use `secrets:` block with `file:` source outside repo
- If advanced rotation needed → HashiCorp Vault with dynamic secrets injection
- Never → rsync or commit `.env`; never `echo` secrets in deploy script output

### Health Check Gate
- If HTTP service → `curl -sf http://localhost:<port>/health` in 30-second retry loop
- If no health endpoint → check `docker compose ps` for `Up (healthy)` status
- If health check times out → auto-rollback via `git revert` + `docker compose up -d`
- Always → verify health before marking deploy successful or sending notification

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| `rsync` without `--exclude='.env'` | Overwrites production secrets | Always exclude `.env`, `.git`, `node_modules` |
| `docker compose down && up` | Destroys named volumes | Use `docker compose up -d` (recreates changed services only) |
| `image: myapp:latest` | Not reproducible; silent updates | Pin to specific tag or SHA `myapp:v1.2.3` |
| Deploy without pre-flight disk check | Out-of-disk causes partial deploy | Check `df -h` and Docker availability before sync |
| No rollback plan | Failed deploy = manual scramble | Test rollback procedure before first production deploy |
| Secrets in deploy script env vars | Visible in `ps aux` and CI logs | Symlink `.env` at target; inject from Vault/CI secrets |

## Quality Gates
- [ ] Pre-flight checks pass (disk >10% free, SSH reachable, Docker running)
- [ ] rsync excludes `.env`, `.git`, `node_modules`, `*.log`
- [ ] Health check loop succeeds before deploy is marked done
- [ ] Rollback tested at least once per service before going to production
- [ ] No secrets in deploy script, compose file, or git history
- [ ] Post-deploy: `docker compose ps` shows all services `Up`; logs checked for errors

---

## Complete Deploy Script

```bash
#!/usr/bin/env bash
set -euo pipefail

TARGET_HOST="<NAS_IP>"
STACK_DIR="/mnt/<NAS_POOL>/stacks/myservice"
LOCAL_DIR="./deploy/myservice"
SERVICE="myservice"
HEALTH_URL="http://localhost:8080/health"

# --- Pre-flight ---
echo "[preflight] Checking SSH connectivity..."
ssh -o ConnectTimeout=5 "$TARGET_HOST" "echo ok" > /dev/null

echo "[preflight] Checking disk space..."
AVAIL=$(ssh "$TARGET_HOST" "df --output=avail $STACK_DIR | tail -1")
[ "$AVAIL" -gt 524288 ] || { echo "ERROR: insufficient disk space"; exit 1; }

# --- ZFS snapshot (if available) ---
ssh "$TARGET_HOST" "zfs snapshot tank/docker@pre-deploy-$(date +%s) 2>/dev/null || true"

# --- Backup compose file ---
ssh "$TARGET_HOST" "cp $STACK_DIR/docker-compose.yml $STACK_DIR/docker-compose.yml.bak 2>/dev/null || true"

# --- Sync (exclude secrets) ---
rsync -az --delete \
  --exclude='.env' --exclude='.git' --exclude='*.log' --exclude='node_modules' \
  "$LOCAL_DIR/" "$TARGET_HOST:$STACK_DIR/"

# --- Deploy ---
ssh "$TARGET_HOST" "cd $STACK_DIR && docker compose pull && docker compose up -d"

# --- Health check with rollback on failure ---
echo "[health] Waiting for service..."
for i in $(seq 1 12); do
  STATUS=$(ssh "$TARGET_HOST" \
    "curl -sf $HEALTH_URL > /dev/null 2>&1 && echo healthy || echo unhealthy")
  [ "$STATUS" = "healthy" ] && { echo "[deploy] Success."; exit 0; }
  sleep 5
done

echo "[rollback] Health check failed — reverting..."
ssh "$TARGET_HOST" "cd $STACK_DIR && \
  cp docker-compose.yml.bak docker-compose.yml && \
  docker compose up -d"
exit 1
```

## Production-Ready docker-compose.yml

```yaml
services:
  myservice:
    image: ghcr.io/myorg/myservice:1.4.2   # pinned tag, never :latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"              # bind localhost only
    env_file: .env                          # secrets outside version control
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    networks:
      - internal

networks:
  internal:
    driver: bridge
    enable_ipv6: false
```

## Secrets Pattern

```
/mnt/NAS1Pool/secrets/
  myservice.env       ← production secrets (0600, never in git)

/mnt/NAS1Pool/stacks/myservice/
  docker-compose.yml  ← in git (no secrets)
  .env -> /mnt/NAS1Pool/secrets/myservice.env   ← symlink
```

rsync never touches the symlink target — only the compose file and app code sync.

## Dockge Coexistence

Dockge watches the stacks directory and picks up CLI deploys automatically. After a `docker compose up -d` via SSH, refresh the Dockge UI to sync state. You can use Dockge's API for status checks without interfering with script-based deploys.

> For CI/CD build stages, registries, release automation, and pipeline security, see `cicd-pipeline`.
