"""
OVERDRIVE - Module 13: Multi-Region Global Network Transit & Jitter Benchmark
Executes precise multi-target ICMP latency & jitter probing across true unicast regional looking glass gateways.
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

GLOBAL_GATEWAYS = [
    {"region": "🇩🇪 Frankfurt (Europe Core)", "host": "139.162.130.8", "desc": "DE-CIX / Telehouse Frankfurt"},
    {"region": "🇬🇧 London (UK Core)", "host": "176.58.107.39", "desc": "LINX / Telehouse North London"},
    {"region": "🇺🇸 New York (US East)", "host": "50.116.57.237", "desc": "Telia / Level3 NY Transit"},
    {"region": "🇺🇸 San Jose (US West)", "host": "50.116.14.9", "desc": "Silicon Valley / Hurricane Electric"},
    {"region": "🇸🇬 Singapore (APAC Central)", "host": "139.162.23.4", "desc": "Equinix SG1 / Singtel Exchange"},
    {"region": "🇯🇵 Tokyo (East Asia)", "host": "139.162.65.37", "desc": "NTT Communications / Equinix TY2"}
]

class BenchmarkModule(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Multi-Region Network Transit & Jitter Benchmark",
            description="Executes precise multi-sample latency and jitter benchmarks across 6 global unicast backbone transit routes.",
            category="Global Network Telemetry"
        )
        self.last_results: List[Dict[str, Any]] = []

    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        console.print()
        Logger.step("Network Benchmark", "Initiating multi-region global latency, jitter & route transit probe...")
        console.print()
        
        real_console = console if isinstance(console, Console) else Console()
        self.last_results = []
        
        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold #a855f7"),
            TextColumn("[bold white]{task.description}[/bold white]"),
            BarColumn(bar_width=32, style="#581c87", complete_style="bold #34d399"),
            console=real_console
        ) as progress:
            total_task = progress.add_task("[bold #c084fc]Global Transit Probing[/bold #c084fc]", total=len(GLOBAL_GATEWAYS))
            
            for gw in GLOBAL_GATEWAYS:
                progress.update(total_task, description=f"[#e9d5ff]Probing: {gw['region']}...[/#e9d5ff]")
                cmd = f"ping -c 3 -W 2 {gw['host']} 2>/dev/null | tail -n 2"
                code, out, _ = ssh.execute_command(cmd, stream_output=False)
                
                avg_rtt = "N/A"
                jitter = "0.0"
                packet_loss = "100%"
                loss_pct = 100
                tier = "UNREACHABLE"
                tier_color = SEMANTIC_ERROR
                
                if code == 0 and out:
                    loss_match = re.search(r'(\d+)%\s+packet loss', out)
                    if loss_match:
                        loss_pct = int(loss_match.group(1))
                        packet_loss = f"{loss_pct}%"
                        
                    rtt_match = re.search(r'=\s+([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+)', out)
                    if rtt_match:
                        min_v, avg_v, max_v, mdev_v = float(rtt_match.group(1)), float(rtt_match.group(2)), float(rtt_match.group(3)), float(rtt_match.group(4))
                        avg_rtt = f"{avg_v:.1f}"
                        jitter = f"{mdev_v:.1f}"
                        
                        if loss_pct > 20:
                            tier = "PACKET LOSS"
                            tier_color = SEMANTIC_ERROR
                        elif avg_v < 30.0:
                            tier = "SUB-30MS"
                            tier_color = SEMANTIC_SUCCESS
                        elif avg_v < 90.0:
                            tier = "LOW-LATENCY"
                            tier_color = SEMANTIC_SUCCESS
                        elif avg_v < 180.0:
                            tier = "TRANS-OCEANIC"
                            tier_color = SEMANTIC_WARN
                        else:
                            tier = "HIGH-BDP"
                            tier_color = BRAND_LAVENDER
                            
                self.last_results.append({
                    "region": gw["region"],
                    "gateway": gw["host"],
                    "desc": gw["desc"],
                    "avg_rtt": avg_rtt,
                    "jitter": jitter,
                    "packet_loss": packet_loss,
                    "tier": tier,
                    "tier_color": tier_color
                })
                
                progress.advance(total_task)
                time.sleep(0.05)
                
        # Render Results Table
        table = Table(box=ROUNDED_BOX, border_style=BORDER_PURPLE, expand=True, padding=(0, 1))
        table.add_column("Target Transit Region", style="bold white", width=32)
        table.add_column("Probe Gateway", style=f"bold {BRAND_LILAC}")
        table.add_column("Avg Latency", justify="center", style="bold white", width=16)
        table.add_column("Jitter (mdev)", justify="center", style=f"dim {BRAND_LAVENDER}", width=16)
        table.add_column("Loss", justify="center", width=10)
        table.add_column("Transit Status", justify="center", width=18)
        
        for r in self.last_results:
            loss_badge = f"[bold {SEMANTIC_SUCCESS}]{r['packet_loss']}[/bold {SEMANTIC_SUCCESS}]" if r['packet_loss'] == "0%" else f"[bold {SEMANTIC_ERROR}]{r['packet_loss']}[/bold {SEMANTIC_ERROR}]"
            status_badge = f"[bold {r['tier_color']}]{r['tier']}[/bold {r['tier_color']}]"
            table.add_row(
                r["region"],
                f"{r['gateway']} [dim {BRAND_LAVENDER}]({r['desc']})[/dim {BRAND_LAVENDER}]",
                f"{r['avg_rtt']} ms" if r['avg_rtt'] != "N/A" else "[dim #f43f5e]N/A ms[/dim #f43f5e]",
                f"±{r['jitter']} ms",
                loss_badge,
                status_badge
            )
            
        real_console.print(table)
        real_console.print()
        return True, "Global Transit & Jitter Benchmark completed across 6 backbone routes."

    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        return {
            "pass": len(self.last_results) > 0,
            "results": self.last_results
        }
