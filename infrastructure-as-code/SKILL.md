---
name: infrastructure-as-code
description: "Use this skill whenever the user wants to define, provision, manage, or automate infrastructure declaratively. Triggers include: any mention of 'Infrastructure as Code', 'IaC', 'Terraform', 'OpenTofu', 'Pulumi', 'Ansible', 'CloudFormation', 'CDK', 'Bicep', 'cloud provisioning', 'infrastructure automation', 'state management', 'terraform plan', 'terraform apply', 'playbook', 'inventory', 'Ansible role', 'Ansible Galaxy', 'provider', 'module', 'resource', 'data source', 'remote state', 'state locking', 'drift detection', 'configuration management', 'idempotent', 'declarative infrastructure', 'immutable infrastructure', or requests to automate server setup, provision cloud resources, manage infrastructure at scale, or codify existing manual infrastructure. Also use when the user asks about managing cloud resources (AWS, GCP, Azure, Hetzner, DigitalOcean) programmatically, setting up VMs/networks/storage via code, or wants to convert manual infrastructure work into repeatable automation. If someone says 'I want to automate my infrastructure' or 'define my servers in code', use this skill."
---

# Infrastructure as Code

Define infrastructure declaratively, version-control it, and apply changes reproducibly. Covers Terraform/OpenTofu for provisioning, Ansible for configuration management, and patterns that apply across all IaC tools.

## Choosing the Right Tool

### Provisioning vs Configuration Management

**Provisioning** (Terraform, Pulumi, CloudFormation) creates or destroys infrastructure resources — VMs, networks, databases, DNS records. **Configuration management** (Ansible, Chef, Puppet) configures existing systems — installs packages, manages services, deploys files. Most real setups need both: Terraform creates the VM, Ansible configures what runs on it.

**Tool selection:**
- **Terraform/OpenTofu**: declarative HCL, massive provider ecosystem, state-based tracking, cloud-agnostic. Best general choice.
- **Pulumi**: use actual programming languages (Python, TypeScript, Go) instead of HCL. Better for teams who want loops, conditionals, testing.
- **Ansible**: agentless (SSH-based), procedural playbooks, idempotent modules. Best for configuration management and ad-hoc tasks.
- **CloudFormation/CDK**: AWS-only. Use if exclusively AWS and want native integration.
- **Bicep**: Azure-only. Same reasoning as CloudFormation.
- **OpenTofu**: open-source Terraform fork. Functionally equivalent for nearly all users.

## Terraform/OpenTofu Fundamentals

### Core Workflow
```bash
terraform init      # Download providers, initialize backend
terraform plan      # Preview changes (ALWAYS review before apply)
terraform apply     # Apply changes
terraform destroy   # Tear down everything
```

Always review plans before applying. Plans are your safety net — they show exactly what will change.

### Project Structure
```
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   └── prod/
├── modules/
│   ├── networking/
│   └── compute/
└── README.md
```

Separate state per environment. Use the same modules and code; change variables per environment.

### State Management: The Critical Part

**State** is Terraform's record of what it manages — your source of truth. Never ignore state.

- **Local state** (`terraform.tfstate` on disk): fine for learning, dangerous for teams.
- **Remote state** (S3+DynamoDB, GCS, Azure Blob, Terraform Cloud): required for production. Everyone sees the same state.
- **State locking**: prevents concurrent modifications. DynamoDB for S3, built-in for others. Always enabled in production.
- **Never edit state manually** — use `terraform state mv`, `terraform state rm`, `terraform import`.
- **Never commit state to git** — it contains secrets. Add `*.tfstate`, `*.tfstate.backup`, `.terraform/` to `.gitignore`.

### Writing Good Terraform

Pin all versions:
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

