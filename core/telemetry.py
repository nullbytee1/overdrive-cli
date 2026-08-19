"""
OVERDRIVE - Real-Time VPS Telemetry & Metrics Subsystem
Collects genuine live hardware metrics (Instantaneous CPU % from /proc/stat, RAM, Swap, Network IPs, active TCP connections, ping latency)
and live optimization status chips asynchronously in the background every 3 seconds without blocking the UI.
"""

import threading
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.ssh_client import SSHClientWrapper

class TelemetryData:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_updated = datetime.now()
        self.is_healthy = False
        
        # CPU
        self.load_avg = "0.00, 0.00, 0.00"
        self.cpu_pct = 0.0
        self.cpu_cores = 1
        self.cpu_history: List[float] = []
        
        # Memory
        self.mem_total_mb = 0
        self.mem_used_mb = 0
        self.mem_avail_mb = 0
        self.mem_pct = 0.0
        self.mem_history: List[float] = []
        
        # Swap
        self.swap_total_mb = 0
        self.swap_used_mb = 0
        self.swap_pct = 0.0
        
        # Network & Connections
        self.public_ip = "SYNCING..."
        self.local_ip = "SYNCING..."
        self.active_tcp_conns = 0
        self.total_conns = 0
        self.ping_rtt_ms = 0.0
        self.ping_history: List[float] = []
        self.port_443_active = False
        
        # Live Optimization Subsystem Status
        self.module_status: Dict[str, Any] = {
            "1": False,
            "2": False,
            "3": False,
            "4": False,
            "5": False,
            "6": False,
            "7": False,
            "8": False,
            "9": False,
            "10": False,
            "11": False,
            "12": "tool",
            "13": "tool",
            "A": "tool",
            "E": "tool",
            "R": "rollback",
            "Q": "exit"
        }

    @staticmethod
    def format_sparkline(data: list, width: int = 8) -> str:
        """Generates a clean, smooth, continuous Unicode sparkline chart for historical trends"""
        sparks = ["\u2581", "\u2582", "\u2583", "\u2584", "\u2585", "\u2586", "\u2587", "\u2588"]
        if not data:
            return "\u2581" * width
        recent = data[-width:]
        if len(recent) < width:
            recent = [recent[0]] * (width - len(recent)) + recent
        min_v = min(recent)
        max_v = max(recent)
        span = max_v - min_v if max_v > min_v else 1.0
        
        chars = []
        for v in recent:
            idx = int(((v - min_v) / span) * (len(sparks) - 1))
            idx = max(0, min(len(sparks) - 1, idx))
            chars.append(sparks[idx])
        return "".join(chars)

    def update(self, data: Dict[str, Any]):
        with self.lock:
            for k, v in data.items():
                if hasattr(self, k):
                    setattr(self, k, v)
                    
            if "cpu_pct" in data:
                self.cpu_history.append(float(data["cpu_pct"]))
                if len(self.cpu_history) > 16:
                    self.cpu_history.pop(0)
                    
            if "mem_pct" in data:
                self.mem_history.append(float(data["mem_pct"]))
                if len(self.mem_history) > 16:
                    self.mem_history.pop(0)
                    
            if "ping_rtt_ms" in data and float(data["ping_rtt_ms"]) > 0:
                self.ping_history.append(float(data["ping_rtt_ms"]))
                if len(self.ping_history) > 16:
                    self.ping_history.pop(0)
                    
            if "module_status" in data:
                self.module_status = data["module_status"]
                    
            self.last_updated = datetime.now()
            self.is_healthy = True

    def get_snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "last_updated": self.last_updated.strftime("%H:%M:%S"),
                "is_healthy": self.is_healthy,
                "load_avg": self.load_avg,
                "cpu_pct": self.cpu_pct,
                "cpu_cores": self.cpu_cores,
                "cpu_sparkline": self.format_sparkline(self.cpu_history, 8),
                "mem_total_mb": self.mem_total_mb,
                "mem_used_mb": self.mem_used_mb,
                "mem_avail_mb": self.mem_avail_mb,
                "mem_pct": self.mem_pct,
                "mem_sparkline": self.format_sparkline(self.mem_history, 8),
                "swap_total_mb": self.swap_total_mb,
                "swap_used_mb": self.swap_used_mb,
                "swap_pct": self.swap_pct,
                "public_ip": self.public_ip,
                "local_ip": self.local_ip,
                "active_tcp_conns": self.active_tcp_conns,
                "total_conns": self.total_conns,
                "ping_rtt_ms": self.ping_rtt_ms,
                "ping_sparkline": self.format_sparkline(self.ping_history, 8),
                "port_443_active": self.port_443_active,
                "module_status": dict(self.module_status)
            }

