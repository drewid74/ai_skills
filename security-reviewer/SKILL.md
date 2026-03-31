---
name: security-reviewer
description: "Use this skill whenever the user wants to audit, harden, or assess the security of code, infrastructure, containers, networks, or deployments. Triggers include: any mention of 'security audit', 'security review', 'vulnerability', 'CVE', 'penetration test', 'pentest', 'hardening', 'CIS benchmark', 'OWASP', 'OWASP Top 10', 'injection', 'XSS', 'CSRF', 'SSRF', 'authentication', 'authorization', 'RBAC', 'zero trust', 'TLS', 'SSL', 'certificate', 'encryption', 'secrets management', 'Vault', 'firewall rules', 'iptables', 'nftables', 'UFW', 'fail2ban', 'intrusion detection', 'IDS', 'SIEM', 'log analysis', 'supply chain security', 'dependency audit', 'container security', 'Docker security', 'image scanning', 'Trivy', 'Grype', 'network segmentation', 'VLAN security', 'SSH hardening', 'API security', 'rate limiting', 'CORS', 'CSP', 'security headers', or any request to check if something is secure, find vulnerabilities, or improve security posture. Also use when the user is setting up authentication, managing certificates, configuring firewalls, or asking 'is this safe?'. If someone describes infrastructure and you notice security concerns, use this skill proactively."
---

# Security Auditing & Hardening

## Overview

Systematic security review methodology covering application code, container images, infrastructure, networks, and operational security. Organized by attack surface with practical remediation steps.

---

## Application Security (OWASP Top 10)

### Injection (SQL, Command, LDAP, NoSQL)

**Why it matters:** Attackers execute arbitrary code or access unauthorized data.

- **SQL injection:** Use parameterized queries, never string concatenation.
  ```sql
  -- BAD: cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
  -- GOOD: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
  ```
- **Command injection:** Use subprocess with array args, never `shell=True` with user input.
  ```python
  # BAD: os.system(f"ping {hostname}")
  # GOOD: subprocess.run(["ping", "-c", "1", hostname])
  ```
- **NoSQL injection:** Validate query operators; reject `$where`, `$expr` from user input.
- **Template injection:** Use auto-escaping engines (Jinja2 `autoescape=True`, React JSX).
- Detection: Search for string formatting near database calls or exec functions.

### Broken Authentication

**Why it matters:** Attackers impersonate users or bypass login entirely.

- **Password storage:** bcrypt, argon2, or scrypt. Never MD5, SHA1, plaintext.
  ```python
  import bcrypt
  hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
  ```
- **Session management:** Secure, httpOnly, sameSite cookies; rotate session IDs on login.
  ```
  Set-Cookie: sessionid=abc123; Secure; HttpOnly; SameSite=Strict; Max-Age=1800
  ```
- **Token handling:** JWTs with short expiry (15-60 min), validate signature + expiry + issuer.
- **Multi-factor authentication:** TOTP (Google Authenticator), WebAuthn/FIDO2.
- **Rate limiting:** Throttle login endpoints to 5 attempts per 15 minutes.
- **Account lockout:** Lock after N failed attempts (15-30 min duration, not permanent).

### Sensitive Data Exposure

**Why it matters:** Encrypted data at transit is useless if exposure happens at rest or in logs.

- **TLS everywhere:** HTTPS for all endpoints, `HSTS` header with `max-age=31536000`.
- **Encryption at rest:** Database column encryption, encrypted volumes for backups.
- **Data classification:** Identify PII, financial data, credentials — apply appropriate protections.
- **Minimize collection:** Don't store what you don't need.
- **Redaction in logs:** Mask passwords, tokens, card numbers, SSN using regex patterns.

### Broken Access Control

**Why it matters:** Users access data or features they shouldn't.

- **Server-side authorization:** Check permissions on EVERY request (never trust client-side only).
- **Resource-level checks:** User A cannot access user B's data via ID guessing.
  ```python
  def get_user_data(user_id, request_user_id):
      if user_id != request_user_id: raise PermissionError()
  ```
- **RBAC:** Define roles (admin, user, viewer), assign permissions explicitly.
- **API:** Verify ownership for CRUD operations on protected resources.
- **Directory traversal:** Validate and canonicalize file paths (`os.path.abspath`).

### XSS (Cross-Site Scripting)

**Why it matters:** Attackers inject scripts that run in victim browsers, stealing sessions or data.

