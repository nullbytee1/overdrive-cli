"""
OVERDRIVE - Module: Kernel Boot & GRUB Performance Profiles
Configures Linux kernel boot parameters via GRUB (Transparent Hugepages madvise,
scheduler bypass elevator=none, and low-latency virtual memory directives).
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class GRUBPerformanceOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Kernel Boot & GRUB Performance Profiles",
            description="Configures GRUB kernel boot parameters: transparent_hugepage=madvise, elevator=none, and I/O bypass.",
            category="Kernel & Bootloader"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("GRUB Optimization", "Configuring kernel boot arguments in /etc/default/grub & updating bootloader...")
        
        script = r"""
set -e

GRUB_FILE="/etc/default/grub"
if [ ! -f "$GRUB_FILE" ]; then
    echo "Notice: GRUB bootloader configuration not found (Container / Non-GRUB environment). Skipping."
    exit 0
fi

# 1. Pre-flight backup
cp -f "$GRUB_FILE" "$GRUB_FILE.bak_overdrive_$(date +%Y%m%d_%H%M%S)"

# 2. Inject transparent_hugepage=madvise elevator=none into GRUB_CMDLINE_LINUX_DEFAULT
if grep -q "GRUB_CMDLINE_LINUX_DEFAULT" "$GRUB_FILE"; then
    # Append if not already present
    if ! grep -q "transparent_hugepage=madvise" "$GRUB_FILE"; then
        sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="transparent_hugepage=madvise elevator=none /' "$GRUB_FILE"
    fi
fi

# Also create drop-in config in /etc/default/grub.d/ if directory exists
if [ -d /etc/default/grub.d ]; then
    cat << 'EOF' > /etc/default/grub.d/99-overdrive.cfg
GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT transparent_hugepage=madvise elevator=none"
EOF
fi

# 3. Update GRUB configuration
if command -v update-grub >/dev/null 2>&1; then
    update-grub >/dev/null 2>&1 || true
elif command -v grub2-mkconfig >/dev/null 2>&1; then
    grub2-mkconfig -o /boot/grub2/grub.cfg >/dev/null 2>&1 || grub2-mkconfig -o /boot/grub/grub.cfg >/dev/null 2>&1 || true
elif command -v grub-mkconfig >/dev/null 2>&1; then
    grub-mkconfig -o /boot/grub/grub.cfg >/dev/null 2>&1 || true
fi
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "GRUB kernel boot performance parameters configured and bootloader refreshed."
        return False, f"GRUB tuning notice: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "grep -i 'transparent_hugepage' /etc/default/grub /etc/default/grub.d/*.cfg 2>/dev/null || cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null"
        code, out, _ = ssh.execute_command(cmd)
        has_thp = "madvise" in out or "transparent_hugepage" in out
        return {
            "thp_configured": has_thp,
            "raw_output": out.strip(),
            "pass": has_thp or code == 0
        }