class TelemetryCollector:
    def __init__(self, ssh: SSHClientWrapper, telemetry: TelemetryData, poll_interval: float = 3.0):
        self.ssh = ssh
        self.telemetry = telemetry
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if not self._running:
            self._running = True
            # Perform immediate synchronous initial probe
            try:
                if self.ssh.is_connected:
                    init_data = self._collect_metrics()
                    if init_data:
                        self.telemetry.update(init_data)
            except Exception:
                pass
                
            self._thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _worker_loop(self):
        while self._running:
            try:
                if self.ssh.is_connected:
                    data = self._collect_metrics()
                    if data:
                        self.telemetry.update(data)
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def _collect_metrics(self) -> Optional[Dict[str, Any]]:
        probe_cmd = (
            "grep '^cpu ' /proc/stat; sleep 0.15; grep '^cpu ' /proc/stat; echo '---'; "
            "cat /proc/loadavg; echo '---'; "
            "grep MemTotal /proc/meminfo | awk '{print $2}'; "
            "grep MemAvailable /proc/meminfo | awk '{print $2}'; echo '---'; "
            "grep SwapTotal /proc/meminfo | awk '{print $2}'; "
            "grep SwapFree /proc/meminfo | awk '{print $2}'; echo '---'; "
            "ss -s 2>/dev/null | grep -i 'TCP:' || netstat -ant 2>/dev/null | grep ESTABLISHED | wc -l; echo '---'; "
            "ping -c 1 -W 1 1.1.1.1 2>/dev/null | grep -o 'time=[0-9.]*' | cut -d= -f2 || echo '0.0'; echo '---'; "
            "curl -4 -s --max-time 2 https://api.ipify.org 2>/dev/null || ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}' | grep -v '127.0.0.1' | head -n 1 || echo '127.0.0.1'; echo '---'; "
            "ss -tulpn 2>/dev/null | grep -q '443' && echo '1' || echo '0'; echo '---'; "
            "nproc; echo '---'; "
            "sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo 'cubic'; echo '---'; "
            "iptables -t mangle -L 2>/dev/null | grep -q 'TCPMSS' && echo '1' || echo '0'; echo '---'; "
            "[ -f /usr/local/bin/set-rps.sh ] && echo '1' || echo '0'; echo '---'; "
            "grep -q -E '1\\.1\\.1\\.1|8\\.8\\.8\\.8' /etc/resolv.conf 2>/dev/null && echo '1' || echo '0'; echo '---'; "
            "grep -q -i '^UseDNS no' /etc/ssh/sshd_config 2>/dev/null && echo '1' || echo '0'; echo '---'; "
            "grep -q -i 'transparent_hugepage=madvise' /etc/default/grub 2>/dev/null && echo '1' || echo '0'; echo '---'; "
            "[ -f /etc/x-ui/x-ui.db ] && echo '1' || echo '0'"
        )
        
        try:
            code, out, _ = self.ssh.execute_command(probe_cmd, stream_output=False)
            if code != 0 or not out:
                return None
                
            parts = [p.strip() for p in out.split("---")]
            if len(parts) < 9:
                return None
                
            # 1. Instantaneous CPU Usage % from /proc/stat differential
            stat_lines = [l.strip() for l in parts[0].splitlines() if l.startswith("cpu ")]
            calc_cpu_pct = 0.0
            if len(stat_lines) >= 2:
                try:
                    s1 = [float(x) for x in stat_lines[0].split()[1:]]
                    s2 = [float(x) for x in stat_lines[1].split()[1:]]
                    tot1, tot2 = sum(s1), sum(s2)
                    idle1 = s1[3] + (s1[4] if len(s1) > 4 else 0.0)
                    idle2 = s2[3] + (s2[4] if len(s2) > 4 else 0.0)
                    tot_d = tot2 - tot1
                    idle_d = idle2 - idle1
                    if tot_d > 0:
                        calc_cpu_pct = round(max(0.0, min(100.0, ((tot_d - idle_d) / tot_d) * 100.0)), 1)
                except Exception:
                    calc_cpu_pct = 0.0
            
            # 2. Load Average from /proc/loadavg
            load_raw = parts[1]
            load_tokens = load_raw.split()
            load_1 = float(load_tokens[0]) if len(load_tokens) > 0 and load_tokens[0].replace(".", "", 1).isdigit() else 0.0
            load_avg_str = f"{load_tokens[0]}, {load_tokens[1]}, {load_tokens[2]}" if len(load_tokens) >= 3 else "0.00, 0.00, 0.00"
            
            nproc_val = int(parts[8]) if len(parts) > 8 and parts[8].isdigit() and int(parts[8]) > 0 else 1
            if calc_cpu_pct == 0.0 and load_1 > 0.0:
                calc_cpu_pct = round(min(100.0, max(0.0, (load_1 / nproc_val) * 100.0)), 1)
            
            mem_lines = parts[2].split()
            mem_tot_kb = int(mem_lines[0]) if len(mem_lines) > 0 and mem_lines[0].isdigit() else 0
            mem_avail_kb = int(mem_lines[1]) if len(mem_lines) > 1 and mem_lines[1].isdigit() else 0
            mem_used_kb = max(0, mem_tot_kb - mem_avail_kb)
            
            mem_tot_mb = round(mem_tot_kb / 1024)
            mem_used_mb = round(mem_used_kb / 1024)
            mem_avail_mb = round(mem_avail_kb / 1024)
            mem_pct = round((mem_used_kb / max(1, mem_tot_kb)) * 100.0, 1) if mem_tot_kb > 0 else 0.0
            
            swap_lines = parts[3].split()
            swap_tot_kb = int(swap_lines[0]) if len(swap_lines) > 0 and swap_lines[0].isdigit() else 0
            swap_free_kb = int(swap_lines[1]) if len(swap_lines) > 1 and swap_lines[1].isdigit() else 0
            swap_used_kb = max(0, swap_tot_kb - swap_free_kb)
            swap_tot_mb = round(swap_tot_kb / 1024)
            swap_used_mb = round(swap_used_kb / 1024)
            swap_pct = round((swap_used_kb / max(1, swap_tot_kb)) * 100.0, 1) if swap_tot_kb > 0 else 0.0
            
            tcp_raw = parts[4]
            match_estab = re.search(r'estab(lished)?\s+(\d+)', tcp_raw, re.IGNORECASE)
            if match_estab:
                active_conns = int(match_estab.group(2))
            elif tcp_raw.strip().isdigit():
                active_conns = int(tcp_raw.strip())
            else:
                active_conns = 0
                
            ping_str = parts[5].strip()
            ping_val = float(ping_str) if ping_str.replace(".", "", 1).isdigit() else 0.0
            
            ip_str = parts[6].strip()
            pub_ip = ip_str if ip_str and ip_str != "127.0.0.1" else self.ssh.host
            loc_ip = pub_ip
            
            p443 = (parts[7] == "1")
            
            # Module Status Probing
            bbr_active = ("bbr" in parts[9]) if len(parts) > 9 else False
            mss_active = (parts[10] == "1") if len(parts) > 10 else False
            rps_active = (parts[11] == "1") if len(parts) > 11 else False
            swap_active = (swap_tot_mb > 0)
            storage_active = True if (bbr_active and swap_active) else False
            dns_active = (parts[12] == "1") if len(parts) > 12 else False
            ssh_active = (parts[13] == "1") if len(parts) > 13 else False
            prov_active = True if (dns_active or ssh_active) else False
            grub_active = (parts[14] == "1") if len(parts) > 14 else False
            xray_active = (parts[15] == "1") if len(parts) > 15 else False
            god_active = (bbr_active and mss_active and rps_active and swap_active and dns_active)
            
            mod_status = {
                "1": god_active,
                "2": bbr_active,
                "3": mss_active,
                "4": rps_active,
                "5": swap_active,
                "6": storage_active,
                "7": dns_active,
                "8": ssh_active,
                "9": prov_active,
                "10": grub_active,
                "11": xray_active,
                "12": "tool",
                "13": "tool",
                "A": "tool",
                "E": "tool",
                "R": "rollback",
                "Q": "exit"
            }
            
            return {
                "load_avg": load_avg_str,
                "cpu_pct": calc_cpu_pct,
                "cpu_cores": nproc_val,
                "mem_total_mb": mem_tot_mb,
                "mem_used_mb": mem_used_mb,
                "mem_avail_mb": mem_avail_mb,
                "mem_pct": mem_pct,
                "swap_total_mb": swap_tot_mb,
                "swap_used_mb": swap_used_mb,
                "swap_pct": swap_pct,
                "active_tcp_conns": active_conns,
                "ping_rtt_ms": ping_val,
                "public_ip": pub_ip,
                "local_ip": loc_ip,
                "port_443_active": p443,
                "module_status": mod_status
            }
        except Exception:
            return None
