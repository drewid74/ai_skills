---
name: infrastructure-as-code
description: >-
  Manage infrastructure declaratively with Terraform and Ansible. Provision
  cloud and homelab resources, enforce idempotent configuration, manage secrets
  with Vault/SOPS, and maintain state safely across environments.
triggers:
  - "write Terraform for"
  - "provision infrastructure"
  - "Ansible playbook for"
  - "manage secrets with Vault"
  - "IaC for homelab"
  - "infrastructure state management"
  - "configure servers with Ansible"
tags: [terraform, ansible, iac, vault, sops, idempotent, homelab]
author: merged
---

# Infrastructure as Code

## Identity

Write declarative infrastructure that can be applied repeatedly without manual intervention. Terraform for provisioning, Ansible for configuration. Never store secrets in plaintext. Every resource needs a destroy path.

## Stack Defaults

| Tool | Purpose | Notes |
|------|---------|-------|
| Terraform | Cloud/VM provisioning | HCL, state in S3 or local |
| Ansible | Config management | Playbooks, idempotent tasks |
| SOPS | Secret encryption | Age or GPG keys |
| HashiCorp Vault | Dynamic secrets | For production; Bitwarden for homelab |
| TFLint | Terraform linting | Rules for provider-specific issues |
| Checkov | IaC security scan | CIS benchmarks, misconfig detection |
| Terragrunt | DRY Terraform | Optional for multi-environment |

## Decision Framework

```
IF provisioning new infrastructure:
  → Terraform: cloud resources (VMs, networks, DNS, storage)
  → Ansible: software installation, config file management
  → Order: Terraform first (infra), Ansible second (config)

IF managing secrets:
  → Dev: SOPS-encrypted files in Git (age key)
  → Prod: HashiCorp Vault with dynamic credentials
  → Never: plaintext .tfvars, .env in Git, or inline in playbooks

IF updating existing resources:
  → terraform plan → review → apply (never skip plan)
  → For Ansible: --check --diff first; apply second

IF destroying resources:
  → terraform destroy with explicit target if partial
  → Protect state: S3 backend with versioning + DynamoDB lock
  → Remove from state first if manual changes made: terraform state rm

IF state gets out of sync:
  → terraform refresh (read actual state)
  → terraform import (import existing resource)
  → Never manually edit .tfstate
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| Plaintext secrets in `.tfvars` | SOPS-encrypted vars file |
| Local Terraform state | Remote backend (S3 + DynamoDB lock) |
| No `terraform plan` before apply | Always plan; always review diff |
| Ansible with `ignore_errors: true` | Fix the underlying error |
| `command:` module for everything | Use purpose-built Ansible modules |
| No tagging strategy on cloud resources | Tags: env, owner, project, created-by |
| `count` for multi-region resources | Use `for_each` with maps |

## Quality Gates

- [ ] All secrets encrypted (SOPS or Vault); no plaintext in Git
- [ ] Remote state backend configured with locking
- [ ] `terraform validate` and `tflint` pass in CI
- [ ] Checkov scan has no HIGH severity findings
- [ ] Destroy tested in staging before production
- [ ] Resource tags applied consistently

→ See `cicd-pipeline` for Terraform CI/CD (plan on PR, apply on merge)  
→ See `proxmox-k3s-infra` for homelab-specific Terraform + Ansible patterns  
→ See `security-engineer` for secrets scanning in IaC pipelines

---

## Terraform: Core Patterns

### Remote State Backend

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "production/network/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Variable + Secrets Pattern

```hcl
# variables.tf
variable "db_password" {
  type      = string
  sensitive = true           # Redacted from plan output
}

variable "environment" {
  type    = string
  default = "production"
}

# terraform.tfvars.enc (encrypted with SOPS; never plaintext)
# Decrypt on apply: sops -d terraform.tfvars.enc > terraform.tfvars
```

### Resource Tagging

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Project     = "homelab"
    Owner       = "<owner>"
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  tags          = merge(local.common_tags, { Name = "web-01" })
}
```

### Module Structure

```
modules/
  vpc/
    main.tf
    variables.tf
    outputs.tf
  ec2/
    main.tf
    variables.tf
    outputs.tf
environments/
  staging/
    main.tf         # calls modules
    terraform.tfvars
  production/
    main.tf
    terraform.tfvars
```

### Proxmox Provider Example

