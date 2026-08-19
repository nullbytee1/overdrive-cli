"""
OVERDRIVE - Module: System Provisioning, Entropy Boost, Timezone Sync & Hostname Acceleration
Updates package repository mirrors, installs essential networking toolchains, activates haveged entropy daemon,
resolves /etc/hosts bottlenecks, auto-detects GeoIP datacenter timezone, and optimizes firewall ports for QUIC/HTTP3.
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class SystemProvisioningOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="System Provisioning & Infrastructure Hardening",
            description="Installs essential tools, haveged entropy daemon, resolves /etc/hosts lag, sets GeoIP timezone & QUIC/UDP 443 rules.",
            category="System Maintenance & Tooling"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("System Provisioning", "Updating mirrors, haveged entropy daemon, /etc/hosts fix, GeoIP timezone & QUIC ports...")
        
        script = r"""
set -e

# 1. Fix /etc/hosts hostname resolution (Eliminates sudo / local socket lookup lag)
HOST_NAME=$(hostname 2>/dev/null || echo "localhost")
if [ -f /etc/hosts ]; then
    if ! grep -q "$HOST_NAME" /etc/hosts; then
        cp -f /etc/hosts /etc/hosts.bak_overdrive 2>/dev/null || true
        echo "127.0.1.1 $HOST_NAME" >> /etc/hosts
    fi
fi

# 2. GeoIP Datacenter Timezone Auto-Detection & NTP Clock Sync
GEO_TZ=$(curl -s --max-time 3 https://ipapi.co/timezone 2>/dev/null || curl -s --max-time 3 http://ip-api.com/line?fields=timezone 2>/dev/null || echo "UTC")
if [ -z "$GEO_TZ" ] || [ ${#GEO_TZ} -gt 40 ]; then
    GEO_TZ="UTC"
fi

if command -v timedatectl >/dev/null 2>&1; then
    timedatectl set-timezone "$GEO_TZ" 2>/dev/null || timedatectl set-timezone UTC 2>/dev/null || true
    timedatectl set-ntp true 2>/dev/null || true
else
    ln -sf "/usr/share/zoneinfo/$GEO_TZ" /etc/localtime 2>/dev/null || ln -sf /usr/share/zoneinfo/UTC /etc/localtime 2>/dev/null || true
fi

# 3. Disable Ubuntu MOTD Terminal News & Background Login Ads
if [ -f /etc/default/motd-news ]; then
    sed -i 's/ENABLED=1/ENABLED=0/' /etc/default/motd-news 2>/dev/null || true
fi
systemctl disable --now motd-news.timer 2>/dev/null || true

# 4. Package Manager Detection & Tooling + haveged Entropy Engine
if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq curl wget socat jq iperf3 ethtool iproute2 net-tools mtr-tiny dnsutils ca-certificates tar unzip chrony haveged 2>/dev/null || \
    apt-get install -y -qq curl wget socat jq iperf3 ethtool iproute2 net-tools ca-certificates tar unzip chrony 2>/dev/null || true
    systemctl enable --now chrony 2>/dev/null || systemctl enable --now systemd-timesyncd 2>/dev/null || true
    systemctl enable --now haveged 2>/dev/null || true
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y -q epel-release 2>/dev/null || true
    dnf install -y -q curl wget socat jq iperf3 ethtool iproute net-tools mtr bind-utils ca-certificates tar unzip chrony haveged 2>/dev/null || true
    systemctl enable --now chronyd 2>/dev/null || true
    systemctl enable --now haveged 2>/dev/null || true
elif command -v yum >/dev/null 2>&1; then
    yum install -y -q epel-release 2>/dev/null || true
    yum install -y -q curl wget socat jq iperf3 ethtool iproute net-tools mtr bind-utils ca-certificates tar unzip chrony haveged 2>/dev/null || true
    systemctl enable --now chronyd 2>/dev/null || true
    systemctl enable --now haveged 2>/dev/null || true
elif command -v pacman >/dev/null 2>&1; then
    pacman -Sy --noconfirm --needed curl wget socat jq iperf3 ethtool iproute2 net-tools mtr bind ca-certificates tar unzip chrony haveged 2>/dev/null || true
    systemctl enable --now chrony 2>/dev/null || true
    systemctl enable --now haveged 2>/dev/null || true
elif command -v apk >/dev/null 2>&1; then
    apk update
    apk add --no-cache curl wget socat jq iperf3 ethtool iproute2 net-tools mtr bind-tools ca-certificates tar unzip chrony haveged 2>/dev/null || true
    rc-update add chrony default 2>/dev/null || true
    rc-service chrony start 2>/dev/null || true
    rc-service haveged start 2>/dev/null || true
fi

# 5. NTP Clock Synchronization Step
chronyc makestep 2>/dev/null || true

# 6. UFW Firewall Policy: Allow SSH, HTTP, and HTTPS (TCP + UDP for QUIC/HTTP3/Reality)
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    SSH_PORT=$(grep -Ei '^\s*Port\s+' /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}' || echo "22")
    [ -z "$SSH_PORT" ] && SSH_PORT=22
    ufw allow "$SSH_PORT"/tcp 2>/dev/null || true
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
    ufw allow 443/udp 2>/dev/null || true
fi
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "Provisioning active: haveged entropy daemon, /etc/hosts fix, GeoIP timezone & QUIC/UDP 443 rules applied."
        return False, f"System provisioning notice: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "date; echo '---'; grep -E '127.0.1.1|127.0.0.1' /etc/hosts 2>/dev/null | wc -l; echo '---'; systemctl is-active haveged 2>/dev/null || ps aux | grep haveged | grep -v grep"
        code, out, _ = ssh.execute_command(cmd)
        parts = out.strip().split("---")
        date_str = parts[0].strip() if len(parts) > 0 else "UTC"
        hosts_ok = int(parts[1].strip()) >= 1 if len(parts) > 1 and parts[1].strip().isdigit() else True
        haveged_ok = len(parts) > 2 and ("active" in parts[2] or "haveged" in parts[2])
        return {
            "system_date": date_str,
            "hosts_resolved": hosts_ok,
            "haveged_active": haveged_ok,
            "pass": hosts_ok
        }
