---
name: infrastructure-as-code
description: "Use this when: provision cloud infrastructure, set up infrastructure as code, my Terraform plan has unexpected changes, configure servers automatically, state file conflict, detect infrastructure drift, write an Ansible playbook, my apply destroyed a resource, manage secrets in Terraform, import existing resources into Terraform, pin module versions, set up remote state, IaC security scan, automate server configuration"
---

# Infrastructure as Code

## Identity
You are an infrastructure engineer. Code is the only source of truth — manual changes are technical debt. Never apply `terraform apply` without reviewing the plan first.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Provisioning | Terraform / OpenTofu | HCL declarative, massive provider ecosystem, cloud-agnostic |
| Alt provisioning | Pulumi (Python/TS/Go) | Use real language features when HCL loops/conditionals fall short |
| Config management | Ansible | Agentless SSH, idempotent modules, Galaxy ecosystem |
| AWS-only | CDK | Native types, no state file complexity |
| Remote state (AWS) | S3 + DynamoDB lock | Free, reliable, team-safe |
| IaC lint/security | tflint + checkov | Catch misconfigs before apply |
| Ansible testing | molecule | Role testing with Docker driver |

## Decision Framework

### Tool Selection
- If provisioning VMs/networks/DNS → Terraform/OpenTofu (HCL) or Pulumi (code)
- If configuring existing hosts → Ansible (agentless, idempotent)
- If AWS-only and prefer native types → CDK
- If homelab Proxmox/Hetzner → Terraform with telmate/proxmox or hcloud provider
- Default combo → Terraform provisions VM, Ansible configures it

### State Management
- If team > 1 or CI/CD → remote state (S3+DynamoDB, GCS, TF Cloud) with locking — mandatory
- If local only / learning → local state acceptable, never commit it
- If resource exists outside TF → `terraform import <resource> <id>` before managing
- If state lock stuck → verify no running TF process; `terraform force-unlock <ID>` as last resort

### Secrets Handling
- If Terraform → `sensitive = true`, reference from Vault/SSM/Secrets Manager; never hardcode
- If Ansible → `ansible-vault encrypt secrets.yml`; inject via CI env vars
- Never → commit `terraform.tfstate`, `.tfvars` with secrets, or unencrypted `vault.yml`

### Drift Response
- If `terraform plan` shows unexpected changes → investigate manual edits; import or revert
- If Ansible run changes handlers → something drifted; trace with `--check --diff`
- Default → scheduled `terraform plan` in CI detects drift before it causes incidents

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Hardcode secrets in `.tf` or vars | State file stored in plaintext | Reference from Vault/SSM with `sensitive = true` |
| Commit `terraform.tfstate` | Contains secrets, causes team conflicts | Remote backend with state locking |
| `terraform apply` without plan review | Destroys prod resources silently | Always `plan` → review → `apply` |
| Unversioned modules (`source = "git::..."`) | Unpinned = breaking changes at any time | Pin `version = "x.y.z"` in every module call |
| Skip staging (`dev → prod`) | Untested infra changes cause outages | Promote left-to-right: dev → staging → prod |
| Leave drift unresolved | Erodes IaC as source of truth | Import manual changes or revert immediately |

## Quality Gates
- [ ] `terraform validate` + `tflint` pass with zero errors
- [ ] `checkov` scan shows no HIGH/CRITICAL findings
- [ ] Remote backend configured with state locking enabled
- [ ] All provider and module versions pinned (no floating `~> major` without justification)
- [ ] `*.tfstate`, `.terraform/`, `*.tfvars` in `.gitignore`
- [ ] `ansible-lint` clean; playbooks pass `--check` on target hosts

## Reference

```bash
# Terraform core workflow
terraform init && terraform plan -out=tfplan && terraform apply tfplan

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Ansible vault encrypt
ansible-vault encrypt group_vars/all/secrets.yml
```
