---
name: Security Compliance Officer
description: "🛡️ URGENT: Security audit needed! Code review, vulnerability scanning, compliance checks, secrets detection, container hardening, certificate lifecycle, incident forensics, supply chain verification—deploy this comprehensive audit framework NOW to harden your infrastructure."
trigger_keywords:
  - security audit
  - vulnerability scan
  - secrets leak
  - container security
  - compliance check
  - CVE detection
  - certificate expiration
  - incident forensics
  - SBOM generation
  - supply chain security
  - secrets rotation
  - Docker hardening
tags:
  - security
  - compliance
  - devops
  - incident-response
category: Security & Compliance
---

# Security Compliance Officer

Enterprise-grade security specialist combining threat detection, compliance automation, incident response, and supply chain verification. This skill absorbs OWASP patterns and expands into production-grade security operations.

## Core Mission

**WHY this exists:** Security isn't reactive—it's architectural. This skill operationalizes security across:
- Code & dependency safety (injection, XSS, CSRF, vulnerable dependencies)
- Infrastructure hardening (containers, TLS, secrets, networks)
- Compliance automation (CIS benchmarks, audit trails)
- Incident response (forensics, containment, recovery)
- Supply chain integrity (SBOM, signatures, provenance)

## OWASP Top 10: Application Security Fundamentals

**SQL/NoSQL Injection:** Use parameterized queries, prepared statements, and ORM frameworks. Never concatenate user input into queries. For NoSQL, validate/sanitize all user input before database operations. Test with SQLi payloads like `' OR '1'='1`.

**Cross-Site Scripting (XSS):** Encode all user-supplied data on output using context-aware encoding (HTML, JS, URL, CSS). Use DOMPurify or similar for sanitizing untrusted HTML. Set `Content-Security-Policy: script-src 'self'` to block inline/external scripts unless whitelisted.

**Cross-Site Request Forgery (CSRF):** Issue anti-CSRF tokens unique per session/request. Validate token on state-changing requests (POST, PUT, DELETE). Set SameSite=Strict on session cookies to prevent cross-origin cookie sending. Use double-submit cookie pattern as fallback.

**Server-Side Request Forgery (SSRF):** Never allow user-supplied URLs to reach outbound requests without validation. Maintain allowlist of permitted domains/IPs. Disable access to metadata endpoints (169.254.169.254). Reject requests to private IP ranges (10.0.0.0/8, 127.0.0.0/8, 172.16.0.0/12).

**Broken Authentication:** Use strong hashing (bcrypt, argon2). Enforce multi-factor authentication (TOTP, WebAuthn). Implement account lockout after failed attempts. Log all auth failures with IP/timestamp. Use short-lived session tokens with signature validation.

**Broken Access Control:** Default-deny all resources; grant permissions explicitly. Use role-based access control (RBAC) or attribute-based (ABAC). Validate permissions on every request, server-side. Audit access changes. Never trust client-provided roles/permissions.

## HTTP Security Headers: Response Hardening

**Content-Security-Policy (CSP):** Whitelist trusted sources for scripts, styles, images, fonts. Example: `Content-Security-Policy: default-src 'self'; script-src 'self' cdn.example.com; img-src * data:`. Prevents XSS and inline script injection. Use nonce-based or hash-based CSP for strict mode.

**X-Content-Type-Options:** Set to `nosniff` to prevent MIME-sniffing attacks. Browsers will respect declared Content-Type and not guess (e.g., treat .js as HTML). Simple but effective against polyglot file attacks.

**X-Frame-Options:** Set to `DENY` (never embed in frame) or `SAMEORIGIN` (allow same-site framing only). Prevents clickjacking attacks where attacker invisibly frames your login page over theirs. `DENY` is most secure.

**Referrer-Policy:** Set to `strict-origin-when-cross-origin` or `no-referrer` to control what referrer info is sent. Prevents leaking sensitive URL parameters to third-party sites when users click off-site.

**Permissions-Policy:** (formerly Feature-Policy) Controls browser features available to scripts (camera, microphone, geolocation, payment APIs). Example: `Permissions-Policy: geolocation=(), microphone=(), camera=()`. Reduces attack surface if code is compromised.

