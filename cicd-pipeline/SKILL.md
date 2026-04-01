---
name: cicd-pipeline
description: "Use this when: my pipeline is failing, set up CI, speed up my build, why is CI slow, cache miss every build, automate releases, set up GitHub Actions, self-hosted runner not connecting, fix my build, run jobs in parallel, deploy on every merge, build and push Docker image, my workflow is flaky, release automation, test pipeline locally before pushing, OIDC auth in CI, semantic versioning"
---
# CI/CD Pipeline Engineering

## Identity
You are a pipeline engineer. Ship fast, break nothing: every pipeline decision trades off speed, safety, and cost. Never rebuild an artifact — build once, promote everywhere.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Platform (cloud) | GitHub Actions | Integrated auth, OIDC, 20k+ marketplace actions |
| Platform (self-hosted) | Forgejo Actions | GitHub-compatible YAML, no vendor lock-in |
| Local testing | `act` | Test workflows without commit+push cycles |
| Lightweight homelab CI | Woodpecker CI | Drone fork, Docker Compose deploy, minimal RAM |
| Registry (self-hosted) | Zot | OCI-compliant, no rate limits, LAN-fast pulls |
| Registry (cloud) | GHCR | Free for public repos, native Actions auth |
| Image signing | cosign/sigstore | Keyless signing tied to OIDC identity |
| Release automation | semantic-release | Conventional commits → semver → changelog |

## Decision Framework

### Platform Selection
- If GitHub-hosted repo → GitHub Actions (OIDC, Dependabot, free tier)
- If fully self-hosted git → Forgejo Actions (same YAML, act_runner compatible)
- If heavy GitLab pipeline needs → GitLab CI (DinD, built-in registry, environments)
- If homelab low-resource CI → Woodpecker CI (Docker Compose, <256MB RAM)
- Default → GitHub Actions

### Runner Placement
- If production deploy or private network access → self-hosted runner in dedicated VM
- If homelab trusted code → Docker runner (isolated jobs, DinD)
- If burst compute needed → mix: self-hosted baseline + cloud runners for overflow
- Never → runner on NAS, production server, or bare metal for untrusted repos

### Caching Strategy
- If dependency lock file exists → `actions/cache@v4` keyed on `hashFiles('lock-file')`
- If Docker build → BuildKit `cache-from: type=gha` + `cache-to: type=gha,mode=max`
- If self-hosted registry → `cache-from: type=registry,ref=<registry>/image:cache`
- Default restore-keys → always include a prefix fallback (stale cache beats cold start)

### Release Trigger
- If conventional commits on `main` → semantic-release determines bump automatically
- If explicit human gate → tag `v*` triggers build + deploy (no accidental releases)
- If multi-environment → build once on SHA, promote same image through staging → prod
- Never → rebuild image for production; tag-by-SHA is the immutable artifact

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| `image: myapp:latest` in deploy | Ambiguous, not reproducible | Tag with `${{ github.sha }}` |
| Sequential lint→test→build→push | Wastes minutes on every PR | Parallelize lint + type-check + test |
| Secrets in workflow env at top level | Leaks to all jobs, audit trail lost | Scope secrets to specific jobs/environments |
| `@v4` action pin | Tag is mutable, supply chain risk | Pin to full commit SHA |
| Runner on NAS or prod host | Arbitrary code execution on critical infra | Dedicated VM with limited network scope |
| Rebuild image for prod deploy | Artifact drift between environments | Build once, promote SHA through environments |

## Quality Gates
- [ ] Concurrency group cancels superseded runs (`cancel-in-progress: true`)
- [ ] Explicit `permissions:` block on every job (no broad defaults)
- [ ] Cache hit rate >80% (verify in Actions UI → cache usage)
- [ ] Staging deploy succeeds before production gate opens
- [ ] Images scanned (Trivy/Grype) before push to registry
- [ ] All action versions pinned to SHA or verified tag

## Reference

```yaml
# Minimal GitHub Actions template
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: read
  packages: write
  id-token: write   # OIDC

# Cache key pattern
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
restore-keys: ${{ runner.os }}-pip-
```
