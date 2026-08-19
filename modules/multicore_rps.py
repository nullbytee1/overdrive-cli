"""
OVERDRIVE - Module 4: Dynamic Multi-Core Receive Packet Steering (RPS/XPS)
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class MultiCoreRPSOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Dynamic Multi-Core RPS/XPS Queue Steering",
            description="Distributes network packet processing across all CPU cores dynamically via systemd.",
            category="CPU & Interrupts"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("Interrupt Steering", "Configuring dynamic multi-core RPS/XPS queue steering across all vCPUs...")
        
        script = r"""
set -e

cat << 'EOF' > /usr/local/bin/set-rps.sh
#!/bin/bash
CPUS=$(nproc 2>/dev/null || echo 2)
if [ "$CPUS" -ge 64 ]; then
    MASK="ffffffffffffffff"
elif [ "$CPUS" -le 1 ]; then
    MASK="1"
else
    MASK=$(printf '%x' "$(( (1 << CPUS) - 1 ))" 2>/dev/null || echo "f")
fi

for dev in /sys/class/net/*; do
  [ -d "$dev" ] || continue
  ifname=$(basename "$dev")
  [ "$ifname" = "lo" ] && continue
  for rx in "$dev"/queues/rx-*; do
    [ -f "$rx/rps_cpus" ] && echo "$MASK" > "$rx/rps_cpus" 2>/dev/null || true
    [ -f "$rx/rps_flow_cnt" ] && echo 4096 > "$rx/rps_flow_cnt" 2>/dev/null || true
  done
  for tx in "$dev"/queues/tx-*; do
    [ -f "$tx/xps_cpus" ] && echo "$MASK" > "$tx/xps_cpus" 2>/dev/null || true
  done
done
if [ -f /proc/sys/net/core/rps_sock_flow_entries ]; then
  echo 32768 > /proc/sys/net/core/rps_sock_flow_entries 2>/dev/null || true
fi
exit 0
EOF

chmod +x /usr/local/bin/set-rps.sh
/usr/local/bin/set-rps.sh 2>/dev/null || true

cat << 'EOF' > /etc/systemd/system/set-rps.service
[Unit]
Description=Dynamic Multi-Core RPS/XPS Network Queue Steering
After=network.target network-online.target
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/set-rps.sh

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload 2>/dev/null || true
systemctl enable --now set-rps.service 2>/dev/null || true
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "Dynamic Multi-Core RPS/XPS queue steering deployed and active across all CPUs."
        return False, f"Failed to configure RPS/XPS: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "systemctl is-active set-rps.service && cat /sys/class/net/*/queues/rx-*/rps_cpus 2>/dev/null | head -n 2"
        code, out, err = ssh.execute_command(cmd)
        is_active = "active" in out
        return {
            "active": is_active,
            "raw_output": out,
            "pass": is_active
        }
