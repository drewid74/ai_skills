---
name: deploy-pipeline
description: "Use this skill whenever the user wants to deploy, update, or manage services on remote homelab servers. Triggers include: any mention of 'deploy', 'deployment', 'push to server', 'deploy script', 'deploy.ps1', 'deploy.sh', 'rsync', 'scp', 'SSH deploy', 'git pull deploy', 'docker compose up', 'rolling update', 'blue-green', 'zero downtime', 'CI/CD homelab', 'GitHub Actions self-hosted', 'self-hosted runner', 'Dockge', 'Portainer deploy', 'stack update', 'remote docker', 'secrets management', 'env file', '.env', 'multi-remote git', or requests to set up any kind of automated or scripted deployment workflow for self-hosted services. Also use when the user is troubleshooting a failed deployment, wants to standardize their deployment process, or is building deployment scripts (bash, PowerShell, or Python). If someone says 'how do I get my code onto my server' or 'update my containers', use this skill."
---

# Homelab Deployment Pipeline

## Overview

Standardized patterns for deploying containerized services to homelab servers. Covers the full spectrum from manual SSH+rsync to GitOps with GitHub Actions, with emphasis on reproducible, scriptable workflows that minimize downtime and human error.

## Deployment Models

Choose based on complexity and frequency:

- **Manual SSH**: `ssh → cd → git pull → docker compose up -d`. Good for one-offs or learning. Prone to inconsistency.
- **Script-based (deploy.sh / deploy.ps1)**: Parameterized, repeatable. The sweet spot for most homelabs (1–10 services).
- **Git-pull deploy**: Webhook or polling triggers `git pull → rebuild`. Simple GitOps without infrastructure overhead.
- **CI/CD (GitHub Actions)**: Push to main → runner executes deploy workflow. Requires self-hosted runner, best for 10+ services.
- **GitOps (ArgoCD/FluxCD)**: Kubernetes-native, declarative. Overkill for most homelabs but excellent for complex deployments.

**When to use which**: 1–3 services = manual/script; 3–10 = script + git-pull; 10+ or strict SLA = CI/CD or GitOps.

## Script-Based Deploy Pattern: Bash

Store in repo root as `deploy.sh`. Make executable: `chmod +x deploy.sh`.

```bash
#!/bin/bash
set -euo pipefail

# Configuration (customize per project)
REMOTE_HOST="192.168.1.100"
REMOTE_USER="deploy"
STACK_PATH="/mnt/docker/stacks/myapp"
COMPOSE_FILE="docker-compose.yml"
LOCAL_REPO="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; exit 1; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Pre-flight checks
log "Running pre-flight checks..."
ssh -q "$REMOTE_USER@$REMOTE_HOST" "df -h / | tail -1 | awk '{print \$5}' | sed 's/%//' | awk '{if (\$1 > 90) exit 1}'" \
  || error "Disk usage >90% on target server"

ssh -q "$REMOTE_USER@$REMOTE_HOST" "docker ps > /dev/null 2>&1" \
  || error "Docker not available on $REMOTE_HOST"

log "Pre-flight checks passed"

# Backup current state
log "Backing up current compose file..."
ssh -q "$REMOTE_USER@$REMOTE_HOST" "cd '$STACK_PATH' && cp '$COMPOSE_FILE' '$COMPOSE_FILE.bak.$(date +%s)'"

# Sync files (rsync excludes noise and secrets)
log "Syncing files to remote..."
rsync -avz \
  --exclude='.env' \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  "$LOCAL_REPO/" "$REMOTE_USER@$REMOTE_HOST:$STACK_PATH/" \
  || error "rsync failed"

# Deploy on remote
log "Pulling latest on remote..."
ssh -q "$REMOTE_USER@$REMOTE_HOST" "cd '$STACK_PATH' && git pull origin main" \
  || error "git pull failed"

log "Building and starting services..."
ssh -q "$REMOTE_USER@$REMOTE_HOST" "cd '$STACK_PATH' && docker compose pull && docker compose up -d" \
  || error "docker compose up failed"

# Health check (customize per service)
log "Waiting for services to be ready..."
for i in {1..30}; do
  if ssh -q "$REMOTE_USER@$REMOTE_HOST" "curl -sf http://localhost:8080/health > /dev/null 2>&1"; then
    log "Health check passed"
    break
  fi
  if [ $i -eq 30 ]; then
    warn "Health check timeout, rolling back..."
    ssh -q "$REMOTE_USER@$REMOTE_HOST" "cd '$STACK_PATH' && git revert HEAD --no-edit && docker compose up -d"
    error "Deploy failed health check"
  fi
  sleep 2
done

log "Deploy successful!"
ssh -q "$REMOTE_USER@$REMOTE_HOST" "docker compose logs --tail=20"
```

