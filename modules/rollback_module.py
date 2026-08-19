"""
OVERDRIVE - Rollback & Factory Revert Module
Restores remote host configuration from pre-flight backups or safe Linux default baseline.
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class RollbackModule(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="System Configuration Rollback & Restore",
            description="Restores sysctl, Netfilter rules, RPS services, and proxy configurations from pre-flight backups.",
            category="System Recovery & Reversion"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("System Rollback", "Scanning pre-flight backups and reverting configurations...")
        
        script = r"""
set -e

# 1. Restore Sysctl from latest backup if available
LATEST_SYSCTL_BAK=$(ls -d /etc/sysctl.d/backup_overdrive_* 2>/dev/null | tail -n 1 || echo "")
if [ -n "$LATEST_SYSCTL_BAK" ] && [ -d "$LATEST_SYSCTL_BAK" ]; then
    echo "Restoring sysctl configs from $LATEST_SYSCTL_BAK..."
    rm -f /etc/sysctl.d/99-vps-optimization.conf /etc/sysctl.d/99-custom-optimization.conf
    cp -f "$LATEST_SYSCTL_BAK"/*.conf /etc/sysctl.d/ 2>/dev/null || true
    if [ -f "$LATEST_SYSCTL_BAK/sysctl.conf" ]; then
        cp -f "$LATEST_SYSCTL_BAK/sysctl.conf" /etc/sysctl.conf 2>/dev/null || true
    fi
else
    echo "No backup folder found; removing OVERDRIVE custom sysctl rules..."
    rm -f /etc/sysctl.d/99-vps-optimization.conf
fi
sysctl --system 2>/dev/null || true

# 2. Revert MSS Clamping & Netfilter
systemctl stop apply-mss-clamping.service 2>/dev/null || true
systemctl disable apply-mss-clamping.service 2>/dev/null || true
rm -f /etc/systemd/system/apply-mss-clamping.service
iptables -t mangle -D INPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true
iptables -t mangle -D FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true
iptables -t mangle -D OUTPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true

# 3. Revert RPS / XPS Multi-Core Steering
systemctl stop set-rps.service 2>/dev/null || true
systemctl disable set-rps.service 2>/dev/null || true
rm -f /etc/systemd/system/set-rps.service /usr/local/bin/set-rps.sh

# 4. Restore 3x-ui Database if backup exists
LATEST_DB_BAK=$(ls /etc/x-ui/x-ui.db.bak_* 2>/dev/null | tail -n 1 || echo "")
if [ -n "$LATEST_DB_BAK" ] && [ -f "$LATEST_DB_BAK" ]; then
    echo "Restoring 3x-ui database from $LATEST_DB_BAK..."
    systemctl stop x-ui 2>/dev/null || true
    cp -f "$LATEST_DB_BAK" /etc/x-ui/x-ui.db
    systemctl start x-ui 2>/dev/null || true
fi

systemctl daemon-reload 2>/dev/null || true
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "Rollback successfully completed. System restored to pre-flight baseline."
        return False, f"Rollback finished with notice: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "test ! -f /etc/sysctl.d/99-vps-optimization.conf && test ! -f /etc/systemd/system/apply-mss-clamping.service"
        code, out, err = ssh.execute_command(cmd)
        return {
            "reverted": code == 0,
            "pass": code == 0
        }
