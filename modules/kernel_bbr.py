"""
OVERDRIVE - Module 2: Kernel BBRv3 / BBR Congestion Control & High-BDP Network Buffers
Dynamically probes and deploys Google BBR/BBRv3, CAKE/FQ pacing, and dynamically sized TCP memory buffers.
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class KernelBBROptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Kernel BBRv3 / BBR & High-BDP TCP Buffers",
            description="Dynamically probes & enables Google BBR/BBRv3, CAKE/FQ pacing, 64MB socket buffers, and uncapped queues.",
            category="Linux Kernel & TCP Stack"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("Kernel Optimization", "Auto-probing BBRv3/BBR & CAKE/FQ qdisc, dynamic memory buffers & tuning sysctl...")
        
        script = r"""
set -e

# 1. Pre-flight safety backup of existing sysctl configs
BACKUP_DIR="/etc/sysctl.d/backup_overdrive_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -f /etc/sysctl.d/*.conf "$BACKUP_DIR/" 2>/dev/null || true
cp -f /etc/sysctl.conf "$BACKUP_DIR/" 2>/dev/null || true

# 2. Probe and load kernel modules
modprobe tcp_bbr 2>/dev/null || true
modprobe tcp_bbr2 2>/dev/null || true
modprobe sch_cake 2>/dev/null || true
modprobe sch_fq 2>/dev/null || true
modprobe sch_fq_codel 2>/dev/null || true
modprobe tcp_fastopen 2>/dev/null || true

# Determine best available congestion control
AVAIL_CONG=$(sysctl -n net.ipv4.tcp_available_congestion_control 2>/dev/null || echo "bbr cubic")
if echo "$AVAIL_CONG" | grep -q "bbrv3"; then
    BEST_CONG="bbrv3"
elif echo "$AVAIL_CONG" | grep -q "bbr2"; then
    BEST_CONG="bbr2"
elif echo "$AVAIL_CONG" | grep -q "bbr"; then
    BEST_CONG="bbr"
else
    BEST_CONG="cubic"
fi

# Determine best available queue discipline (CAKE / FQ)
if lsmod | grep -q "sch_cake" 2>/dev/null || modinfo sch_cake >/dev/null 2>&1; then
    BEST_QDISC="cake"
else
    BEST_QDISC="fq"
fi

# 3. Dynamic RAM detection for optimal buffer sizing
MEM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "2000000")
if [ "$MEM_KB" -ge 3500000 ]; then
    BUF_MAX=67108864      # 64MB for 4GB+ systems
    BUF_DEF=33554432
elif [ "$MEM_KB" -ge 1800000 ]; then
    BUF_MAX=67108864      # 64MB for 2GB systems
    BUF_DEF=16777216
else
    BUF_MAX=33554432      # 32MB for 512MB-1GB systems
    BUF_DEF=8388608
fi

# 4. Clean conflicting legacy files
rm -f /etc/sysctl.d/99-xray-sg.conf /etc/sysctl.d/99-vpn-reality-optimization.conf /etc/sysctl.d/99-bbr-x-ui.conf /etc/sysctl.d/99-custom-optimization.conf

# 5. Inject peak performance sysctl configuration
cat << EOF > /etc/sysctl.d/99-vps-optimization.conf
# TCP Congestion Control and Queuing Discipline
net.core.default_qdisc = $BEST_QDISC
net.ipv4.tcp_congestion_control = $BEST_CONG

# Dynamic IP Forwarding for VPN/Proxy Routing
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1

# Path MTU Probing (Prevent GTP-U 4G/5G & PPPoE blackholes)
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_base_mss = 1024

# Uncapped TCP Socket Send Queue for High BDP
net.ipv4.tcp_notsent_lowat = 4294967295
net.ipv4.tcp_autocorking = 0
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_no_metrics_save = 1
net.ipv4.tcp_adv_win_scale = 1
net.ipv4.tcp_fastopen = 3

# Dynamically Calculated High-BDP Memory Buffers
net.core.rmem_max = $BUF_MAX
net.core.wmem_max = $BUF_MAX
net.core.rmem_default = $BUF_DEF
net.core.wmem_default = $BUF_DEF
net.core.optmem_max = 2097152
net.ipv4.tcp_rmem = 4096 87380 $BUF_MAX
net.ipv4.tcp_wmem = 4096 65536 $BUF_MAX

# Socket Backlog and Connection Handling
net.core.netdev_max_backlog = 65536
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_tw_reuse = 1

# SoftIRQ Packet Budget & UDP Reserves
net.core.netdev_budget = 600
net.core.netdev_budget_usecs = 4000
net.ipv4.udp_rmem_min = 16384
net.ipv4.udp_wmem_min = 16384

# File Descriptors Limit & Virtual Memory
fs.file-max = 2097152
fs.inotify.max_user_instances = 8192
vm.swappiness = 10
vm.vfs_cache_pressure = 50
EOF

sed -i '/vm.swappiness/d' /etc/sysctl.conf 2>/dev/null || true
sysctl -p /etc/sysctl.d/99-vps-optimization.conf 2>/dev/null || sysctl --system 2>/dev/null || true
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "Kernel Congestion Control (BBR/BBRv3), FQ/CAKE pacing & dynamic TCP buffers active."
        return False, f"Notice: Applied sysctl configuration with warnings: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc net.core.rmem_max net.ipv4.tcp_notsent_lowat"
        code, out, err = ssh.execute_command(cmd)
        bbr_active = "bbr" in out
        qdisc_active = "fq" in out or "cake" in out
        return {
            "congestion_control": out.splitlines()[0] if out else "Unknown",
            "qdisc": out.splitlines()[1] if len(out.splitlines()) > 1 else "Unknown",
            "raw_output": out,
            "pass": bbr_active and qdisc_active
        }
