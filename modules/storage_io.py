"""
OVERDRIVE - Module 6: Storage I/O Scheduler & Kernel VM Dirty Writeback
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class StorageIOOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Storage I/O & Kernel Dirty Writeback",
            description="Tunes disk I/O queue readahead, VM dirty background/ratio writeback, and inotify resources.",
            category="Disk & Storage"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("Storage Tuning", "Optimizing block device readahead queues & kernel dirty page writeback...")
        
        script = r"""
set -e

# Tune readahead buffers and queue scheduler for all physical disks
for disk in /sys/block/sd* /sys/block/vd* /sys/block/nvme*n1; do
  [ -d "$disk" ] || continue
  if [ -f "$disk/queue/read_ahead_kb" ]; then
    echo 1024 > "$disk/queue/read_ahead_kb" 2>/dev/null || true
  fi
  if [ -f "$disk/queue/scheduler" ]; then
    grep -q "none" "$disk/queue/scheduler" && echo "none" > "$disk/queue/scheduler" 2>/dev/null || true
  fi
done

# Persist readahead across reboots via udev
mkdir -p /etc/udev/rules.d/
cat << 'EOF' > /etc/udev/rules.d/99-overdrive-readahead.rules
ACTION=="add|change", KERNEL=="sd[a-z]*|vd[a-z]*|nvme[0-9]*n[0-9]*", ATTR{queue/read_ahead_kb}="1024"
EOF
udevadm control --reload-rules 2>/dev/null || true

# Add storage and dirty page parameters to sysctl (deduplicated)
touch /etc/sysctl.d/99-vps-optimization.conf
sed -i '/vm.dirty_/d' /etc/sysctl.d/99-vps-optimization.conf 2>/dev/null || true

cat << 'EOF' >> /etc/sysctl.d/99-vps-optimization.conf
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
vm.dirty_expire_centisecs = 3000
vm.dirty_writeback_centisecs = 500
EOF

sysctl -p /etc/sysctl.d/99-vps-optimization.conf 2>/dev/null || sysctl --system 2>/dev/null || true
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "Storage I/O schedulers and dirty page writeback ratios tuned."
        return False, f"Failed to tune storage I/O: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "sysctl vm.dirty_background_ratio vm.dirty_ratio"
        code, out, err = ssh.execute_command(cmd)
        is_ok = "vm.dirty_ratio = 10" in out
        return {
            "dirty_ratio_ok": is_ok,
            "raw_output": out,
            "pass": is_ok
        }