- **Output encoding:** HTML-encode user data before rendering.
  ```python
  # Python: use flask.escape() or jinja2 autoescape
  # JS: textContent instead of innerHTML for user data
  ```
- **Content Security Policy (CSP):** Restrict script sources.
  ```
  Content-Security-Policy: default-src 'self'; script-src 'self'
  ```
- **Framework defaults:** React, Vue, Angular auto-escape by default — avoid `dangerouslySetInnerHTML`, `v-html`.
- **Rich text:** Use DOMPurify (JS) or bleach (Python) for sanitization.

### CSRF (Cross-Site Request Forgery)

**Why it matters:** Attackers trick users into taking actions on their behalf.

- **Anti-CSRF tokens:** Include on all state-changing forms, validate server-side.
- **SameSite cookies:** `SameSite=Strict` or `Lax` to prevent cross-site requests.
- **Verify Origin/Referer:** Check request headers for API endpoints.
- **Double-submit cookie:** For SPAs, token in cookie + request body/header must match.

### SSRF (Server-Side Request Forgery)

**Why it matters:** Attackers make your server request internal services, bypassing firewall.

- **Allowlist URLs:** Validate and allowlist destinations your server can fetch.
- **Block internal IPs:** Reject requests to `10.x`, `172.16-31.x`, `192.168.x`, `127.x`, `169.254.x`.
- **Allowlist, not blocklist:** Explicit allowlists are more secure than trying to block all bad IPs.
- **DNS rebinding protection:** Resolve and validate IP before connecting.

---

## Container Security

### Image Security

**Why it matters:** Compromised images deploy compromise to all containers.

- **Minimal base images:** Use alpine, distroless, or slim. Smaller = smaller attack surface.
  ```dockerfile
  FROM alpine:3.19  # ~5 MB vs 150 MB for ubuntu
  ```
- **Pin image digests:** Reference by digest, not `:latest`, for reproducibility.
  ```dockerfile
  FROM alpine@sha256:abc123def456...
  ```
- **Scanning tools:** Trivy, Grype, Snyk in CI before deploy.
  ```bash
  trivy image --severity HIGH,CRITICAL my-image:latest
  ```
- **Multi-stage builds:** Build in one stage, copy only artifacts to runtime (no compilers in prod).
- **Run as nonroot:** Add `USER nonroot` in Dockerfile (prevents privilege escalation).

### Docker Daemon Security

**Why it matters:** Docker socket access = root access to host.

- **Avoid mounting `/var/run/docker.sock`** unless absolutely necessary.
- **Read-only filesystems:** Use `--read-only` to prevent container from writing.
- **Resource limits:** CPU and memory quotas prevent resource exhaustion attacks.
  ```bash
  docker run --memory=512m --cpus=1 my-app
  ```
- **No `--privileged` flag** unless explicitly required and understood.
- **Seccomp profiles:** Use default or custom restricted profiles to limit system calls.
- **AppArmor/SELinux:** Enable for additional containment on host.

### Docker Compose Security

**Why it matters:** Compose files can expose services unintentionally.

- **Port binding:** Use `127.0.0.1:8080:80`, not `0.0.0.0:8080:80` to restrict to localhost.
- **Custom networks:** Don't use default bridge; create isolated networks.
- **Secrets:** Use Docker secrets or .env files (never in compose file).
- **Health checks:** Detect compromised or failing containers early.
- **Read-only root:** `read_only: true` in service definition.

---

## Infrastructure Security

### SSH Hardening

**Why it matters:** SSH is a primary attack vector for remote compromise.

```bash
# /etc/ssh/sshd_config
PasswordAuthentication no
PermitRootLogin no
AllowUsers deploy admin
Port 22  # optional, reduces noise but not true security
Protocol 2
X11Forwarding no
MaxAuthTries 3
MaxSessions 5
LoginGraceTime 30
```

- **Key-based auth only:** Disable password login.
- **Disable root:** Use a deploy user with sudo for privilege escalation.
- **Fail2ban:** Brute force protection — ban IPs after N failed attempts.
  ```bash
  apt install fail2ban
  systemctl enable fail2ban
  ```
