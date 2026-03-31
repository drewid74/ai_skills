---
name: cicd-pipeline
description: "Use this skill whenever the user wants to build, debug, optimize, or manage CI/CD pipelines and runner infrastructure. Triggers include: any mention of 'CI/CD', 'pipeline', 'GitHub Actions', 'Forgejo Actions', 'Gitea Actions', 'GitLab CI', 'Jenkins', 'Drone CI', 'Woodpecker CI', 'act', 'self-hosted runner', 'runner', 'build pipeline', 'build cache', 'artifact', 'container registry', 'OCI registry', 'Zot', 'Harbor', 'Docker Hub', 'GHCR', 'matrix build', 'parallel jobs', 'build optimization', 'pipeline debugging', 'workflow', 'YAML pipeline', 'build agent', 'build failing', 'CI broken', 'pipeline slow', 'cache miss', 'build artifact', 'release automation', 'semantic release', 'auto-tag', 'multi-environment', 'promote', 'staging pipeline', 'canary deploy', 'pipeline security', 'OIDC', 'workload identity', 'reusable workflow', 'composite action', or any request to set up, fix, speed up, or redesign a CI/CD pipeline. Also use when the user is troubleshooting build failures, slow pipelines, runner issues, or wants to move from cloud CI to self-hosted. If someone says 'my build is failing', 'pipeline is slow', 'set up CI for my project', or 'I want to run my own runners', use this skill."
---

# CI/CD Pipeline Engineering

Build, optimize, and troubleshoot CI/CD pipelines from single-project GitHub Actions workflows to self-hosted runner fleets with private registries. Covers pipeline design, runner infrastructure, caching, artifacts, multi-environment promotion, and debugging failing builds.

## CI/CD Platform Selection

### GitHub Actions
- Integrated with GitHub, YAML-based workflows in `.github/workflows/`
- Free tier: 2,000 minutes/month (public repos unlimited)
- Marketplace: 20,000+ community actions
- Self-hosted runners: run on your own hardware for unlimited minutes and private network access
- Best for: projects already on GitHub, most common choice

### Forgejo/Gitea Actions
- Compatible with GitHub Actions syntax (same YAML, most actions work)
- Self-hosted git + CI in one platform
- Runner: Forgejo Runner (forked from `act_runner`)
- Best for: fully self-hosted git+CI, avoiding GitHub dependency
- Gotcha: not all GitHub Actions marketplace actions work (some use GitHub-specific APIs)

### GitLab CI
- `.gitlab-ci.yml` in repo root, built into GitLab
- Strong: Docker-in-Docker, built-in container registry, environment management
- Self-hosted: GitLab CE (heavy but complete)
- Best for: teams already on GitLab, complex pipelines with many stages

### Woodpecker CI
- Lightweight, container-native, YAML pipelines
- Fork of Drone CI (Apache 2.0 licensed)
- Docker Compose deployment, minimal resource usage
- Best for: homelab CI that's lighter than GitLab

### Local Testing: `act`
- Run GitHub Actions locally in Docker containers
- `act -j build` — test workflows without pushing
- Limitations: some GitHub-specific features don't work (OIDC, some contexts)
- Essential for debugging workflow changes without commit+push+wait cycles

## Pipeline Architecture

### Standard Stages
```
Trigger → Checkout → Setup → Lint → Test → Build → Publish → Deploy
```

1. **Trigger**: push, PR, tag, schedule, manual (workflow_dispatch)
2. **Checkout**: `actions/checkout@v4` with fetch-depth for history
3. **Setup**: install language runtime, restore caches
4. **Lint/Format**: fail fast on style issues (cheapest check)
5. **Type Check**: catch type errors (TypeScript, mypy)
6. **Test**: unit → integration → e2e (ordered by speed)
7. **Build**: compile/bundle/package the artifact
8. **Publish**: push image to registry, upload artifact
9. **Deploy**: push to target environment (staging/production)

### Design Principles
- **Fail fast**: cheapest/fastest checks first (lint before test, unit before integration)
- **Parallel where possible**: lint, type-check, and test can run simultaneously
- **Cache aggressively**: dependencies, build artifacts, Docker layers
- **Idempotent**: re-running the same pipeline produces the same result
- **One artifact, many deploys**: build once, promote the same artifact through environments

### GitHub Actions Workflow Template
```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # Cancel superseded runs on same branch

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: ruff check .
      - run: mypy src/
      - run: pytest --cov=src tests/

  build:
    needs: lint-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: ${{ github.ref == 'refs/heads/main' }}
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: self-hosted
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          docker pull ghcr.io/${{ github.repository }}:${{ github.sha }}
          docker compose -f docker-compose.staging.yml up -d
```

