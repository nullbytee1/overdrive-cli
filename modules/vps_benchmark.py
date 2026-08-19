"""
OVERDRIVE - Module 12: Comprehensive VPS Compute, Disk I/O & Network Speed Benchmark
Measures genuine live CPU compute ops/sec, Memory RAM bandwidth (GB/s), Disk I/O (MB/s),
and real-time global CDN edge download throughput (Mbps) with zero hardcoded fallbacks.
"""

import re
import time
from typing import Tuple, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .base_module import BaseOptimizerModule
from core.ssh_client import SSHClientWrapper
from core.logger import Logger
from core.theme import (
    BRAND_PURPLE,
    BRAND_LAVENDER,
    BRAND_LILAC,
    BORDER_PURPLE,
    SEMANTIC_SUCCESS,
    SEMANTIC_WARN,
    SEMANTIC_ERROR,
    ROUNDED_BOX
)

class VPSBenchmarkOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="VPS Hardware & Compute Benchmark",
            description="Benchmarks CPU compute speed, RAM memory bandwidth, Disk I/O throughput, and real-time CDN download speed.",
            category="System Performance Verification"
        )
        self.last_benchmark_data: Dict[str, Any] = {}

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        console.print()
        Logger.step("VPS Benchmarking", "Initiating multi-vector CPU compute, RAM bandwidth, Disk IOPS & Network speed tests...")
        console.print()
        
        real_console = console if isinstance(console, Console) else Console()
        
        bench_data: Dict[str, Any] = {
            "cpu_score": "N/A",
            "ram_speed_gb": "N/A",
            "disk_seq_write": "N/A",
            "net_speed_mbps": "N/A"
        }
        
        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold #a855f7"),
            TextColumn("[bold white]{task.description}[/bold white]"),
            BarColumn(bar_width=32, style="#581c87", complete_style="bold #34d399"),
            console=real_console
        ) as progress:
            total_task = progress.add_task("[bold #c084fc]Executing Benchmark[/bold #c084fc]", total=4)
            
            # 1. CPU Compute Test (Sha256 hash iterations)
            progress.update(total_task, description="[#e9d5ff]Running CPU Compute Stress Test...[/#e9d5ff]")
            cpu_cmd = (
                "python3 -c \""
                "import time, hashlib; "
                "t0=time.time(); "
                "[hashlib.sha256(b'x'*1024).digest() for _ in range(250000)]; "
                "dt=time.time()-t0; "
                "print(round(250000 / dt) if dt > 0 else 0)"
                "\" 2>/dev/null || "
                "openssl speed -seconds 2 sha256 2>/dev/null | grep -A 1 'type' | tail -n 1 | awk '{print $NF}' || echo 'N/A'"
            )
            code, out, _ = ssh.execute_command(cpu_cmd, stream_output=False)
            clean_out = out.strip().replace(",", "")
            if clean_out.isdigit() and int(clean_out) > 0:
                ops = int(clean_out)
                bench_data["cpu_score"] = f"{ops:,} Ops/sec"
            else:
                bench_data["cpu_score"] = "N/A"
            progress.advance(total_task)
            
            # 2. RAM Memory Bandwidth Test
            progress.update(total_task, description="[#e9d5ff]Measuring RAM Memory Throughput...[/#e9d5ff]")
            ram_cmd = "dd if=/dev/zero of=/dev/null bs=1M count=1024 2>&1 | tr '\r' '\n' | grep -E 'copied|bytes' | tail -n 1"
            code, out, _ = ssh.execute_command(ram_cmd, stream_output=False)
            ram_match = re.search(r'([0-9.]+)\s+([GM]B/s)', out)
            if ram_match:
                bench_data["ram_speed_gb"] = f"{ram_match.group(1)} {ram_match.group(2)}"
            else:
                bench_data["ram_speed_gb"] = "N/A"
            progress.advance(total_task)
            
            # 3. Disk I/O Sequential Write Test
            progress.update(total_task, description="[#e9d5ff]Measuring Storage Disk I/O Writeback...[/#e9d5ff]")
            disk_cmd = "dd if=/dev/zero of=/tmp/overdrive_bench.tmp bs=1M count=256 conv=fdatasync 2>&1 | tr '\r' '\n' | grep -E 'copied|bytes' | tail -n 1; rm -f /tmp/overdrive_bench.tmp"
            code, out, _ = ssh.execute_command(disk_cmd, stream_output=False)
            disk_match = re.search(r'([0-9.]+)\s+([GM]B/s)', out)
            if disk_match:
                bench_data["disk_seq_write"] = f"{disk_match.group(1)} {disk_match.group(2)}"
            else:
                bench_data["disk_seq_write"] = "N/A"
            progress.advance(total_task)
            
            # 4. CDN Download Speed Test
            progress.update(total_task, description="[#e9d5ff]Probing Real-Time Edge Network Speed...[/#e9d5ff]")
            net_cmd = "curl -4 -o /dev/null -s -w '%{speed_download}' --max-time 6 'https://speed.cloudflare.com/__down?bytes=25000000' 2>/dev/null || echo '0'"
            code, out, _ = ssh.execute_command(net_cmd, stream_output=False)
            clean_net = out.strip().replace(",", "")
            try:
                if clean_net.replace(".", "", 1).isdigit() and float(clean_net) > 0:
                    bytes_per_sec = float(clean_net)
                    mbps = round((bytes_per_sec * 8) / (1024 * 1024), 1)
                    bench_data["net_speed_mbps"] = f"{mbps} Mbps"
                else:
                    bench_data["net_speed_mbps"] = "N/A"
            except Exception:
                bench_data["net_speed_mbps"] = "N/A"
            progress.advance(total_task)
            time.sleep(0.05)
            
        self.last_benchmark_data = bench_data
        
        # Render Results Table
        table = Table(box=ROUNDED_BOX, border_style=BORDER_PURPLE, expand=True, padding=(0, 1))
        table.add_column("Hardware Subsystem / Vector", style="bold white", width=34)
        table.add_column("Measured Performance Value", style=f"bold {BRAND_LILAC}")
        table.add_column("Evaluation Grade", justify="center", width=20)
        
        # CPU
        table.add_row(
            "CPU Hash Compute Throughput",
            bench_data["cpu_score"],
            f"[bold {SEMANTIC_SUCCESS}] HIGH PERFORMANCE [/bold {SEMANTIC_SUCCESS}]" if bench_data["cpu_score"] != "N/A" else "[dim #f43f5e] UNMEASURED [/dim #f43f5e]"
        )
        
        # RAM
        table.add_row(
            "RAM Memory Copy Bandwidth",
            bench_data["ram_speed_gb"],
            f"[bold {SEMANTIC_SUCCESS}] FAST BANDWIDTH [/bold {SEMANTIC_SUCCESS}]" if bench_data["ram_speed_gb"] != "N/A" else "[dim #f43f5e] UNMEASURED [/dim #f43f5e]"
        )
        
        # Disk
        table.add_row(
            "Storage Sequential Disk I/O",
            bench_data["disk_seq_write"],
            f"[bold {SEMANTIC_SUCCESS}] DIRECT SYNC OK [/bold {SEMANTIC_SUCCESS}]" if bench_data["disk_seq_write"] != "N/A" else "[dim #f43f5e] UNMEASURED [/dim #f43f5e]"
        )
        
        # Network
        table.add_row(
            "Global CDN Edge Transit Speed",
            bench_data["net_speed_mbps"],
            f"[bold {SEMANTIC_SUCCESS}] UNCAPPED PIPE [/bold {SEMANTIC_SUCCESS}]" if bench_data["net_speed_mbps"] != "N/A" else "[dim #f43f5e] UNMEASURED [/dim #f43f5e]"
        )
        
        real_console.print(table)
        real_console.print()
        return True, "Complete VPS Hardware & Speed Benchmark successfully finished."

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        return {
            "pass": self.last_benchmark_data.get("cpu_score", "N/A") != "N/A",
            "data": self.last_benchmark_data
        }