```hcl
terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.40"
    }
  }
}

provider "proxmox" {
  endpoint = "https://proxmox.local:8006"
  api_token = var.proxmox_api_token
  insecure  = true   # Use false if you have valid cert
}

resource "proxmox_virtual_environment_vm" "docker_node" {
  name      = "docker-node-01"
  node_name = "pve"
  vm_id     = 200

  clone {
    vm_id = 100   # Template VM
    full  = true
  }

  cpu { cores = 8 }
  memory { dedicated = 16384 }

  network_device {
    bridge = "vmbr0"
    vlan_id = 200
  }

  initialization {
    ip_config {
      ipv4 {
        address = "<VM_IP>/<CIDR>"
        gateway = "<GATEWAY_IP>"
      }
    }
    user_account {
      username = "ubuntu"
      keys     = [var.ssh_public_key]
    }
  }
}
```

---

## Ansible: Core Patterns

### Directory Structure

```
ansible/
  inventory/
    production.yml
    staging.yml
  group_vars/
    all.yml          # Common vars
    docker_nodes.yml
  roles/
    docker/
      tasks/main.yml
      handlers/main.yml
      defaults/main.yml
  playbooks/
    site.yml         # Full site playbook
    docker.yml       # Role-specific playbook
  ansible.cfg
```

### Idempotent Docker Install

```yaml
# roles/docker/tasks/main.yml
- name: Install Docker dependencies
  apt:
    name:
      - apt-transport-https
      - ca-certificates
      - curl
    state: present
    update_cache: true

- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: "deb https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
    state: present

- name: Install Docker CE
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-compose-plugin
    state: present

- name: Ensure Docker service is running
  service:
    name: docker
    state: started
    enabled: true

- name: Add user to docker group
  user:
    name: "{{ ansible_user }}"
    groups: docker
    append: true
```

### Vault-Encrypted Variables

```bash
# Encrypt secrets file
ansible-vault encrypt group_vars/all/secrets.yml

# Create encrypted string inline
ansible-vault encrypt_string 'SuperSecretPassword' --name 'db_password'

# Run playbook with vault password
ansible-playbook site.yml --vault-password-file ~/.vault_pass
```

### Deploy Compose Stack

```yaml
# playbooks/deploy_stack.yml
- hosts: docker_nodes
  become: true
  vars:
    stack_name: myapp
    deploy_dir: "/opt/stacks/{{ stack_name }}"

  tasks:
    - name: Create deploy directory
      file:
        path: "{{ deploy_dir }}"
        state: directory
        mode: '0750'

    - name: Copy compose file
      template:
        src: templates/docker-compose.j2
        dest: "{{ deploy_dir }}/docker-compose.yml"

    - name: Copy env file
      template:
        src: templates/env.j2
        dest: "{{ deploy_dir }}/.env"
        mode: '0600'

    - name: Pull and restart stack
      community.docker.docker_compose_v2:
        project_src: "{{ deploy_dir }}"
        pull: always
        state: present
      notify: health_check

  handlers:
    - name: health_check
      uri:
        url: "http://localhost:8080/health"
        status_code: 200
      retries: 5
      delay: 5
```

---

## SOPS Secret Management

```bash
# Generate age key
age-keygen -o ~/.config/sops/age/keys.txt

# .sops.yaml (in repo root)
creation_rules:
  - path_regex: .*secrets.*\.yaml$
    age: >-
      age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Encrypt a secrets file
sops --encrypt secrets.yaml > secrets.enc.yaml

# Edit encrypted file
sops secrets.enc.yaml

# Decrypt for use
sops --decrypt secrets.enc.yaml > /tmp/secrets.yaml
```

---

## CI/CD Integration

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    paths: ['terraform/**']

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3

      - name: Decrypt secrets
        run: |
          echo "$SOPS_AGE_KEY" > /tmp/age.key
          sops --decrypt terraform/terraform.tfvars.enc > terraform/terraform.tfvars
        env:
          SOPS_AGE_KEY: ${{ secrets.SOPS_AGE_KEY }}

      - name: Terraform Init
        run: terraform -chdir=terraform init

      - name: Terraform Plan
        run: terraform -chdir=terraform plan -out=tfplan
        env:
          TF_VAR_db_password: ${{ secrets.DB_PASSWORD }}

      - name: Checkov Security Scan
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          quiet: true
          soft_fail: false
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| State lock timeout | Previous apply failed mid-run | `terraform force-unlock <LOCK_ID>` |
| "Error acquiring state lock" | DynamoDB table missing | Create `terraform-state-lock` DynamoDB table |
| Ansible task not idempotent | Using `command:` module | Replace with specific module (apt, file, service, etc.) |
| `terraform plan` shows unexpected destroy | Manual change outside Terraform | `terraform import` to reconcile |
| SOPS decrypt fails in CI | Age key not in environment | Set `SOPS_AGE_KEY_FILE` or `SOPS_AGE_KEY` env var |
| Vault dynamic secrets expire mid-pipeline | Short TTL on role | Increase lease TTL or renew token during long pipeline |