## Self-Hosted Runner Infrastructure

### GitHub Actions Self-Hosted Runner
- Install: download runner package, configure with repo/org token, run as service
- Systemd service: `sudo ./svc.sh install && sudo ./svc.sh start`
- Labels: tag runners with capabilities (`self-hosted`, `linux`, `gpu`, `arm64`)
- Runner groups (org level): control which repos can use which runners
- Ephemeral runners: `--ephemeral` flag — runner handles one job then re-registers (clean environment)

### Forgejo/Gitea Runner
- `forgejo-runner` binary or Docker container
- Register: `forgejo-runner register` with instance URL and token
- Labels match GitHub-style: `ubuntu-latest`, `self-hosted`, custom labels
- Docker executor: runs each job in a fresh container (isolated, clean)
- Host executor: runs directly on the machine (faster, less isolated)

### Runner Placement
- **VM-based**: dedicated VM per runner, good isolation, GPU passthrough possible
- **LXC container**: lightweight, fast, but Docker-in-Docker needs privileged mode
- **Docker container**: runner itself in Docker, jobs in nested containers (DinD)
- **Bare metal**: maximum performance, least isolation — use for trusted repos only
- Recommendation: VM for production runners, Docker for CI runners on trusted code

### Runner Security
- Self-hosted runners execute arbitrary code from workflows — treat as semi-trusted
- Never put runners on your NAS or production infrastructure directly
- Use dedicated VMs or containers with limited network access
- Restrict runner access to specific repos (GitHub) or use runner groups
- Ephemeral runners: fresh environment per job, no state leakage between runs
- Network: runners need outbound HTTPS to GitHub/Forgejo, and access to your registry/deploy targets

### Multi-Runner Fleet
- Scale horizontally: multiple runner instances for parallel jobs
- Auto-scaling: GitHub supports webhook-based auto-scaling (spin up runners on demand)
- Mix runners: cloud for burst capacity, self-hosted for baseline + private network access
- Labels for routing: `runs-on: [self-hosted, linux, gpu]` targets specific runners

## Build Caching

### Why Cache
- Dependency installation (npm install, pip install) can take minutes
- Docker layer rebuilds waste time when only application code changed
- Build artifacts (compiled code) can be reused across jobs
- Good caching turns a 10-minute pipeline into a 2-minute pipeline

### GitHub Actions Cache
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
    restore-keys: pip-${{ runner.os }}-
```
- Key strategy: hash the lock file — cache invalidates when dependencies change
- Restore keys: fallback to partial match (stale cache is usually better than no cache)
- Size limit: 10GB per repo (GitHub), LRU eviction

### Docker Layer Caching
- BuildKit cache: `cache-from: type=gha` / `cache-to: type=gha,mode=max` (GitHub Actions)
- Registry cache: `cache-from: type=registry,ref=ghcr.io/repo:cache`
- Multi-stage builds: cache the dependency stage separately from the application stage
- Order Dockerfile instructions: least-changing first (OS deps → language deps → app code)

### Language-Specific Caching
- **Node/npm**: cache `~/.npm` or `node_modules`, key on `package-lock.json`
- **Python/pip**: cache `~/.cache/pip`, key on `requirements.txt` or `poetry.lock`
- **Go**: cache `~/go/pkg/mod`, key on `go.sum`
- **Rust**: cache `~/.cargo` and `target/`, key on `Cargo.lock`

## Container Registry

### Options
- **GHCR (GitHub Container Registry)**: free for public repos, integrated with GitHub Actions
- **Zot**: lightweight OCI-compliant registry, self-hosted, minimal resources
- **Harbor**: enterprise features (vulnerability scanning, replication, RBAC)
- **Docker Hub**: default registry, rate limited on free tier
- **Forgejo packages**: built-in container registry in Forgejo

### Self-Hosted Registry (Zot)
```yaml
# docker-compose.yml
services:
  registry:
    image: ghcr.io/project-zot/zot-linux-amd64:latest
    ports:
      - "5000:5000"
    volumes:
      - ./zot-data:/var/lib/registry
      - ./zot-config.json:/etc/zot/config.json
```
- Why self-host: no rate limits, faster pulls on local network, store private images, works when internet is down
- Tag strategy: `<registry>/<project>:<git-sha>` for traceability, plus `:latest` or `:v1.2.3` for convenience

### Image Tagging Strategy
- **Git SHA**: `myapp:abc123f` — every commit gets a unique, traceable tag
- **Semantic version**: `myapp:1.2.3` — for releases
- **Branch**: `myapp:main` — mutable, always points to latest build from branch
- **Latest**: `myapp:latest` — convenient but dangerous (ambiguous, not reproducible)
- Best practice: always tag with SHA, optionally add semver on release

## Multi-Environment Promotion

### Pattern: Build Once, Deploy Many
```
main push → Build image → Push to registry → Deploy to staging
                                             ↓ (manual approval)
                                           Deploy to production