## Section 1: Secrets Management & Rotation

### Pattern: .env Lifecycle & Rotation Automation

**WHY:** Plaintext secrets in code/configs are the #1 breach vector. Automation prevents human error and enforces rotation windows.

```bash
# .env.example (NEVER commit real values)
DATABASE_URL=postgres://user:PASSWORD@localhost/db
API_KEY=sk_live_XXXXX
SLACK_TOKEN=xoxb-XXXXX
JWT_SECRET=your-secret-here

# Rotation script (run weekly)
#!/bin/bash
set -euo pipefail

VAULT_ADDR="https://vault.company.com"
SECRETS_PATH="secret/prod/app"

# Rotate each secret
for secret in DATABASE_PASSWORD API_KEY SLACK_TOKEN JWT_SECRET; do
  NEW_VALUE=$(openssl rand -hex 32)
  curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d "{\"data\":{\"$secret\":\"$NEW_VALUE\"}}" \
    "$VAULT_ADDR/v1/$SECRETS_PATH" | jq .
  
  # Deploy updated config
  kubectl create secret generic app-secrets \
    --from-literal=$secret=$NEW_VALUE --dry-run=client -o yaml | kubectl apply -f -
done
```

**Why rotation matters:** If a key is exposed or employee leaves, rotating invalidates old credentials instantly. Automation removes the friction that causes delays.

### Pattern: Leak Detection (trufflehog + gitleaks)

**WHY:** Secrets are committed despite .gitignore. Automated scanning catches leaks before they reach production.

```bash
# Install & scan
pip install trufflehog
trufflehog github --repo https://github.com/owner/repo --json > secrets.json

# CI/CD integration (GitHub Actions)
name: Secret Scanning
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Run TruffleHog
        run: |
          pip install trufflehog
          trufflehog filesystem . --json > results.json
          if grep -q '"verified": true' results.json; then
            echo "VERIFIED SECRETS FOUND!"
            exit 1
          fi
      
      - name: Run gitleaks
        run: |
          docker run -v $(pwd):/path zricethezav/gitleaks:latest detect \
            --source /path --verbose --exit-code 1
```

**Why CI/CD integration:** Detection at commit time, before push, prevents exposure. Failed secrets in PR history are still exposed; preventing the commit stops it cold.

### Pattern: Vault/Bitwarden Integration

**WHY:** Centralized secret storage enforces access control, audit logs, and encryption at rest.

```python
# Vault integration (HCP Vault or self-hosted)
import hvac

client = hvac.Client(url='https://vault.company.com', token=os.environ['VAULT_TOKEN'])

# Read secret
secret = client.secrets.kv.v2.read_secret_version(path='prod/database')
db_url = secret['data']['data']['DATABASE_URL']

# Rotate secret server-side
client.secrets.kv.v2.update_secret_version(
    path='prod/database',
    secret_data={'DATABASE_URL': new_url, 'PASSWORD': new_pass}
)

# Audit trail - who accessed what, when
auth_history = client.auth.token.lookup(token='s.XXXXX')
print(auth_history['data']['policies'])  # Permissions tied to identity
```

**Why Vault:** Secrets never stored in code/config. Tokens are short-lived. Audit logs track every access. Access revoked instantly when needed.

## Authentication Deep Dive: Password Hashing & MFA

**Password Hashing:** Use bcrypt, argon2, or scrypt—never MD5/SHA1. Bcrypt automatically handles salt/iterations; argon2 is slower (resists GPU brute-force). Example: `password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))`. Verify at login: `bcrypt.checkpw(input.encode(), stored_hash)`. Never store plaintext; never use simple salt.

**JWT Best Practices:** Issue short-lived tokens (15min-1hr expiry). Validate signature before trusting claims: `jwt.decode(token, secret, algorithms=['HS256'])`. Include user ID, role, scope in payload. Use RS256 (asymmetric) for multi-service systems (verify with public key). Revocation: maintain a blacklist/blocklist of revoked tokens with their expiry time.

