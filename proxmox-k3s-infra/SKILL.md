---
name: proxmox-k3s-infra
description: "Use this skill whenever the user wants to set up, manage, or troubleshoot Proxmox VE, K3s (lightweight Kubernetes), or homelab virtualization infrastructure. Triggers include: any mention of 'Proxmox', 'PVE', 'virtual machine', 'VM', 'LXC', 'container', 'K3s', 'Kubernetes', 'kubectl', 'Helm', 'ArgoCD', 'FluxCD', 'GitOps', 'GPU passthrough', 'IOMMU', 'PCIe passthrough', 'cluster', 'node', 'hypervisor', 'virtualization', 'KVM', 'QEMU', 'cloud-init', 'terraform proxmox', 'Ansible proxmox', or requests to create VMs, manage LXC containers, set up Kubernetes clusters, configure GPU passthrough, plan homelab hardware, or implement GitOps workflows. Also use when the user asks about homelab network design (VLANs, bridges, SDN), storage backends (ZFS, Ceph, NFS), high availability, backup strategies (PBS), or migrating between hypervisors. If someone says 'I want to run VMs' or 'set up a cluster at home', use this skill."
---

## Overview

Build and manage homelab infrastructure using Proxmox VE as the hypervisor layer and K3s for container orchestration. Patterns range from single-node setups to multi-node clusters with GPU passthrough, distributed storage, and GitOps-driven application deployment.

## Proxmox VE Fundamentals

Start with post-install essentials. Proxmox ships with the enterprise repo enabled; disable it and enable the no-subscription community repo to get updates without a license.

```bash
# Edit /etc/apt/sources.list.d/pve-enterprise.list and comment it out
# Edit /etc/apt/sources.list and add:
deb http://download.proxmox.com/debian/pve bullseye pve-no-subscription
apt update && apt upgrade
```

Access the web UI at `https://<PROXMOX_IP>:8006` with root credentials. Configure storage: `local` for ISOs and templates, `local-zfs` for VM disks (if using ZFS). Add NFS or CIFS for shared storage across nodes. Network bridges: `vmbr0` is your primary bridge; create additional bridges (vmbr1, vmbr2) for VLAN isolation. Manage users and API tokens in Datacenter → Permissions; use API tokens for automation instead of passwords.

## VM Management

Create VMs from the UI or CLI (`qm create <VMID>`). For rapid scaling, build cloud-init templates: download a cloud image (Ubuntu 22.04 generic or similar), create a VM, attach the image as a disk, add a cloud-init drive, configure user/SSH key via cloud-init settings, convert to template, then clone it. This pattern eliminates manual OS configuration.

Allocate CPU type carefully: use `host` for compute VMs (passes through CPU flags), `x86-64-v2-AES` for compatibility across generations. Enable memory ballooning (allows Proxmox to reclaim unused RAM from VMs) to pack more workloads. Resize disks with `qm disk resize <VMID> scsi0 +10G`. Manage VM lifecycle via CLI: `qm start`, `qm stop`, `qm suspend`, `qm migrate`, `qm snapshot`. If running multi-node, set autostart order and enable HA (High Availability) to move VMs if a node fails.

## LXC Containers

Use LXC for lightweight services (DNS, monitoring, file serving) where you don't need a full OS kernel. VMs are better for anything requiring Docker, GPU access, or isolation guarantees.

Always prefer unprivileged containers for security; only use privileged if you need Docker inside LXC (requires nesting + keyctl features, adds security risk). Proxmox provides templates via UI or command line. Bind mounts let you share directories from the Proxmox host into the container—useful for shared storage or config files. Monitor resource limits: CPU cores, memory, swap.

## GPU Passthrough

Enable IOMMU in BIOS (VT-d for Intel, AMD-Vi for AMD). Update kernel cmdline:

```bash
# GRUB systems (Intel):
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"
update-grub

# systemd-boot:
echo "quiet intel_iommu=on iommu=pt" > /etc/kernel/cmdline
proxmox-boot-tool refresh
```

List IOMMU groups: `find /sys/kernel/iommu_groups/ -type l`. Bind your GPU to VFIO (virtual function I/O) driver by adding its PCI IDs to `/etc/modprobe.d/vfio.conf`:

```
options vfio-pci ids=10de:2b81,10de:228b
```

Blacklist the host driver so Proxmox doesn't claim it:

```
blacklist nouveau  # NVIDIA open-source
blacklist nvidia   # NVIDIA proprietary
echo "blacklist nouveau" >> /etc/modprobe.d/blacklist.conf
update-initramfs -u
```

After reboot, verify VFIO binding: `lspci -nnk | grep -A 2 <GPU_PCI_ID>` should show `Kernel driver in use: vfio-pci`. In the VM settings, add a PCI device, select your GPU, enable "All Functions" and "Primary GPU" if it's the VM's only display. Install NVIDIA drivers inside the VM using the .run installer or apt.

Why this matters: GPU passthrough gives near-native performance to the VM, essential for AI workloads, gaming, or CUDA computing. Multi-GPU setups work if each GPU has an isolated IOMMU group; consumer GPUs sometimes share groups (fix requires ACS override kernel patch).

## K3s Deployment

K3s is Kubernetes in ~512MB RAM: single binary, built-in containerd, Traefik ingress, CoreDNS, and Flannel networking. Deploy a control plane VM (2+ CPU, 4GB+ RAM) and worker node VMs (2+ CPU, 2GB+ RAM).

On control plane:

```bash
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
# Retrieve token for workers:
cat /var/lib/rancher/k3s/server/node-token
```

On each worker:

```bash
curl -sfL https://get.k3s.io | K3S_URL=https://<CONTROL_PLANE_IP>:6443 K3S_TOKEN=<NODE_TOKEN> sh -
```

Verify: `kubectl get nodes`. Copy `/etc/rancher/k3s/k3s.yaml` from control plane to your workstation, update the server address to the control plane IP, and set `KUBECONFIG` environment variable to use it remotely.

Disable built-in services if replacing them:

```bash
curl -sfL https://get.k3s.io | sh -s - --disable traefik --disable servicelb
```

Then install nginx-ingress or MetalLB separately via Helm.

## Helm & Application Deployment

Install Helm: `curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash`

Standard pattern:

```bash
helm repo add <NAME> <CHART_REPO_URL>
helm repo update
helm install <RELEASE> <NAME>/<CHART> -n <NAMESPACE> --create-namespace -f values-homelab.yaml
```

Keep per-environment values in git (values-homelab.yaml, values-prod.yaml). Useful charts: `cert-manager`, `ingress-nginx`, `MetalLB`, `Longhorn` (distributed storage), `prometheus-community` (monitoring).

## GitOps with FluxCD or ArgoCD

**FluxCD** is lightweight and git-native. Bootstrap a cluster:

```bash
flux bootstrap github --owner=<USERNAME> --repository=<REPO> --path=clusters/homelab --personal
```

Structure your git repo: `clusters/homelab/` contains Kustomization manifests pointing to `apps/` directories. Commit changes, flux reconciles every few minutes.

**ArgoCD** offers a richer UI and app-of-apps pattern:

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl port-forward -n argocd svc/argocd-server 8080:443
# Login at localhost:8080, default user: admin, password in secret
```

Both patterns: git is source of truth, controller reconciles cluster to match manifests, drift is automatically corrected.

## Network Design

Use VLANs to separate management (Proxmox UI), VM traffic, storage, and IoT. Create a trunk port on your switch, configure VLAN-aware bridges in Proxmox:

```
auto vmbr0
iface vmbr0 inet static
  bridge_ports <PHYSICAL_NIC>
  bridge_vlan_aware yes
  # VLAN 100 for management
  # Assign VLAN tag to each VM's vNIC
```

Or use Proxmox SDN (software-defined networking) for complex topologies. K3s uses Flannel by default for pod networking. Deploy MetalLB for bare-metal load balancing (assigns real IPs to K3s LoadBalancer services). Use your ingress controller (Traefik in K3s or nginx-ingress) for HTTP routing. For internal DNS: CoreDNS (built into K3s) or Pi-hole/AdGuard on a separate VM.

## Storage Backends

- **Local ZFS**: Best single-node choice. Built into Proxmox, snapshots, compression, deduplication. Configure ZVOL for VM disks.
- **Ceph**: Distributed storage for 3+ node clusters. Overkill for homelabs unless you need redundancy.
- **NFS**: Simple shared storage from a NAS. Good for ISOs, backups, and non-critical shared volumes.
- **Longhorn**: Kubernetes-native distributed storage running on K3s worker nodes. Good for PersistentVolumes.

Single node = ZFS. Multi-node shared = NFS or Ceph. K3s persistent volumes = Longhorn or NFS.

## Backup & Recovery

Use **Proxmox Backup Server (PBS)** for VM backups. Set scheduled backup jobs via UI (Datacenter → Backup). PBS deduplicates and encrypts backups. Choose snapshot mode for running VMs (fast, slight inconsistency risk) or stop mode for consistency.

For K3s, snapshot etcd (built into K3s) or use **Velero** for application-level backup. Test restore procedures regularly—untested backups aren't backups.

## Automation

**Terraform**: Use `telmate/proxmox` provider for declarative VM/LXC infrastructure.

```bash
provider "proxmox" {
  pm_api_url      = "https://<PROXMOX_IP>:8006/api2/json"
  pm_api_token_id = "terraform-user@pam!terraform"
  pm_api_token_secret = "<TOKEN>"
}
```

**Ansible**: Use `community.general.proxmox` modules to configure VMs after creation.

**API**: Proxmox REST API at `https://<PROXMOX_IP>:8006/api2/json/`. Great for custom automation and integration.

## Troubleshooting

- **VM won't start with GPU**: Check IOMMU groups are isolated, verify VFIO binding (`lspci -nnk`), review dmesg for IOMMU errors.
- **K3s node won't join**: Verify token matches, check firewall (port 6443 TCP, 8472 UDP Flannel, 10250 kubelet), ensure unique hostnames.
- **Storage slow**: Check ZFS pool health (`zpool status`), verify ARC (adaptive replacement cache) is sized appropriately, review IO scheduler.
- **Networking issues**: Use `brctl show` to verify bridges, check VLAN tags on vNICs, verify firewall rules on both Proxmox and guest OS.
- **Backup failing**: Verify storage space, check PBS connectivity, review backup task logs in Proxmox UI.

---

**Quick Start Checklist:**
1. Post-install: disable enterprise repo, enable no-subscription repo, update
2. Create cloud-init template VM for rapid scaling
3. Deploy K3s control plane on one VM, workers on others
4. Install Helm, add chart repos, deploy core services (MetalLB, ingress, storage)
5. Initialize git repo with FluxCD or ArgoCD for GitOps
6. Configure backups with PBS or K3s etcd snapshots
7. Test failover and restore procedures