```
- Same image artifact promoted through environments (never rebuild for production)
- Environment-specific config via env vars or config files (not baked into image)
- GitHub environments: require approvals, restrict secrets to specific environments

### Environment Configuration
```yaml
deploy-production:
  needs: deploy-staging
  runs-on: self-hosted
  environment:
    name: production
    url: https://app.example.com
  steps:
    - name: Deploy
      env:
        DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
      run: ./deploy.sh production ${{ github.sha }}
```

### Promotion Strategies
- **Automatic**: staging deploys on merge, production after staging health check passes
- **Manual gate**: require human approval in GitHub/Forgejo UI before production deploy
- **Canary**: deploy to subset of production, monitor, expand or rollback
- **Blue-green**: deploy to inactive environment, switch traffic, keep old as rollback

## Release Automation

### Semantic Release
- Analyzes commit messages (conventional commits) → determines version bump → creates tag + release
- `semantic-release` (npm) or `python-semantic-release`
- Commit mapping: `feat:` → minor, `fix:` → patch, `BREAKING CHANGE:` → major
- Generates changelog automatically from commit messages

### Release Workflow
```yaml
release:
  needs: build
  if: github.ref == 'refs/heads/main'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for changelog
    - name: Semantic Release
      uses: cycjimmy/semantic-release-action@v4
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Tag-Triggered Deploys
- Push git tag → triggers release workflow → builds final artifact → deploys to production
- Pattern: `v*` tag trigger builds the release image and deploys
- Advantage: explicit human decision to release (tag creation)

## Pipeline Security

### Secrets Management
- GitHub: repository or organization secrets, environment-scoped secrets
- Never echo secrets in logs (GitHub auto-masks, but be careful with indirect exposure)
- Rotate secrets regularly, use OIDC where possible (no stored secrets)
- Least privilege: each environment's secrets only accessible to that environment's jobs

### OIDC / Workload Identity
- Pipeline authenticates to cloud/registry without stored secrets
- GitHub Actions: built-in OIDC provider → exchange for cloud credentials
- Forgejo: similar OIDC support for compatible providers
- Why: no secret rotation needed, tokens are short-lived, auditable

### Supply Chain Security
- Pin action versions to SHA: `actions/checkout@<commit-sha>` (not `@v4` which is mutable)
- Dependabot for action version updates
- Sign container images (cosign/sigstore)
- SBOM (Software Bill of Materials): generate with Syft, attach to release
- Scan images in pipeline: Trivy/Grype before push to registry

### Workflow Permissions
```yaml
permissions:
  contents: read
  packages: write  # Only what's needed
```
- Always set explicit permissions (don't use default broad permissions)
- `GITHUB_TOKEN` scoping: limit to minimum required permissions per job

## Debugging Failing Pipelines

### Common Failures and Fixes
- **"Permission denied"**: check file permissions, runner user, Docker socket access
- **"Command not found"**: missing setup step, wrong runner image, tool not installed
- **"Out of disk space"**: clean up Docker images, prune caches, increase runner storage
- **"Cache miss every time"**: wrong cache key (not matching lock file hash), cache evicted
- **"Timeout"**: tests hanging, network timeout, increase job timeout, add step timeouts
- **"Works locally, fails in CI"**: environment difference — check Node/Python version, OS, env vars
- **"Docker build slow"**: missing layer cache, wrong instruction order, large context

### Debugging Techniques
- **Step-level debugging**: add `run: env` to see environment, `run: ls -la` to check files
- **SSH into runner**: some CI systems support debug SSH session for failing runs
- **Local reproduction**: use `act` (GitHub Actions) or Docker to replicate CI environment
- **Verbose output**: `--verbose` flags on build tools, `set -x` in shell scripts
- **Re-run with debug logging**: GitHub Actions has "Re-run with debug logging" option

### Pipeline Optimization Checklist
- [ ] Jobs that can run in parallel ARE parallel (not sequential)
- [ ] Dependency caching enabled and hitting (check cache hit rate)
- [ ] Docker builds use layer caching (BuildKit + cache mount)
- [ ] Fail-fast: cheapest checks run first
- [ ] Concurrency group cancels superseded runs
- [ ] No unnecessary steps (remove debug steps before merge)
- [ ] Self-hosted runners for frequently-run pipelines
- [ ] Matrix builds for multi-platform/version testing