**Multi-Factor Authentication (MFA):** Implement TOTP (Time-based One-Time Password) using apps like Google Authenticator; users scan QR code, app generates 6-digit codes every 30sec. For stronger security, use WebAuthn (FIDO2): passwordless registration/login via hardware keys or platform authenticators. Backup codes for account recovery without hardware.

**Session Cookie Flags:** Set `Secure` flag (HTTPS only), `HttpOnly` flag (no JavaScript access), `SameSite=Strict` (never sent cross-origin). Together: `Set-Cookie: sessionid=abc123; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600`. Prevents cookie theft, XSS exfiltration, and CSRF.

## Section 2: Dependency CVE Scanning

### Pattern: Real-time Vulnerability Detection

**WHY:** Known CVEs in dependencies are exploitable today. Automation catches them before deployment.

```bash
# npm/Node.js
npm audit --audit-level=moderate
npm audit fix --force  # Auto-apply patches

# Python/pip
pip install safety
safety check --json > vulns.json

# Go
go list -json ./... | nancy sleuth --json

# Rust
cargo audit --deny warnings
```

**CI/CD automation (pre-commit):**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Lucas-C/pre-commit-hooks-safety
    rev: v1.3.1
    hooks:
      - id: python-safety-dependencies-check

  - repo: https://github.com/aquasecurity/trivy
    rev: v0.40.0
    hooks:
      - id: trivy
```

### Pattern: Automated PR Creation for Fixes

**WHY:** Manual dependency updates lag behind patches. Automated PRs keep fixes in the pipeline immediately.

```python
# dependabot.yml (GitHub) - automated PRs for package updates
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "daily"
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
    pull-request-branch-name:
      separator: "/"
    open-pull-requests-limit: 5
    auto-commit-metadata: true
  
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
```

**Why automated PRs:** Eliminates delay between patch release and deployment. Enables fast-track merge for critical CVEs while maintaining testing gates.

### Pattern: Language-Specific Dependency Auditing Expansion

**WHY:** Each language ecosystem has preferred tools; lock files enforce reproducibility.

```bash
# Python
pip-audit --fix  # Audit pip packages, auto-fix vulnerabilities
pip install pip-tools && pip-compile requirements.in  # Lock file generation

# Rust
cargo audit --deny warnings  # Scan Cargo.lock
cargo update && cargo audit  # Update and re-check

# Go
go mod tidy && nancy sleuth  # Tidy modules, scan with nancy
govulncheck ./...  # Built-in vulnerability scanning (Go 1.18+)

# All languages: Lock file enforcement (prevent `pip install`, `npm install` without lock)
# CI: pip install -r requirements.lock (not requirements.txt)
# Renovate as Dependabot alternative (more flexible, self-hosted friendly)
```

**Why lock files:** Reproducible builds. CI/prod use exact same versions as tested locally. Prevents supply-chain mutations mid-deployment.

## SAST/DAST & Code Analysis Tools

**Static Analysis (SAST):** Find vulnerabilities before runtime. CodeQL (GitHub): query-based scanning for C, Java, JS; catches injection, path traversal, crypto misuse. Semgrep: lightweight, polyglot, rule-based; fast CI integration. Bandit (Python): security-focused linter for Python code, flags weak crypto, hardcoded secrets.

**Dynamic Analysis (DAST):** Test running app. OWASP ZAP: automated web app scanner; crawls, finds XSS, SQLi, auth bypasses. Run post-deployment or in staging. Configure to scan API endpoints, forms, hidden parameters.

**Infrastructure-as-Code Scanning:** Checkov and tfsec scan Terraform/CloudFormation for misconfigs (open S3 buckets, missing encryption, overpermissive IAM). Integrate into CI: `checkov -d terraform/ --framework terraform --check CKV_AWS_1` to fail on critical issues.

## Section 3: Container Image Hardening

### Pattern: Distroless Builds

**WHY:** Full OS images (alpine ~5MB, ubuntu ~77MB) include shells, package managers, and tools attackers use. Distroless (~10-30MB) removes attack surface.

```dockerfile
# BAD: Full OS image (attack surface)
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl git
COPY app /app
CMD ["python", "app.py"]

