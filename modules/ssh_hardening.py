"""
OVERDRIVE - Module: SSH Server Latency & Security Hardening
Eliminates DNS lookup connection stalls (UseDNS no), disables GSSAPI delays,
enforces 30s TCP keepalives, and safely reloads sshd with pre-flight configuration validation.
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class SSHHardenOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="SSH Server Latency & Security Hardening",
            description="Eliminates DNS lookup connection stalls (UseDNS no), disables GSSAPI delays, and enforces 30s keepalive heartbeats.",
            category="Security & Access Gateway"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("SSH Hardening", "Optimizing sshd daemon: UseDNS no, keepalive intervals & pre-flight syntax validation...")
        
        script = r"""
set -e

SSHD_CONF="/etc/ssh/sshd_config"
if [ ! -f "$SSHD_CONF" ]; then
    echo "Notice: /etc/ssh/sshd_config not found, skipping sshd hardening."
    exit 0
fi

# 1. Pre-flight timestamped backup
BACKUP_SSHD="/etc/ssh/sshd_config.bak_$(date +%Y%m%d_%H%M%S)"
cp -f "$SSHD_CONF" "$BACKUP_SSHD"

# 2. Update / Inject directives safely
sed -i -E 's/^[#\s]*UseDNS\s+.*/UseDNS no/' "$SSHD_CONF" || true
if ! grep -q "^UseDNS" "$SSHD_CONF"; then
    echo "UseDNS no" >> "$SSHD_CONF"
fi

sed -i -E 's/^[#\s]*GSSAPIAuthentication\s+.*/GSSAPIAuthentication no/' "$SSHD_CONF" || true
if ! grep -q "^GSSAPIAuthentication" "$SSHD_CONF"; then
    echo "GSSAPIAuthentication no" >> "$SSHD_CONF"
fi

sed -i -E 's/^[#\s]*ClientAliveInterval\s+.*/ClientAliveInterval 30/' "$SSHD_CONF" || true
if ! grep -q "^ClientAliveInterval" "$SSHD_CONF"; then
    echo "ClientAliveInterval 30" >> "$SSHD_CONF"
fi

sed -i -E 's/^[#\s]*ClientAliveCountMax\s+.*/ClientAliveCountMax 5/' "$SSHD_CONF" || true
if ! grep -q "^ClientAliveCountMax" "$SSHD_CONF"; then
    echo "ClientAliveCountMax 5" >> "$SSHD_CONF"
fi

sed -i -E 's/^[#\s]*TCPKeepAlive\s+.*/TCPKeepAlive yes/' "$SSHD_CONF" || true
if ! grep -q "^TCPKeepAlive" "$SSHD_CONF"; then
    echo "TCPKeepAlive yes" >> "$SSHD_CONF"
fi

# Also support sshd_config.d drop-in directory if present
if [ -d /etc/ssh/sshd_config.d ]; then
    cat << 'EOF' > /etc/ssh/sshd_config.d/99-overdrive-ssh.conf
UseDNS no
GSSAPIAuthentication no
ClientAliveInterval 30
ClientAliveCountMax 5
TCPKeepAlive yes
EOF
fi

# 3. Validate syntax before applying
if sshd -t 2>/dev/null; then
    systemctl reload ssh 2>/dev/null || systemctl reload sshd 2>/dev/null || service ssh reload 2>/dev/null || service sshd reload 2>/dev/null || true
else
    echo "Warning: sshd syntax check reported errors; reverting to pre-flight backup..."
    cp -f "$BACKUP_SSHD" "$SSHD_CONF"
    exit 1
fi
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "SSH server latency optimization active (UseDNS no, 30s keepalives, GSSAPI disabled)."
        return False, f"SSH hardening notice: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "grep -Ei '^(UseDNS|ClientAliveInterval)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null"
        code, out, _ = ssh.execute_command(cmd)
        has_usedns = "no" in out.lower()
        has_interval = "30" in out
        return {
            "usedns_no": has_usedns,
            "keepalive_30s": has_interval,
            "raw_output": out,
            "pass": has_usedns or has_interval
        }