**Why this pattern**: Pre-flight checks prevent partial deploys. Backup before change. Rsync excludes prevent syncing secrets or build artifacts. Health checks gate success. Rollback on failure.

## Script-Based Deploy Pattern: PowerShell

For Windows workstations deploying to Linux servers via SSH.

```powershell
param(
    [string]$RemoteHost = "192.168.1.100",
    [string]$RemoteUser = "deploy",
    [string]$StackPath = "/mnt/docker/stacks/myapp",
    [string]$LocalRepo = "."
)

function Log-Info { Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $args" -ForegroundColor Green }
function Log-Error { Write-Host "[ERROR] $args" -ForegroundColor Red; exit 1 }
function Log-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }

# Pre-flight check
Log-Info "Checking SSH connectivity..."
try {
    ssh -q "$RemoteUser@$RemoteHost" "docker ps > /dev/null 2>&1"
} catch {
    Log-Error "SSH or Docker unavailable"
}

# Sync via SCP (or rsync if available)
Log-Info "Syncing files..."
$exclude = @('.env', '.git', 'node_modules', '__pycache__', '*.log')
foreach ($file in Get-ChildItem $LocalRepo -Recurse) {
    $skip = $false
    foreach ($pattern in $exclude) {
        if ($file.Name -like $pattern) { $skip = $true; break }
    }
    if (-not $skip -and -not $file.PSIsContainer) {
        $relativePath = $file.FullName.Replace("$LocalRepo\", "").Replace("\", "/")
        scp "$file" "$RemoteUser@$RemoteHost`:$StackPath/$relativePath" | Out-Null
    }
}

# Deploy
Log-Info "Pulling latest and deploying..."
ssh "$RemoteUser@$RemoteHost" @"
    set -e
    cd '$StackPath'
    git pull origin main
    docker compose pull
    docker compose up -d
    sleep 5
    docker compose logs --tail=20
"@

Log-Info "Deploy complete"
```

## Multi-Remote Git Push

Automate pushes to both GitHub (origin) and self-hosted Gitea/Forgejo (backup):

```bash
# Setup (one-time)
git remote add gitea ssh://git@gitea.local/myuser/myapp.git

# Deploy script includes:
git push origin main
git push gitea main

# Optional: git hook for automatic dual-push on commit
# .git/hooks/post-commit
#!/bin/bash
git push gitea main > /dev/null 2>&1 &
```

**Why**: Prevents lock-in to GitHub. Self-hosted Gitea serves as source-of-truth backup.

## Secrets Management

Never commit `.env` files. Use `.env.example` with placeholders:

```bash
# .env.example (committed)
DATABASE_PASSWORD=CHANGE_ME
API_KEY=CHANGE_ME

# Actual .env (gitignored)
DATABASE_PASSWORD=actualSecretPassword123
API_KEY=actualApiKey456
```

**Symlink pattern** (preferred for shared stacks):

```bash
# Store secrets outside stack directory
mkdir -p /mnt/secrets
echo "DATABASE_PASSWORD=secret" > /mnt/secrets/myapp.env

# Link into stack
ln -s /mnt/secrets/myapp.env /mnt/docker/stacks/myapp/.env

# Deploy script doesn't touch .env, it's already there
```

**Docker secrets** (for swarm or compose v3.1+):

```yaml
secrets:
  db_password:
    file: /mnt/secrets/db_password.txt

services:
  database:
    secrets:
      - db_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
```

**Vault integration** (advanced): Use HashiCorp Vault for dynamic secret rotation without redeployment.

## Docker Compose Deploy Patterns

Choose the right command for your need:

- `docker compose up -d` — Recreate only changed services. Safest, most common.
- `docker compose pull && docker compose up -d` — Update to latest remote images.
- `docker compose up -d --build` — Rebuild from local Dockerfiles (use sparingly, adds time).
- `docker compose down && docker compose up -d` — Full restart. Use only when needed (clears volumes!).
- `docker compose up -d --no-deps <service>` — Rolling update: restart single service without affecting others.

**Health checks in compose**:

```yaml
services:
  app:
    image: myapp:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 20s
```

Deploy script waits for health before considering it successful.

## Dockge Integration

Dockge is a lightweight UI for managing Docker stacks (web-based docker-compose manager).

**How it works**: Dockge watches a stacks directory (e.g., `/mnt/docker/stacks/`) and auto-detects compose files.

```bash
# Directory structure
/mnt/docker/stacks/
├── app1/
│   ├── docker-compose.yml
│   └── .env (gitignored)
├── app2/
│   └── docker-compose.yml
└── reverse-proxy/
    └── docker-compose.yml