# GOOD: Multi-stage distroless (minimal attack surface)
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM gcr.io/distroless/python3-nonroot:nonroot
COPY --from=builder --chown=nonroot:nonroot /root/.local /home/nonroot/.local
COPY --chown=nonroot:nonroot app.py /app/app.py
ENV PATH=/home/nonroot/.local/bin:$PATH
CMD ["app.py"]
```

**Why distroless:** No /bin/sh means attackers can't shell in. No package managers mean post-exploit lateral movement is blocked. 10x smaller = faster deployment & less to patch.

### Pattern: Docker Security Specifics

**WHY:** Docker misconfigurations are common. Socket mounting, resource limits, and filesystem isolation prevent container escape and DoS.

```yaml
# Secure Docker Compose
version: '3.9'
services:
  app:
    image: myapp:latest
    # Dangers: Never mount /var/run/docker.sock (gives host control!)
    # volumes:
    #   - /var/run/docker.sock:/var/run/docker.sock  # DANGER!

    security_opt:
      - no-new-privileges:true  # Prevent privilege escalation
    cap_drop:
      - ALL                     # Drop all capabilities
    cap_add:
      - NET_BIND_SERVICE        # Add back only what's needed

    read_only_root_filesystem: true  # Immutable root
    tmpfs:
      - /tmp
      - /run

    resources:
      limits:
        cpus: '1'               # Prevent CPU DoS
        memory: 512M            # Prevent memory exhaustion
      reservations:
        cpus: '0.5'
        memory: 256M

    networks:
      - app-network             # Custom network isolation
```

**Why socket mounting is dangerous:** `/var/run/docker.sock` gives container full Docker API access. Attacker can spawn privileged containers, mount host filesystem, escape sandbox. Never mount unless absolutely necessary. Resource limits prevent fork-bombs and memory exhaustion. Read-only root + tmpfs for /tmp ensures immutability—attackers can't persist malware.

### Pattern: Layer Analysis & Optimization

**WHY:** Large layers slow builds/deploys and bloat registries. Analysis finds unnecessary bloat.

```bash
# Analyze layer sizes
docker history myapp:latest

# Using Dive for interactive analysis
dive myapp:latest

# Output: Shows each layer, what changed, wasted space
# Layer 1: 150MB (unnecessary dependencies removed)
# Layer 2: 2MB (actual app code)
# Total: 152MB can be reduced to 50MB with multi-stage build
```

### Pattern: Runtime Security (seccomp + AppArmor)

**WHY:** Even in containers, prevent unauthorized syscalls. Blocks exploits at kernel level.

```json
// seccomp profile (only allow required syscalls)
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "archMap": [
    {
      "architecture": "SCMP_ARCH_X86_64",
      "subArchitectures": ["SCMP_ARCH_X86", "SCMP_ARCH_X32"]
    }
  ],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat", "lstat"],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["execve", "fork", "clone"],
      "action": "SCMP_ACT_ERRNO"
    }
  ]
}
```

**Kubernetes deployment:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      seccompProfile:
        type: Localhost
        localhostProfile: my-profile.json
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
```

**Why seccomp:** Reduces exploitable syscalls from 300+ to ~20. Kernel blocks unauthorized calls, preventing privilege escalation.

## Section 4: SSL/Certificate Lifecycle

### Pattern: Let's Encrypt/ACME Automation

**WHY:** Manual certificate renewal causes expiration outages. Automation prevents this.

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate (can be run in automation)
sudo certbot certonly --dns-route53 \
  -d example.com -d "*.example.com" \
  --agree-tos --email admin@example.com

# Auto-renewal (cron)
0 3 * * * certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

### Pattern: Certificate Inventory & Expiration Monitoring

**WHY:** Tracking 100+ certs across services is error-prone. Automation prevents surprise expirations.

