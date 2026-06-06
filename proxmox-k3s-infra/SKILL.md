---
name: proxmox-k3s-infra
description: "Use this when: set up a homelab Kubernetes cluster, create a VM from a template, my K3s node won't join, set up GPU passthrough, automate VM provisioning with cloud-init, my IOMMU groups are wrong, back up VMs automatically, install K3s on a new node, deploy persistent workloads in Kubernetes, manage LXC containers, rebuild infrastructure from code, set up GitOps for my cluster, Proxmox, K3s, FluxCD, ArgoCD, Helm, Longhorn, PBS, Terraform proxmox, VLAN design, Ceph vs NFS, MetalLB, NVIDIA passthrough, ACS override"
---

# Proxmox & K3s Infrastructure

## Identity
You are a homelab virtualization and Kubernetes engineer. Deploy deterministic, reproducible infrastructure — every VM and cluster should be rebuildable from code. Never use the Proxmox enterprise repo without a subscription.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Hypervisor | Proxmox VE (no-subscription repo) | Free, ZFS-native, REST API |
| VM templates | cloud-init clones from Ubuntu 22.04 generic | Rapid spin-up, no manual OS setup |
| Storage (single node) | local-zfs for VM disks | Snapshots, compression, fast clones |
| Storage (multi-node) | NFS from TrueNAS or Ceph (3+ nodes) | Ceph overkill under 3 nodes |
| Kubernetes | K3s (single binary, ~512MB RAM) | Built-in Traefik, CoreDNS, Flannel |
| K3s storage | Longhorn for PVs, NFS for shared | Longhorn is K8s-native; NFS for legacy |
| Backups | PBS for VMs, K3s etcd snapshots | PBS deduplicates and encrypts |
| IaC | Terraform (telmate/proxmox provider) | Declarative VM lifecycle |

## Decision Framework

### Container vs VM
- If service is lightweight (DNS, monitoring, file serving) → LXC unprivileged container
- If service needs Docker inside it → VM (Docker in LXC needs nesting + keyctl, security risk)
- If service needs GPU or custom kernel → VM with PCIe passthrough
- Default → VM with cloud-init template clone

### GPU Passthrough
- If Intel GPU (QSV) → /dev/dri device passthrough in VM config or LXC
- If NVIDIA → enable IOMMU (VT-d/AMD-Vi), bind GPU to vfio-pci, blacklist nouveau/nvidia on host
- If IOMMU groups are not isolated (consumer GPU) → ACS override kernel patch required
- Default → verify with `lspci -nnk | grep vfio-pci` before starting VM

### K3s Cluster Sizing
- If single node → K3s server only, no agents; disable traefik if using external ingress
- If multi-node → 1 control plane VM (4GB RAM), N worker VMs (2GB+ RAM each)
- If HA control plane needed → 3 server nodes + embedded etcd
- Default → single control plane + 2-3 workers for most homelabs

### Storage Selection
- If single Proxmox node → local-zfs for VM disks
- If 3+ node cluster and shared storage needed → Ceph (built into Proxmox)
- If K3s PersistentVolumes → Longhorn (in-cluster) or NFS storage class
- Default → local-zfs on Proxmox, Longhorn on K3s

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Leave enterprise repo enabled (no license) | apt update fails with 401 errors | Disable enterprise repo, enable pve-no-subscription |
| Use privileged LXC for Docker workloads | Privilege escalation risk | Run Docker in a VM instead |
| Skip cloud-init template; install OS manually | Slow, error-prone, not reproducible | Build one cloud-init template, clone it |
| Run K3s workers without unique hostnames | Nodes fail to join cluster | Set unique hostname before K3s install |
| Use RAIDZ or degraded pools for VM storage | I/O errors corrupt VM disk images | Fix storage before creating VMs |
| Store kubeconfig with root server URL | Remote kubectl fails | Update server IP in k3s.yaml after copying |

## Quality Gates
- [ ] Enterprise repo disabled; system updated from no-subscription repo
- [ ] Cloud-init template exists; VMs are clones, not manual installs
- [ ] K3s: all nodes show Ready in `kubectl get nodes`
- [ ] GPU passthrough: `lspci -nnk` shows `vfio-pci` as kernel driver
- [ ] PBS backup job runs nightly; test restore completed
- [ ] GitOps repo bootstrapped; `flux get all` or ArgoCD shows apps Synced

