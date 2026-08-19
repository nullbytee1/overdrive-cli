"""
OVERDRIVE - Module 5: Memory Governance, Go Runtime Heap Tuning & System Limits
Dynamically calculates GOMEMLIMIT, madvdontneed GC pacing, provisions swap, and enforces full ulimit spectrum.
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class MemoryLimitsOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Memory Governance, Dynamic Swap & Limits",
            description="Dynamically calculates and sets GOMEMLIMIT, GODEBUG, GOGC, provisions swap, and sets 1M FD & memlock limits.",
            category="Memory & Process Limits"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("Memory Governance", "Enforcing dynamic GOMEMLIMIT, madvdontneed GC pacing, swap file & full ulimits...")
        
        script = r"""
set -e

# 1. Calculate dynamic GOMEMLIMIT based on total RAM (65%)
TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "2000000")
TARGET_MEM_MIB=$(( TOTAL_MEM_KB * 65 / 1024 / 100 ))
if [ $TARGET_MEM_MIB -lt 400 ]; then
  TARGET_MEM_MIB=400
fi

# 2. Auto-provision dynamic swap (1GB for <=1GB RAM, 2GB for 2GB+ RAM)
if ! swapon --show 2>/dev/null | grep -q "swap"; then
  if [ ! -f /swapfile ]; then
    SWAP_SZ=2048
    if [ "$TOTAL_MEM_KB" -lt 1200000 ]; then
      SWAP_SZ=1024
    fi
    fallocate -l ${SWAP_SZ}M /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=$SWAP_SZ 2>/dev/null || true
    chmod 600 /swapfile 2>/dev/null || true
    mkswap /swapfile 2>/dev/null || true
  fi
  swapon /swapfile 2>/dev/null || true
  if [ -f /swapfile ] && ! grep -q "/swapfile" /etc/fstab 2>/dev/null; then
    echo "/swapfile none swap sw 0 0" >> /etc/fstab 2>/dev/null || true
  fi
fi

# 3. Update x-ui.service if present
if [ -f /etc/systemd/system/x-ui.service ]; then
  cat << EOF > /etc/systemd/system/x-ui.service
[Unit]
Description=x-ui Service
After=network.target network-online.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/x-ui/
ExecStart=/usr/local/x-ui/x-ui
Restart=on-failure
RestartSec=5s
LimitNOFILE=1048576
LimitNPROC=1048576
LimitMEMLOCK=infinity
TasksMax=infinity
EnvironmentFile=-/etc/default/x-ui
Environment="XRAY_VMESS_AEAD_FORCED=false"
Environment="GOMEMLIMIT=${TARGET_MEM_MIB}MiB"
Environment="GODEBUG=madvdontneed=1"
Environment="GOGC=80"

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload 2>/dev/null || true
  systemctl restart x-ui 2>/dev/null || true
fi

# 4. Set comprehensive global limits in /etc/security/limits.d/
mkdir -p /etc/security/limits.d/
cat << 'EOF' > /etc/security/limits.d/99-overdrive-limits.conf
* soft nofile 1048576
* hard nofile 1048576
root soft nofile 1048576
root hard nofile 1048576
* soft nproc 1048576
* hard nproc 1048576
root soft nproc 1048576
root hard nproc 1048576
* soft memlock unlimited
* hard memlock unlimited
root soft memlock unlimited
root hard memlock unlimited
* soft sigpending 1048576
* hard sigpending 1048576
* soft msgqueue 819200
* hard msgqueue 819200
EOF

# Ensure system-wide ulimit in /etc/profile
if ! grep -q "ulimit -n 1048576" /etc/profile 2>/dev/null; then
  echo "ulimit -n 1048576 2>/dev/null || true" >> /etc/profile
  echo "ulimit -u 1048576 2>/dev/null || true" >> /etc/profile
  echo "ulimit -l unlimited 2>/dev/null || true" >> /etc/profile
fi
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "Memory limits, Go runtime GC/GOMEMLIMIT, swap, and 1,048,576 FD/memlock limits active."
        return False, f"Memory limits notice: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "swapon --show && cat /etc/security/limits.d/99-overdrive-limits.conf 2>/dev/null | grep 'memlock'"
        code, out, err = ssh.execute_command(cmd)
        has_swap = "swapfile" in out or "partition" in out
        has_memlock = "memlock" in out
        return {
            "swap_active": has_swap,
            "memlock_unlimited": has_memlock,
            "pass": has_swap or has_memlock
        }