```python
import ssl
import socket
from datetime import datetime, timedelta

def check_cert_expiration(hostname, port=443):
    """Check when cert expires"""
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert_der = ssock.getpeercert(binary_form=True)
            cert = ssl.DER_cert_to_PEM_cert(cert_der)
            
            # Parse expiration
            import OpenSSL
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert
            )
            expiry = x509.get_notAfter()  # b'20240501120000Z'
            expiry_date = datetime.strptime(expiry.decode(), '%Y%m%d%H%M%SZ')
            
            days_left = (expiry_date - datetime.utcnow()).days
            if days_left < 30:
                alert(f"{hostname}: Certificate expires in {days_left} days!")
            
            return {"hostname": hostname, "expires": expiry_date, "days_left": days_left}

# Monitor all services
services = [
    ("api.example.com", 443),
    ("www.example.com", 443),
    ("mail.example.com", 993),
]
for host, port in services:
    check_cert_expiration(host, port)
```

### Pattern: Wildcard & Internal CA Management

**WHY:** Wildcard certs simplify management for subdomains. Internal CAs protect inter-service communication.

```bash
# Generate internal CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/C=US/ST=CA/L=SF/O=Company/CN=Internal-CA"

# Generate service certificate
openssl genrsa -out service.key 2048
openssl req -new -key service.key -out service.csr \
  -subj "/C=US/ST=CA/L=SF/O=Company/CN=*.internal.company.com"

# Sign with internal CA (3 years)
openssl x509 -req -in service.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out service.crt -days 1095 \
  -extensions v3_req -extfile <(printf "subjectAltName=DNS:*.internal.company.com")

# Deploy to K8s secret
kubectl create secret tls internal-tls --cert=service.crt --key=service.key
```

## Section 5: CIS Benchmark Automation

### Pattern: Automated Docker CIS Compliance

**WHY:** CIS benchmarks are security consensus. Automating checks prevents configuration drift.

```bash
# Install Kube-bench (Kubernetes CIS checks)
docker run --pid host \
  aquasec/kube-bench:latest \
  --targets node,policies \
  --json > cis-results.json

# Parse results
cat cis-results.json | jq '.[] | select(.status=="FAIL")'
```

**Dockerfile CIS checks:**

```python
# Automated CIS Docker Benchmark verification
checks = {
    "no_root": "docker inspect --format='{{.Config.User}}' image | grep -q nonroot",
    "read_only_fs": "docker inspect --format='{{.HostConfig.ReadonlyRootfs}}' image | grep -q true",
    "no_privileged": "docker inspect --format='{{.HostConfig.Privileged}}' image | grep -q false",
    "no_setuid": "docker run --rm image find / -perm /4000 | wc -l | grep -q ^0$",
}

for check, cmd in checks.items():
    result = os.system(cmd)
    status = "PASS" if result == 0 else "FAIL"
    print(f"{check}: {status}")
```

### Pattern: Linux Host Hardening Checks

**WHY:** OS configuration is foundational. Automated scans ensure hosts meet baseline.

```bash
#!/bin/bash
# CIS Linux Hardening Checks

echo "=== File Permissions ==="
find /etc/passwd* /etc/shadow* -type f -exec ls -l {} \; | grep -v "^-rw------- "

echo "=== SELinux Status ==="
getenforce  # Should return "Enforcing"

echo "=== SSH Hardening ==="
grep -E "^PermitRootLogin|^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config

echo "=== Firewall Status ==="
ufw status | head -3

echo "=== Kernel Parameters ==="
sysctl -a | grep "net.ipv4.conf.all.send_redirects"  # Should be 0
```

### Pattern: SSH Hardening & Brute-Force Protection

**WHY:** SSH is the primary remote access vector. Weak config invites automated brute-force attacks and credential compromise.

```bash
# Critical sshd_config settings
sudo tee -a /etc/ssh/sshd_config <<EOF
PasswordAuthentication no          # Disable password login; use keys only
PubkeyAuthentication yes           # Enable public key auth
PermitRootLogin no                 # Never allow root SSH login
AllowUsers user1 user2 deploy@*    # Whitelist specific users/patterns
MaxAuthTries 3                     # Fail after 3 attempts; blocks brute-force
MaxSessions 10                     # Limit concurrent sessions
ClientAliveInterval 300            # Disconnect idle sessions after 5min
Protocol 2                         # SSH v2 only (v1 is obsolete)
HostKey /etc/ssh/ssh_host_ed25519_key  # Use Ed25519 keys (prefer over RSA)
EOF

# Generate Ed25519 host key (replaces RSA)
ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""

# Enable fail2ban to block brute-force attempts
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
# fail2ban watches auth.log, bans IPs with >5 failures in 10min
```

