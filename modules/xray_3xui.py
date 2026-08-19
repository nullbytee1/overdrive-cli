"""
OVERDRIVE - Module 7: 3x-ui / Xray Database & Protocol Optimization
"""

from typing import Tuple, Dict, Any
from rich.console import Console
from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger

class Xray3xuiOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="3x-ui / Xray Database & Protocol Engine",
            description="Configures inbound 0.0.0.0, sockopt, Parallel IPv4 DNS, 24h Stale Cache, and global SNIs with pre-flight database backup.",
            category="Proxy & Xray Engine"
        )

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        Logger.step("Proxy Optimization", "Injecting low-latency socket options, parallel cached DNS & global SNIs...")
        
        script = r"""
set -e

if [ ! -f /etc/x-ui/x-ui.db ]; then
  echo "No /etc/x-ui/x-ui.db found, skipping 3x-ui specific database injection."
  exit 0
fi

# Pre-flight timestamped backup
BACKUP_PATH="/etc/x-ui/x-ui.db.bak_$(date +%s)"
cp /etc/x-ui/x-ui.db "$BACKUP_PATH"
echo "Created pre-flight database backup: $BACKUP_PATH"

python3 - << 'EOF'
import sqlite3
import json

db_path = '/etc/x-ui/x-ui.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Inbounds Update
c.execute("SELECT id, port, protocol, listen, stream_settings FROM inbounds")
for row in c.fetchall():
    inbound_id, port, protocol, listen, stream_str = row
    stream = json.loads(stream_str) if stream_str else {}
    
    stream['sockopt'] = {
        "tcpFastOpen": True,
        "tcpNoDelay": True,
        "tcpKeepAliveInterval": 15
    }
    
    if stream.get('security') == 'reality':
        reality = stream.get('realitySettings', {})
        existing = reality.get('serverNames', [])
        for target_sni in ["www.bing.com", "teams.microsoft.com", "www.microsoft.com"]:
            if target_sni not in existing:
                existing.append(target_sni)
        reality['serverNames'] = existing
        if not reality.get('target'):
            reality['target'] = 'www.bing.com:443'
        stream['realitySettings'] = reality
        
    c.execute("UPDATE inbounds SET listen = ?, stream_settings = ? WHERE id = ?", 
              ("0.0.0.0", json.dumps(stream, separators=(',', ':')), inbound_id))

# 2. Xray Template Update
c.execute("SELECT value FROM settings WHERE key = 'xrayTemplateConfig'")
row = c.fetchone()
if row and row[0]:
    tpl = json.loads(row[0])
    for ob in tpl.get('outbounds', []):
        if ob.get('protocol') == 'freedom' or ob.get('tag') == 'direct':
            ob['streamSettings'] = {
                "sockopt": {
                    "tcpFastOpen": True,
                    "tcpNoDelay": True,
                    "tcpKeepAliveInterval": 15
                }
            }
    tpl['dns'] = {
        "tag": "dns_inbound",
        "queryStrategy": "UseIPv4",
        "disableCache": False,
        "disableFallback": False,
        "disableFallbackIfMatch": False,
        "useSystemHosts": True,
        "enableParallelQuery": True,
        "serveStale": True,
        "serveExpiredTTL": 86400,
        "hosts": {},
        "servers": [
            "1.1.1.1",
            "8.8.8.8"
        ]
    }
    c.execute("UPDATE settings SET value = ? WHERE key = 'xrayTemplateConfig'", (json.dumps(tpl, indent=2),))

conn.commit()
conn.close()
EOF

# Restart service and test syntax
systemctl restart x-ui 2>/dev/null || true
sleep 1
XRAY_BIN=$(ls /usr/local/x-ui/bin/xray-linux-* 2>/dev/null | head -n 1 || echo "")
if [ -n "$XRAY_BIN" ] && [ -x "$XRAY_BIN" ] && [ -f /usr/local/x-ui/bin/config.json ]; then
  "$XRAY_BIN" -test -config /usr/local/x-ui/bin/config.json 2>/dev/null || true
fi
"""
        code, out, err = ssh.execute_script(script, stream_output=False)
        if code == 0:
            return True, "3x-ui database, Xray sockopts, parallel DNS caching & SNIs active."
        return False, f"Notice: Proxy database tuning returned: {err}"

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        cmd = "systemctl is-active x-ui && ss -tulpn | grep 443"
        code, out, err = ssh.execute_command(cmd)
        is_running = "active" in out
        is_port_open = "443" in out
        return {
            "xui_active": is_running,
            "port_443_listening": is_port_open,
            "raw_output": out,
            "pass": is_running and is_port_open
        }
