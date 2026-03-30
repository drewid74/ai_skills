---
name: docker-selfhost
description: "Use this skill whenever the user wants to work with Docker, Docker Compose, containers, TrueNAS Scale, self-hosted services, or home lab infrastructure. Triggers include: any mention of 'docker', 'container', 'compose', 'docker-compose', 'docker compose', 'TrueNAS', 'self-hosted', 'home lab', 'homelab', 'reverse proxy', 'Traefik', 'nginx proxy manager', 'Portainer', 'Watchtower', 'Cloudflare tunnel', or requests to deploy, migrate, or configure services for home hosting. Also use when converting between hosting platforms (cloud to self-hosted), setting up networking between containers, configuring persistent storage/volumes, or troubleshooting container issues. If the user mentions any service name commonly self-hosted (Jellyfin, Nextcloud, Home Assistant, Pi-hole, Plex, Immich, Vaultwarden, Gitea, etc.), use this skill."
---

# Docker & Self-Hosting Skill

## Overview

Help users create, manage, troubleshoot, and optimize Docker containers and self-hosted services, with particular focus on Docker Compose workflows and TrueNAS Scale deployments.

## Core Principles

1. **Compose-first**: Always prefer Docker Compose over raw `docker run` commands. Compose files are version-controlled, reproducible, and self-documenting.
2. **Security by default**: Never expose management ports to the internet. Use non-root users in containers where possible. Always set restart policies.
3. **Persistence matters**: Always define named volumes or bind mounts for data that must survive container recreation.
4. **Network isolation**: Use custom Docker networks. Don't put everything on the default bridge.

## Docker Compose Generation

When generating a `docker-compose.yml`:

### Structure Template
```yaml
version: "3.8"  # or omit for modern Docker Compose v2

services:
  service-name:
    image: image:tag        # Always pin a specific tag, never use :latest in production
    container_name: service-name
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/Chicago   # Ask user for their timezone
    volumes:
      - ./config:/config     # Config persistence
      - /path/to/data:/data  # Data persistence
    ports:
      - "8080:80"            # host:container
    networks:
      - proxy                # Custom network for reverse proxy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  proxy:
    external: true           # Created separately for shared reverse proxy
```

### Key Patterns

**Multi-service stacks**: Group related services in one compose file (e.g., app + database + cache). Use `depends_on` with health checks.

**Environment variables**: Use `.env` files for secrets. Never hardcode passwords in compose files. Reference with `${VARIABLE}`.

**Reverse proxy integration**: Always include labels or config for the user's reverse proxy (Traefik labels, nginx upstream blocks, or Cloudflare tunnel config).

## TrueNAS Scale Specifics

TrueNAS Scale runs containers differently than vanilla Docker:

- **Apps system**: TrueNAS uses a Kubernetes-based app system (previously used Docker Compose in older versions). For SCALE 24.10+, TrueNAS moved to Docker Compose natively.
- **Storage paths**: Data typically lives under `/mnt/pool-name/dataset-name/`. Always ask the user for their pool/dataset structure.
- **Networking**: TrueNAS handles networking through its own bridge. Host networking mode is often needed for services that require mDNS or DLNA (like Plex, Home Assistant).
- **GPU passthrough**: For transcoding (Jellyfin/Plex), include device mappings:
  ```yaml
  devices:
    - /dev/dri:/dev/dri    # Intel QuickSync
  ```

## Common Self-Hosted Service Patterns

### Media Stack
Jellyfin/Plex + Sonarr + Radarr + Prowlarr + qBittorrent/SABnzbd + Overseerr

### Productivity Stack
Nextcloud + Collabora/OnlyOffice + Redis + MariaDB/PostgreSQL

### Home Automation
Home Assistant + Mosquitto MQTT + Zigbee2MQTT + Node-RED + ESPHome

### Network & Security
Pi-hole/AdGuard Home + WireGuard/Tailscale + Uptime Kuma + Authelia/Authentik

### Dev Tools
Gitea/Forgejo + Drone CI + Portainer + Watchtower

## Migration Workflows

When migrating from cloud to self-hosted:

1. **Inventory**: List all cloud services and their self-hosted equivalents
2. **Data export**: Generate scripts to export data from cloud services
3. **Compose generation**: Build the compose stack with proper networking
4. **DNS/proxy config**: Set up reverse proxy and DNS records
5. **Testing**: Verify services work before cutting over DNS
6. **Backup strategy**: Set up automated backups before going live

## Troubleshooting Guide

When a container isn't working:

1. Check logs: `docker logs container-name --tail 100`
2. Check status: `docker ps -a` (look for restart loops)
3. Check networking: `docker network inspect network-name`
4. Check volumes: `docker volume inspect volume-name`
5. Check permissions: Verify PUID/PGID match the host user owning the data directories
6. Check resources: `docker stats` for CPU/memory issues

### Common Issues
- **Permission denied on volumes**: PUID/PGID mismatch or SELinux (add `:z` or `:Z` suffix)
- **Container restart loop**: Check logs for missing env vars or config files
- **Can't reach service**: Verify port mapping, firewall rules, and container is on the right network
- **DNS resolution between containers**: Use container names as hostnames on the same Docker network

## Backup Best Practices

Always recommend a backup strategy:
- **Config**: Git-track compose files and .env templates (not secrets)
- **Data**: Automated rsync, restic, or borgbackup to a separate location
- **Databases**: `docker exec` cron jobs for pg_dump / mysqldump before file-level backup
- **Testing restores**: A backup that hasn't been tested is not a backup

## Output Format

When generating Docker Compose configurations:
1. Provide the complete `docker-compose.yml`
2. Provide a companion `.env.example` with all required variables documented
3. Include setup instructions (network creation, directory structure, etc.)
4. Note any post-deployment steps (initial admin setup, API key generation, etc.)