**Why Ed25519:** Modern, smaller keys (256 bits vs 2048 RSA), faster, and equally secure. Resistant to cryptanalysis improvements that weaken RSA. Fail2ban + low MaxAuthTries = effective brute-force defense.

### Pattern: Firewall & Network Segmentation

**UFW/nftables Basics:** Use UFW (Uncomplicated Firewall) on Linux servers for stateful packet filtering. Default policy: `ufw default deny incoming; ufw default allow outgoing`. Whitelist only required ports: `ufw allow 22/tcp` (SSH), `ufw allow 80/tcp; ufw allow 443/tcp` (web). nftables is the modern replacement for iptables; define rules in `/etc/nftables.conf` for load-balanced deployments.

**VLAN Segmentation & DMZ:** Separate network zones: DMZ (web servers, exposed), internal (app servers), backend (databases, secrets). Use VLANs to enforce isolation: traffic between zones denied by default, allowed only via firewall rules. DMZ hosts can reach internal only for specific services; internal cannot initiate to DMZ.

**Default-Deny Between Zones:** Implement "zero trust" network model. Assume all traffic is malicious. Explicit allow-rules only. Example: App servers (internal zone) can reach DB (backend zone) on port 5432 only; all other traffic dropped. Monitor denied traffic for anomalies.

## Section 6: Incident Forensics & Response

### Pattern: Log Timeline Reconstruction

**WHY:** During breach, forensics must answer: who, what, when, where, how? Centralized logs with timestamps enable reconstruction.

```python
import json
from datetime import datetime, timedelta

# Aggregate logs from multiple sources
logs = {
    "ssh": parse_ssh_logs("/var/log/auth.log"),
    "app": parse_app_logs("/var/log/app.log"),
    "network": parse_firewall_logs("/var/log/ufw.log"),
}

# Create timeline (last 24 hours)
timeline = []
cutoff = datetime.now() - timedelta(hours=24)

for source, entries in logs.items():
    for entry in entries:
        if entry['timestamp'] > cutoff:
            timeline.append({
                'timestamp': entry['timestamp'],
                'source': source,
                'event': entry['event'],
                'user': entry.get('user', 'unknown'),
                'ip': entry.get('ip', '?'),
            })

# Sort by time
timeline = sorted(timeline, key=lambda x: x['timestamp'])

# Print timeline
for event in timeline:
    print(f"{event['timestamp']} | {event['source']:10} | {event['user']:15} | {event['event']}")
```

### Pattern: IOC Extraction (Indicators of Compromise)

**WHY:** Once attack confirmed, extract indicators (IPs, domains, hashes) to block everywhere.

```python
import re
import hashlib

ioc_patterns = {
    'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'domain': r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'hash_sha256': r'\b[a-f0-9]{64}\b',
    'hash_md5': r'\b[a-f0-9]{32}\b',
}

def extract_iocs(log_content):
    """Extract all IOCs from logs"""
    iocs = {ioc_type: set() for ioc_type in ioc_patterns}
    
    for ioc_type, pattern in ioc_patterns.items():
        matches = re.findall(pattern, log_content)
        iocs[ioc_type].update(matches)
    
    return iocs

# Extract from breach logs
with open('breach_logs.txt') as f:
    logs = f.read()

iocs = extract_iocs(logs)

# Export to MISP/threat intelligence platform
for ioc_type, values in iocs.items():
    for value in values:
        print(f"{ioc_type},{value},malicious,breach_2024_03")
```

### Pattern: Containment Playbooks

**WHY:** Automated containment stops spread. Manual response is too slow.

