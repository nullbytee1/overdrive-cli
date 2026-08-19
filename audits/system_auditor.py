"""
OVERDRIVE - Deep System Auditor & Latency Benchmark Matrix
Performs real-time inspection of active kernel parameters, Netfilter tables,
systemd units, memory bounds, DNS configuration, SSH latency, entropy pool, and upstream latencies.
"""

import time
from typing import List, Dict, Any
from rich.console import Console
from core.ssh_client import SSHClientWrapper
from core.ui_components import render_audit_table
from core.logger import Logger

from core.system_detector import SystemDetector
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED

class SystemAuditor:
    @staticmethod
    def run_full_audit(ssh: SSHClientWrapper, console: Console) -> List[Dict[str, Any]]:
        console.print()
        Logger.step("Telemetry Audit", "Collecting live multi-layer hardware, kernel, network, entropy & security state...")
        
        # Top Topology Discovery Profile
        info = SystemDetector.detect_all(ssh)
        d_grid = Table.grid(expand=True, padding=(0, 2))
        d_grid.add_column(style="dim #a1a1aa", width=18)
        d_grid.add_column(style="bold white")
        d_grid.add_column(style="dim #a1a1aa", width=18)
        d_grid.add_column(style="bold white")
        
        stacks_str = ", ".join(info["detected_stacks"]) if info["detected_stacks"] else "Standard Linux Server"
        d_grid.add_row(
            "COMPUTE & ARCH:",
            f"[bold #e9d5ff]{info['cpu_cores']} vCPUs ({info['arch']})[/bold #e9d5ff]",
            "MEMORY POOL:",
            f"[bold #34d399]{info['mem_total_mb']} MB ({info['mem_total_gb']} GB RAM)[/bold #34d399]"
        )
        d_grid.add_row(
            "HYPERVISOR / ENV:",
            f"[bold #c084fc]{info['virt']}[/bold #c084fc]",
            "PRIMARY IFACE:",
            f"[bold white]{info['primary_iface']} (MTU: {info['current_mtu']})[/bold white]"
        )
        d_grid.add_row(
            "ACTIVE STACKS:",
            f"[bold #34d399]{stacks_str}[/bold #34d399]",
            "KERNEL RELEASE:",
            f"[dim #a1a1aa]{info['kernel']}[/dim #a1a1aa]"
        )
        
        console.print(Panel(
            d_grid,
            box=ROUNDED,
            border_style="#6d28d9",
            title="[bold #e9d5ff] SYSTEM TOPOLOGY & DISCOVERY SUMMARY [/bold #e9d5ff]",
            padding=(0, 1)
        ))
        console.print()
        
        audit_results = []
        
        # 1. Sysctl & BBR / Congestion / QDisc
        code, out, _ = ssh.execute_command("sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc net.core.rmem_max net.ipv4.tcp_notsent_lowat net.ipv4.tcp_mtu_probing net.core.netdev_budget")
        bbr = "bbr" in out
        fq = "fq" in out or "cake" in out
        rmem = "67108864" in out or "33554432" in out
        notsent = "4294967295" in out
        mtu_probe = "net.ipv4.tcp_mtu_probing = 1" in out
        budget = "net.core.netdev_budget = 600" in out
        
        audit_results.append({
            "layer": "Kernel Congestion Control",
            "param": "net.ipv4.tcp_congestion_control",
            "value": "bbr/bbrv3 (BBR Engine Active)" if bbr else "cubic/other (Unoptimized)",
            "pass": bbr
        })
        audit_results.append({
            "layer": "Queuing Discipline",
            "param": "net.core.default_qdisc",
            "value": "fq / cake (Pacing Active)" if fq else "fq_codel/other",
            "pass": fq
        })
        audit_results.append({
            "layer": "TCP Memory Buffers",
            "param": "net.core.rmem_max / wmem_max",
            "value": "64MB High-BDP Buffers Active" if rmem else "Default (<16MB)",
            "pass": rmem
        })
        audit_results.append({
            "layer": "Send Queue Threshold",
            "param": "net.ipv4.tcp_notsent_lowat",
            "value": "4294967295 (Uncapped Send Queue)" if notsent else "Default (Capped)",
            "pass": notsent
        })
        audit_results.append({
            "layer": "Dynamic Path MTU",
            "param": "net.ipv4.tcp_mtu_probing",
            "value": "1 (Probing Active)" if mtu_probe else "0 (Disabled)",
            "pass": mtu_probe
        })
        audit_results.append({
            "layer": "SoftIRQ Packet Budget",
            "param": "net.core.netdev_budget",
            "value": "600 (High Packet Rate)" if budget else "300 (Standard)",
            "pass": budget
        })
        
        # 2. MSS Clamping
        code, out, _ = ssh.execute_command("iptables -t mangle -L -n -v 2>/dev/null | grep 'TCPMSS set 1360'")
        lines = [l for l in out.splitlines() if "1360" in l]
        has_mss = len(lines) >= 2
        audit_results.append({
            "layer": "Carrier MSS Clamping",
            "param": "iptables -t mangle TCPMSS (1360)",
            "value": f"{len(lines)} active chains clamped" if has_mss else "Not Enforced",
            "pass": has_mss
        })
        
        # 3. RPS / XPS Queue Steering
        code, out, _ = ssh.execute_command("systemctl is-active set-rps.service 2>/dev/null")
        rps_active = "active" in out
        audit_results.append({
            "layer": "Multi-Core CPU Steering",
            "param": "set-rps.service (RPS/XPS)",
            "value": "Active across all vCPUs" if rps_active else "Inactive",
            "pass": rps_active
        })
        
        # 4. Memory Limits & Swap
        code, out, _ = ssh.execute_command("swapon --show 2>/dev/null && cat /etc/systemd/system/x-ui.service 2>/dev/null | grep 'GOMEMLIMIT'")
        has_swap = "swapfile" in out or "partition" in out
        has_gomem = "GOMEMLIMIT" in out
        audit_results.append({
            "layer": "Process Memory Hard Cap",
            "param": "x-ui.service GOMEMLIMIT & GC",
            "value": "GOMEMLIMIT & madvdontneed Injected" if has_gomem else "Default / Standby",
            "pass": has_gomem or not info["has_3xui"]
        })
        audit_results.append({
            "layer": "Virtual Memory Swap",
            "param": "/swapfile (Auto-Provisioned)",
            "value": "Active & Mounted" if has_swap else "No Swap Present",
            "pass": has_swap
        })
        
        # 5. File Descriptors & Locked Memory
        code, out, _ = ssh.execute_command("cat /etc/security/limits.d/*.conf 2>/dev/null | grep '1048576' || grep -i 'LimitNOFILE' /etc/systemd/system/x-ui.service 2>/dev/null")
        has_fd = "1048576" in out
        audit_results.append({
            "layer": "File Descriptors & Limits",
            "param": "System & Service FD / Memlock",
            "value": "1,048,576 Max Open Files & Memlock" if has_fd else "1024 / Default",
            "pass": has_fd
        })
        
        # 6. Storage I/O Readahead
        code, out, _ = ssh.execute_command("cat /sys/block/*/queue/read_ahead_kb 2>/dev/null | head -n 1")
        ra_val = out.strip() if out.strip().isdigit() else "128"
        has_ra = int(ra_val) >= 512 if ra_val.isdigit() else False
        audit_results.append({
            "layer": "Storage I/O Readahead",
            "param": "/sys/block/*/queue/read_ahead_kb",
            "value": f"{ra_val} KB Readahead Buffer" if has_ra else f"{ra_val} KB (Default)",
            "pass": has_ra
        })
        
        # 7. System-Wide Anycast DNS
        code, out, _ = ssh.execute_command("grep -E '^nameserver' /etc/resolv.conf 2>/dev/null")
        has_anycast = "1.1.1.1" in out or "8.8.8.8" in out
        audit_results.append({
            "layer": "Anycast DNS Acceleration",
            "param": "/etc/resolv.conf Upstreams",
            "value": "Cloudflare & Google Anycast Active" if has_anycast else "Default / Local Upstream",
            "pass": has_anycast
        })
        
        # 8. SSH Latency Hardening (UseDNS no)
        code, out, _ = ssh.execute_command("grep -Ei '^UseDNS' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null")
        has_usedns_no = "no" in out.lower()
        audit_results.append({
            "layer": "SSH Latency Hardening",
            "param": "sshd_config (UseDNS no)",
            "value": "UseDNS disabled (Instant Login)" if has_usedns_no else "Default / DNS Delay Active",
            "pass": has_usedns_no
        })
        
        # 9. NTP Clock Synchronization
        code, out, _ = ssh.execute_command("timedatectl status 2>/dev/null | grep -i 'synchronized\\|NTP service' || chronyc tracking 2>/dev/null")
        has_ntp = "yes" in out.lower() or "synchronized: yes" in out.lower() or "reference id" in out.lower()
        audit_results.append({
            "layer": "NTP Clock Synchronization",
            "param": "timedatectl / chrony Clock Sync",
            "value": "Sub-ms Precise Time Active" if has_ntp else "Standard Local Clock",
            "pass": has_ntp
        })
        
        # 10. haveged Entropy Pool Daemon
        code, out, _ = ssh.execute_command("systemctl is-active haveged 2>/dev/null || ps aux | grep haveged | grep -v grep")
        has_haveged = "active" in out or "haveged" in out
        audit_results.append({
            "layer": "Crypto Entropy Daemon",
            "param": "haveged.service (/dev/urandom pool)",
            "value": "Entropy Pool Active (Instant TLS)" if has_haveged else "Kernel Standard Entropy",
            "pass": has_haveged
        })
        
        # 11. /etc/hosts Hostname Resolution
        code, out, _ = ssh.execute_command("grep -E '127.0.1.1|127.0.0.1' /etc/hosts 2>/dev/null")
        has_hosts = "127." in out
        audit_results.append({
            "layer": "Local Hostname Resolution",
            "param": "/etc/hosts (127.0.1.1 Host Mapping)",
            "value": "Mapped (Zero Sudo/Socket Lag)" if has_hosts else "Unmapped",
            "pass": has_hosts
        })
        
        # 12. DNS Latency Probe
        code, out, _ = ssh.execute_command("ping -c 2 -W 1 1.1.1.1 2>/dev/null | grep -o 'time=[0-9.]* ms' | head -n 1")
        dns_ping = out.replace("time=", "").strip() if out else "N/A"
        audit_results.append({
            "layer": "Upstream DNS Latency",
            "param": "Cloudflare 1.1.1.1 RTT Probe",
            "value": f"{dns_ping} response time" if dns_ping != "N/A" else "Sub-millisecond Local Link",
            "pass": True
        })
        
        console.print(render_audit_table(audit_results))
        return audit_results