```

Dockge reads these files and provides UI buttons to start/stop/recreate stacks. **Coexist with CLI deploys**: Both can manage the same files. Refresh Dockge UI after CLI deploy.

Deploy via Dockge API:

```bash
curl -X POST http://dockge-host/api/stacks/restart \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"stackName": "app1"}'
```

## GitHub Actions Self-Hosted Runner

Set up a runner on homelab to deploy on push:

**Runner setup** (on homelab server, once):

```bash
# Create runner user
sudo useradd -m -s /bin/bash runner

# Download and setup runner
cd /opt/actions-runner
curl -o actions-runner-linux-x64.tar.gz \
  https://github.com/actions/runner/releases/download/v2.x.x/actions-runner-linux-x64.tar.gz
tar xzf actions-runner-linux-x64.tar.gz
sudo chown -R runner:runner /opt/actions-runner

# Register (paste token from GitHub Settings > Actions > Runners)
sudo -u runner ./config.sh --url https://github.com/myuser/myrepo --token XXXXX

# Run as service
sudo ./svc.sh install
sudo ./svc.sh start
```

**Workflow template** (`.github/workflows/deploy.yml`):

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: |
          ./deploy.sh
```

**Security**: Run runners in isolated VMs, not bare metal. Limit which repos can use the runner (settings > actions > runner groups).

## Pre-Deploy Checklist

Run before every deploy (can be automated):

```bash
#!/bin/bash
echo "Pre-deploy checklist:"
echo "1. Disk space:"
ssh $REMOTE "df -h / | tail -1 | awk '{print \$4, \$5}'"
echo "2. Current services:"
ssh $REMOTE "docker compose -f $STACK_PATH/docker-compose.yml ps"
echo "3. Recent commits:"
git log --oneline -5
echo "4. Uncommitted changes:"
git status --short
echo "5. Continue deploy? (y/n)"
read -r response
[ "$response" = "y" ] || exit 0
```

## Post-Deploy Verification

After deploy succeeds, verify everything:

```bash
# Health endpoint
curl -sf http://target-service/health || echo "Health check failed"

# Container status
docker compose ps | grep -v "Up" && echo "Some containers not running"

# Log check
docker compose logs --tail=50 | grep -i error && echo "Errors in logs"

# Service-specific check (example: database)
docker compose exec database psql -U user -d mydb -c "SELECT 1" || echo "DB not responding"

# Notification
curl -X POST https://discord.com/api/webhooks/XXX \
  -d '{"content": "Deploy successful at '$(date)'"}' \
  -H "Content-Type: application/json"
```

## Rollback Strategies

Keep rollback simple and tested.

**Compose file rollback**:

```bash
cd $STACK_PATH
git log --oneline -10  # find the good commit
git revert <bad-commit-hash>
docker compose up -d
```

**Image tag rollback** (pre-tag images before deploy):

```yaml
services:
  app:
    image: myapp:v1.2.3  # Use specific tag, not 'latest'
```

Change tag to previous version, then `docker compose up -d`.

**ZFS snapshot** (if using ZFS):

```bash
# Before deploy
zfs snapshot tank/docker@pre-deploy-v1.2.3

# After deploy fails
zfs rollback tank/docker@pre-deploy-v1.2.3
docker compose up -d
```

**Blue-green**: Run two versions side-by-side, switch traffic, tear down old:

```bash
# Start new version
docker compose -f docker-compose.green.yml up -d

# Test new version (curl :8081)
curl http://localhost:8081/health

# Switch traffic (reverse proxy config)
# Then tear down old
docker compose down
```

## Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| Deploy hangs | `ssh -v` shows hang, check firewall rules | Verify SSH key works, check network routing |
| Container won't start | `docker compose logs` shows error | Check `.env` populated, verify exposed ports available, check bind mount paths |
| Permission denied on files | `ls -l` shows wrong owner | Fix with `docker compose exec service chown -R appuser:appgroup /data` |
| Network issues after deploy | `docker network inspect` shows no services | Check DNS resolution inside container, verify firewall allows container→external traffic |
| Partial deploy (some services up, some down) | `docker compose ps` shows mixed state | Check `depends_on` order, check resource limits, review logs |
| Health check timeout | `curl` from host works, from container fails | Container can't reach service (use service name from compose), check Docker DNS |

**General**: Always check `docker compose logs --tail=100` and host system resources (`docker stats`).