module "networking" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"
}
```

Use variables with types, descriptions, and validation:
```hcl
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Must be a t3 instance."
  }
}
```

Tag everything:
```hcl
locals {
  common_tags = {
    Name        = "my-resource"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "web" {
  tags = local.common_tags
}
```

Use `count` or `for_each` to avoid repetition:
```hcl
resource "aws_instance" "web" {
  for_each      = toset(var.web_server_names)
  ami           = var.ami_id
  instance_type = var.instance_type
  tags = { Name = each.value }
}
```

### Modules

Extract repeated patterns into modules. One module = one concern.

```
modules/
└── web_tier/
    ├── main.tf          # Resources
    ├── variables.tf     # Inputs with validation
    ├── outputs.tf       # What consumers get back
    └── README.md        # Usage documentation
```

Module interface is clear: `variables.tf` defines inputs, `outputs.tf` defines outputs. Always pin module versions in consuming code.

## Ansible Fundamentals

### Inventory

Define your hosts:
```ini
[webservers]
web1 ansible_host=<IP_ADDRESS_1>
web2 ansible_host=<IP_ADDRESS_2>

[dbservers]
db1 ansible_host=<IP_ADDRESS_3>

[all:vars]
ansible_user=deploy
ansible_python_interpreter=/usr/bin/python3
```

### Playbook Example

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes

  tasks:
    - name: Install packages
      apt:
        name: "{{ item }}"
        state: present
        update_cache: yes
      loop:
        - nginx
        - python3-pip
      notify: Restart nginx

    - name: Deploy config
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: Restart nginx

  handlers:
    - name: Restart nginx
      systemd:
        name: nginx
        state: restarted
```

**Idempotency** matters: running the same playbook twice produces the same result. Use handlers so tasks only run when config actually changes.

### Roles

Reusable packages for configuration:
```
roles/
└── web_server/
    ├── tasks/main.yml
    ├── handlers/main.yml
    ├── templates/
    ├── files/
    ├── vars/main.yml
    └── defaults/main.yml
```

Use Ansible Galaxy for community roles: `ansible-galaxy install geerlingguy.docker`. Write your own when community roles don't fit.

## Combining Terraform + Ansible

**The handoff pattern:**
1. Terraform provisions infrastructure (VMs, networks, storage)
2. Terraform outputs connection details
3. Ansible receives inventory (static file or dynamic) and configures hosts

Generate Ansible inventory from Terraform output:
```bash
terraform output -json | python3 generate_inventory.py > inventory/hosts.json
```

**Alternative: Cloud-Init.** Pass initial configuration at VM creation time via `user_data`. Good for immutable infrastructure (configure once, never update). Less flexible than Ansible for ongoing management.

## IaC Best Practices

### Version Control Everything

All infrastructure code lives in git. Changes go through pull requests with review. Tag releases. Protect main branch.

### Environment Parity

Keep dev, staging, and prod as similar as possible. Use same modules and code; differ only in variables. Promote changes left-to-right: dev → staging → prod. Never skip staging.

### Secrets Management

Never hardcode secrets. Terraform: use `sensitive = true` and reference from Vault/AWS Secrets Manager/SSM. Ansible: use `ansible-vault encrypt secrets.yml`. CI/CD injects secrets via environment variables.

### Drift Detection

Manual changes outside of IaC break reproducibility. Run `terraform plan` regularly (scheduled job or CI/CD) to detect drift. Backport manual fixes into code immediately.

### Testing

- `terraform validate`: syntax checking
- `tflint`: Terraform linting
- `checkov`: security scanning for IaC misconfigurations
- `ansible-lint`: playbook linting
- `molecule`: Ansible role testing framework

## Homelab IaC Patterns

- **Proxmox**: telmate/proxmox provider manages VMs and LXC containers declaratively
- **Hetzner Cloud**: hcloud provider for affordable cloud VMs
- **Local Ansible**: playbooks for NAS/server package installation, service management, users
- **GitOps bridge**: Terraform provisions K3s nodes, FluxCD/ArgoCD manages deployed applications

## Troubleshooting

**State lock stuck**: check for running terraform process; force-unlock only as last resort (`terraform force-unlock <ID>`).

**Provider version conflicts**: pin versions strictly. Use `terraform providers lock` for reproducibility across machines.

**Resource already exists**: bring it under management with `terraform import aws_instance.web <INSTANCE_ID>`.

**Ansible connection failures**: verify SSH access, check Python path, test with `ansible -m ping all`.

**Drift detected**: review plan carefully. Was the manual change intentional? Import it or revert it, but don't leave drift.

**Module changes breaking consumers**: use semantic versioning. Never break module interfaces in minor versions.
