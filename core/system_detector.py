"""
OVERDRIVE - Enterprise Auto-Detection & Systems Discovery Engine
Probes the remote target over SSH to discover architecture, CPU cores, RAM, virtualization,
active network interfaces, MTU, kernel capabilities, block devices, and installed proxy stacks.
"""

import re
from typing import Dict, Any, Optional
from core.ssh_client import SSHClientWrapper

class SystemDetector:
    @staticmethod
    def detect_all(ssh: SSHClientWrapper) -> Dict[str, Any]:
        """Executes a single combined discovery probe to gather comprehensive host specs without latency"""
        cmd = (
            "uname -m; echo '===UNAME==='; uname -r; echo '===VIRT==='; "
            "systemd-detect-virt 2>/dev/null || cat /sys/class/dmi/id/product_name 2>/dev/null || echo 'kvm'; "
            "echo '===CPU==='; nproc; grep 'model name' /proc/cpuinfo 2>/dev/null | head -n 1 | cut -d: -f2; "
            "echo '===MEM==='; grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}'; "
            "echo '===NET==='; ip -o -4 route show to default 2>/dev/null | awk '{print $5}'; "
            "echo '===MTU==='; ip -o link show 2>/dev/null; "
            "echo '===DISKS==='; lsblk -d -n -o NAME,ROTA,TYPE 2>/dev/null || ls /sys/block; "
            "echo '===STACKS==='; "
            "test -f /etc/x-ui/x-ui.db && echo '3x-ui'; "
            "test -f /etc/xray/config.json && echo 'xray-core'; "
            "test -f /etc/sing-box/config.json && echo 'sing-box'; "
            "which nginx 2>/dev/null && echo 'nginx'; "
            "echo '===CONG==='; sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null; "
            "echo '===QDISC==='; sysctl -n net.core.default_qdisc 2>/dev/null"
        )
        
        info: Dict[str, Any] = {
            "arch": "x86_64",
            "kernel": "Linux",
            "virt": "KVM (Hardware Virtualization)",
            "cpu_cores": 2,
            "cpu_model": "Virtual CPU",
            "mem_total_kb": 2014208,
            "mem_total_mb": 1967,
            "mem_total_gb": 2.0,
            "primary_iface": "eth0",
            "current_mtu": 1500,
            "disks": ["vda"],
            "has_3xui": False,
            "has_xray": False,
            "has_singbox": False,
            "has_nginx": False,
            "detected_stacks": [],
            "congestion_control": "cubic",
            "qdisc": "pfifo_fast",
            "is_container": False
        }
        
        try:
            code, out, _ = ssh.execute_command(cmd, stream_output=False)
            if code != 0 or not out:
                return info
                
            parts = re.split(r'===([A-Z_]+)===\n?', out)
            
            # Initial part before first section marker is Arch
            if parts and len(parts) > 0:
                arch_val = parts[0].strip()
                if arch_val:
                    info["arch"] = arch_val
                    
            # Pairwise iteration over captured section names and their contents
            for i in range(1, len(parts), 2):
                sec_name = parts[i].strip()
                sec_body = parts[i+1].strip() if i + 1 < len(parts) else ""
                
                if sec_name == "UNAME":
                    info["kernel"] = sec_body.splitlines()[0].strip() if sec_body else "Linux"
                    
                elif sec_name == "VIRT":
                    virt_type = sec_body.splitlines()[0].strip() if sec_body else "kvm"
                    if virt_type in ("lxc", "openvz", "docker", "podman"):
                        info["is_container"] = True
                        info["virt"] = f"Container ({virt_type.upper()})"
                    else:
                        info["virt"] = f"Hypervisor ({virt_type.upper()})" if virt_type != "none" else "Bare-Metal Server"
                        
                elif sec_name == "CPU":
                    lines = sec_body.splitlines()
                    if len(lines) >= 1 and lines[0].strip().isdigit():
                        info["cpu_cores"] = int(lines[0].strip())
                    if len(lines) >= 2:
                        info["cpu_model"] = lines[1].strip()
                        
                elif sec_name == "MEM":
                    val = sec_body.strip()
                    if val.isdigit():
                        kb = int(val)
                        info["mem_total_kb"] = kb
                        info["mem_total_mb"] = round(kb / 1024)
                        info["mem_total_gb"] = round(kb / (1024 * 1024), 1)
                        
                elif sec_name == "NET":
                    iface = sec_body.strip().splitlines()[0] if sec_body else "eth0"
                    if iface:
                        info["primary_iface"] = iface
                        
                elif sec_name == "MTU":
                    p_iface = info["primary_iface"]
                    match = re.search(rf'{p_iface}.*?mtu\s+(\d+)', sec_body)
                    if match:
                        info["current_mtu"] = int(match.group(1))
                        
                elif sec_name == "DISKS":
                    disk_list = []
                    for line in sec_body.splitlines():
                        toks = line.strip().split()
                        if toks and toks[0] not in ("NAME", "loop"):
                            disk_list.append(toks[0])
                    if disk_list:
                        info["disks"] = disk_list
                        
                elif sec_name == "STACKS":
                    stacks = []
                    if "3x-ui" in sec_body:
                        info["has_3xui"] = True
                        stacks.append("3x-ui (Xray Management)")
                    if "xray-core" in sec_body:
                        info["has_xray"] = True
                        stacks.append("Xray-Core Engine")
                    if "sing-box" in sec_body:
                        info["has_singbox"] = True
                        stacks.append("Sing-Box Core")
                    if "nginx" in sec_body:
                        info["has_nginx"] = True
                        stacks.append("Nginx Web Gateway")
                    info["detected_stacks"] = stacks
                    
                elif sec_name == "CONG":
                    info["congestion_control"] = sec_body.strip() or "cubic"
                    
                elif sec_name == "QDISC":
                    info["qdisc"] = sec_body.strip() or "pfifo_fast"
                    
        except Exception:
            pass
            
        return info
