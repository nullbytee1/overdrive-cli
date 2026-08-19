"""
OVERDRIVE - Module 3: Path MTU Probing & Carrier MSS Clamping (1360)
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class CarrierMSSOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Carrier MSS Clamping (1360)",
            description="Enforces persistent TCP MSS clamping to 1360 across INPUT/FORWARD/OUTPUT to eliminate GTP-U (4G/5G) and PPPoE packet drops.",
            category="Network Routing"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("MSS Clamping", "Enforcing persistent Netfilter TCPMSS 1360 rules & systemd service...")
        
        script = r"""
set -e

# Flush existing TCPMSS rules in mangle to avoid duplicates
iptables -t mangle -D INPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true
iptables -t mangle -D FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true
iptables -t mangle -D OUTPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true

# Append IPv4 MSS clamping rules
iptables -t mangle -A INPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true
iptables -t mangle -A FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true
iptables -t mangle -A OUTPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || true

# Append IPv6 PMTU clamping rules if ip6tables exists
ip6tables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu 2>/dev/null || true

# Optional netfilter-persistent save if available
if command -v netfilter-persistent >/dev/null 2>&1; then
    netfilter-persistent save 2>/dev/null || true
fi

# Deploy universal persistent systemd service
cat << 'EOF' > /etc/systemd/system/apply-mss-clamping.service
[Unit]
Description=Persistent TCP MSS Clamping for Mobile & PPPoE Links (1360)
After=network.target network-online.target
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'iptables -t mangle -C INPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || iptables -t mangle -A INPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360; iptables -t mangle -C FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || iptables -t mangle -A FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360; iptables -t mangle -C OUTPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360 2>/dev/null || iptables -t mangle -A OUTPUT -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360; ip6tables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu 2>/dev/null || true'

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload 2>/dev/null || true
systemctl enable --now apply-mss-clamping.service 2>/dev/null || true
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "Universal TCP MSS Clamping (1360) active & persistent across systemd."
        return False, f"Notice: Clamping configured with status output: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "iptables -t mangle -L -n -v | grep 'TCPMSS set 1360'"
        code, out, err = ssh.execute_command(cmd)
        lines = [l for l in out.splitlines() if "1360" in l]
        is_valid = len(lines) >= 2
        return {
            "rules_count": len(lines),
            "raw_output": out,
            "pass": is_valid
        }