## Reference
```bash
# Proxmox post-install
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/pve-enterprise.list
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
  >> /etc/apt/sources.list
apt update && apt upgrade -y

# K3s install
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
# Worker join:
curl -sfL https://get.k3s.io | K3S_URL=https://<CP_IP>:6443 K3S_TOKEN=<TOKEN> sh -
```

---

## Cloud-Init VM Template

```bash
# 1. Download cloud image
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# 2. Create VM
qm create 9000 --memory 2048 --net0 virtio,bridge=vmbr0 --name ubuntu-template

# 3. Import disk
qm importdisk 9000 jammy-server-cloudimg-amd64.img local-zfs

# 4. Configure
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-zfs:vm-9000-disk-0
qm set 9000 --ide2 local-zfs:cloudinit
qm set 9000 --boot c --bootdisk scsi0
qm set 9000 --serial0 socket --vga serial0
qm set 9000 --ipconfig0 ip=dhcp
qm set 9000 --sshkey ~/.ssh/id_ed25519.pub

# 5. Convert to template (no turning back)
qm template 9000

# 6. Clone when needed
qm clone 9000 101 --name my-vm --full
qm resize 101 scsi0 +20G
qm start 101
```

## GPU Passthrough (NVIDIA)

```bash
# 1. Enable IOMMU in GRUB
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"
update-grub

# 2. Bind GPU to VFIO
echo "options vfio-pci ids=<VENDOR>:<DEVICE>" > /etc/modprobe.d/vfio.conf
echo "blacklist nouveau" >> /etc/modprobe.d/blacklist.conf
update-initramfs -u && reboot

# 3. Verify
lspci -nnk | grep -A 2 <GPU_PCI_ID>
# Should show: Kernel driver in use: vfio-pci

# 4. Add PCI device in VM config (PCIe passthrough mode)
qm set <VMID> -hostpci0 <PCI_ID>,pcie=1,x-vga=1
```

## K3s + Helm Quickstart

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Core services
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metallb https://metallb.github.io/metallb
helm repo add longhorn https://charts.longhorn.io
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
helm install metallb metallb/metallb -n metallb-system --create-namespace
helm install longhorn longhorn/longhorn -n longhorn-system --create-namespace

# Disable built-in K3s traefik if using nginx
# Add to K3s install: --disable traefik
```

## GitOps with FluxCD

```bash
# Bootstrap (GitHub)
flux bootstrap github \
  --owner=<USERNAME> \
  --repository=homelab-gitops \
  --path=clusters/homelab \
  --personal

# Verify
flux get all
```

Structure: `clusters/homelab/` → Kustomization → `apps/<service>/` → HelmRelease / Deployment. Commit to git; Flux reconciles every 10 minutes (configurable).

## Network Design

```
VLANs:
  VLAN 10 — Management (Proxmox UI, SSH, iLO)
  VLAN 20 — VM traffic (homelab services)
  VLAN 30 — Storage (NFS/iSCSI to TrueNAS)
  VLAN 40 — IoT (isolated, no LAN access)
```

```
# Proxmox VLAN-aware bridge
auto vmbr0
iface vmbr0 inet static
  bridge_ports <NIC>
  bridge_vlan_aware yes
```

MetalLB provides LoadBalancer IPs for K3s services on bare metal. Assign an IP pool from your LAN range that is outside DHCP scope.

## Terraform Provider

```hcl
provider "proxmox" {
  pm_api_url          = "https://<PROXMOX_IP>:8006/api2/json"
  pm_api_token_id     = "terraform-user@pam!terraform"
  pm_api_token_secret = var.proxmox_token
}

resource "proxmox_vm_qemu" "k3s_worker" {
  count       = 3
  name        = "k3s-worker-${count.index}"
  clone       = "ubuntu-template"
  full_clone  = true
  memory      = 4096
  cores       = 2
  ipconfig0   = "ip=dhcp"
  sshkeys     = file("~/.ssh/id_ed25519.pub")
}
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| VM won't start with GPU | Check IOMMU groups; `lspci -nnk` for vfio-pci; review `dmesg | grep iommu` |
| K3s node won't join | Verify token, firewall port 6443/TCP + 8472/UDP, unique hostname |
| kubectl can't reach cluster | Update `server:` in k3s.yaml to control plane IP |
| Storage slow | `zpool status`; verify ARC size; check IO scheduler |
| PBS backup fails | Verify storage space; check PBS connectivity; review backup task logs |
| Enterprise repo 401 | Comment out `/etc/apt/sources.list.d/pve-enterprise.list` |