- **Ed25519 keys:** Shorter, faster, more secure than RSA.
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
  ```

### Firewall Configuration

**Why it matters:** Firewall is your first line of defense against network attacks.

```bash
# UFW quick setup
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 443/tcp
ufw limit 22/tcp  # rate limit SSH
ufw enable
```

- **Default deny inbound:** Only allow specific ports.
- **nftables/iptables:** For granular control (VLANs, port knocking, NAT).
- **Restrict management:** Management interfaces only from management VLAN/IP.
- **Egress filtering:** Restrict outbound connections to necessary destinations (prevents data exfil).

### Network Segmentation

**Why it matters:** One compromised device shouldn't compromise your entire network.

- **VLANs:** Separate management, services, IoT, guest, DMZ.
- **No cross-VLAN traffic:** Require explicit firewall rules.
- **DMZ for public services:** Web servers, APIs — not internal databases.
- **Internal services:** Unreachable from internet (only via VPN or bastion host).

### TLS / Certificate Management

**Why it matters:** Unencrypted traffic is readable to anyone on the network.

- **Let's Encrypt:** Free, automated certificates via ACME.
  ```bash
  certbot certonly --standalone -d example.com
  ```
- **Internal CA:** Use for internal services (don't use self-signed in production).
- **Automation:** Tools like cert-manager (k8s) or letsencrypt renewal scripts.
- **TLS 1.2 minimum:** Disable TLS 1.0, 1.1, SSLv3.
- **Strong ciphers:** ECDHE-ECDSA-AES256-GCM-SHA384, ChaCha20-Poly1305.
- **HSTS:** `Strict-Transport-Security: max-age=31536000; includeSubDomains`

---

## Security Headers

Set these on all web services:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

---

## Secrets Management

**Why it matters:** Hardcoded secrets are found, exploited, rotated at scale with difficulty.

- **Environment variables:** Minimum viable; better than hardcoding.
- **HashiCorp Vault:** Enterprise-grade, dynamic secrets, auto-rotation, audit logs.
- **Docker secrets:** Swarm/compose — mounted as files, not env vars.
- **Cloud-native:** AWS Secrets Manager, GCP Secret Manager, Azure Key Vault.
- **SOPS:** Encrypts files with age/PGP/KMS — good for git-stored secrets.
- **Rotation:** Automate credential rotation (databases, API keys, certificates).
- **Audit:** Log every secret access for compliance.

---

## Dependency & Supply Chain Security

**Why it matters:** Dependencies are attack vectors; ransomware and malware hide in packages.

- **Pin versions:** Lock files (`package-lock.json`, `poetry.lock`, `Cargo.lock`) committed to git.
- **Regular audits:** `npm audit`, `pip-audit`, `cargo audit`, `go mod tidy`.
- **Dependabot/Renovate:** Automated update PRs with security info.
- **Verify integrity:** Check package signatures, checksums.
- **Reduce dependencies:** Fewer deps = smaller attack surface.
- **Review before adding:** Popularity, maintenance status, known vulnerabilities.

---

## Security Scanning Pipeline

Run these in CI:

- **SAST (Static):** CodeQL, Semgrep, Bandit (Python), ESLint security plugin.
- **DAST (Dynamic):** OWASP ZAP, Nikto — test running application.
- **SCA (Dependencies):** Snyk, npm audit, pip-audit.
- **Container scanning:** Trivy, Grype in CI before push.
- **IaC scanning:** Checkov, tfsec for Terraform/CloudFormation misconfigs.
- **Fail on high/critical:** Set CI jobs to fail on severity threshold.

---

## Monitoring & Incident Response

**Why it matters:** Detection speed determines blast radius.

- **Centralized logging:** Loki, Elasticsearch, Graylog — enable searchability.
- **Log auth events:** Logins, failures, privilege escalation, secret access.
- **Alerting on anomalies:** Unusual access patterns, error spikes, new admin accounts.
- **Incident response plan:** Detection → containment → eradication → recovery → post-mortem.
- **Tested backups:** Ransomware recovery depends on this.

---

## Quick Security Audit Checklist

- [ ] Passwords hashed with bcrypt/argon2 (not MD5/SHA1)
- [ ] TLS on all external-facing services, HSTS header set
- [ ] SSH key-only auth, root login disabled, fail2ban enabled
- [ ] Firewall default-deny with explicit allowlist
- [ ] Container images scanned, no critical CVEs
- [ ] No secrets in code, git history, or environment
- [ ] Security headers set on all web services
- [ ] Dependencies audited, up to date
- [ ] Backups exist and tested for recovery
- [ ] Network segmented (management, services, IoT separate)
- [ ] Logging and alerting configured for anomalies
- [ ] MFA enabled for admin/privileged accounts