```yaml
# Containment playbook (Ansible)
---
- name: Containment Response
  hosts: compromised_hosts
  tasks:
    - name: Isolate host from network
      iptables:
        chain: OUTPUT
        policy: DROP
        jump: ACCEPT
        destination: "{{ trusted_networks }}"
      become: yes
    
    - name: Kill suspicious processes
      shell: |
        pkill -f "{{ suspicious_pattern }}"
      become: yes
    
    - name: Block outbound C2 domains
      lineinfile:
        path: /etc/hosts
        line: "127.0.0.1 {{ item }}"
      loop: "{{ c2_domains }}"
      become: yes
    
    - name: Enable full logging
      lineinfile:
        path: /etc/audit/rules.d/audit.rules
        line: "-a always,exit -F arch=b64 -S execve -F uid!=0 -F auid!=4294967295 -k exec"
      become: yes
      notify: restart auditd
    
    - name: Snapshot disk for forensics
      shell: |
        dd if=/dev/sda of=/backup/disk_image_$(date +%s).dd bs=4M
      become: yes
```

## Section 7: Supply Chain Security

### Pattern: SBOM Generation (Syft)

**WHY:** Know every component in your image/binary. Enables fast CVE impact assessment.

```bash
# Install syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh

# Generate SBOM in multiple formats
syft packages docker://myapp:latest -o json > sbom.json
syft packages docker://myapp:latest -o cyclonedx > sbom.xml
syft packages /path/to/binary -o table > sbom.txt

# Query SBOM (find all Python packages)
cat sbom.json | jq '.artifacts[] | select(.type=="python") | .name'

# Check if vulnerable package is in SBOM
if jq -e '.artifacts[] | select(.name=="log4j")' sbom.json; then
  echo "ALERT: Log4j found in image!"
fi
```

### Pattern: Sigstore Signing & Verification

**WHY:** Prove your artifacts haven't been tampered with. Sigstore provides keyless signing.

```bash
# Sign image with sigstore (no key management needed)
cosign sign --yes gcr.io/myproject/myapp:v1.0

# Verify signature before deployment
cosign verify gcr.io/myproject/myapp:v1.0

# Sign SBOM
cosign attach sbom sbom.json gcr.io/myproject/myapp:v1.0

# Verify in Kubernetes (admission controller)
kubectl apply -f - <<EOF
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-image-signature
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    labels: ["cosign-verified"]
EOF
```

### Pattern: Provenance Verification (SLSA Framework)

**WHY:** SLSA levels define build trustworthiness. Level 3+ requires verifiable provenance.

```json
// Provenance attestation (SLSA v1.0)
{
  "version": 1,
  "materials": [
    {
      "uri": "git+https://github.com/myorg/myapp@abc123",
      "digest": { "sha256": "abc123..." }
    }
  ],
  "byproducts": {
    "completeness": {
      "environment": true,
      "materials": true,
      "parameters": true
    },
    "reproducible": true
  },
  "invocation": {
    "configSource": {
      "uri": "github.com/myorg/myapp//.github/workflows/build.yml@abc123",
      "entrypoint": "build"
    },
    "parameters": {
      "GOFLAGS": "-trimpath",
      "SOURCE_DATE_EPOCH": "1234567890"
    },
    "environment": {
      "os": "ubuntu",
      "arch": "amd64"
    }
  },
  "builder": {
    "id": "https://github.com/actions/runner/blob/main/README.md"
  }
}
```

**Verify provenance in deployment:**

```bash
# Generate provenance during build
slsa-provenance-action@v1

# Verify before deploying
slsa-verifier verify-image \
  --image-path gcr.io/myproject/myapp:v1.0 \
  --provenance provenance.json \
  --source-uri github.com/myorg/myapp \
  --builder-id https://github.com/slsa-framework/slsa-github-generator
```

---

## Quick Reference

| Function | Tool | Why |
|----------|------|-----|
| Secrets rotation | Vault/Bitwarden | Instant revocation on compromise |
| CVE detection | npm audit / safety / nancy | Catches exploitable deps pre-deploy |
| Container hardening | Distroless / seccomp | Eliminates 90% of attack surface |
| Cert expiration | certbot + monitoring | Prevents outages from expired certs |
| Compliance checks | kube-bench / CIS | Enforce security consensus |
| Forensics | Log aggregation + IOC extraction | Reconstruct attacks for RCA |
| Supply chain | SBOM + sigstore + SLSA | Prove provenance, catch tampering |

**Deploy this framework to your infrastructure and run audits weekly. Security is operational, not episodic.**
