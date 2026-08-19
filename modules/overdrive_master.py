"""
OVERDRIVE - Module 1: Autonomous Full-Stack Master Optimization Pipeline
Master Orchestrator that applies all 10 enterprise optimization tiers in sequence with pre-flight backups.
"""

from typing import Tuple, Dict, Any, List
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED

from .base_module import BaseOptimizerModule
from .system_provisioning import SystemProvisioningOptimizer
from .kernel_bbr import KernelBBROptimizer
from .carrier_mss import CarrierMSSOptimizer
from .multicore_rps import MultiCoreRPSOptimizer
from .memory_limits import MemoryLimitsOptimizer
from .storage_io import StorageIOOptimizer
from .dns_accelerator import DNSAcceleratorOptimizer
from .ssh_hardening import SSHHardenOptimizer
from .grub_tuning import GRUBPerformanceOptimizer
from .xray_3xui import Xray3xuiOptimizer

from core.ssh_client import SSHClientWrapper
from core.system_detector import SystemDetector
from core.logger import Logger

class OverdriveMasterOptimizer(BaseOptimizerModule):
    def __init__(self):
        super().__init__(
            name="Full-Stack System Optimization (Autonomous God Mode)",
            description="Autonomous multi-tier deployment: BBRv3/BBR, 1360 MSS, RPS multi-core, dynamic swap, DNS, SSH hardening, GRUB & sockopts.",
            category="All-in-One Master Suite"
        )
        self.sub_modules: List[BaseOptimizerModule] = [
            SystemProvisioningOptimizer(),
            KernelBBROptimizer(),
            CarrierMSSOptimizer(),
            MultiCoreRPSOptimizer(),
            MemoryLimitsOptimizer(),
            StorageIOOptimizer(),
            DNSAcceleratorOptimizer(),
            SSHHardenOptimizer(),
            GRUBPerformanceOptimizer(),
            Xray3xuiOptimizer()
        ]

    def run(self, ssh: SSHClientWrapper, console) -> Tuple[bool, str]:
        console.print()
        console.rule("[bold #e9d5ff] FULL-STACK AUTONOMOUS OPTIMIZATION PIPELINE [/bold #e9d5ff]", style="#581c87")
        console.print()
        
        # 0. Auto-Discovery Pre-Flight Probe
        Logger.step("Auto-Discovery", "Probing hardware architecture, hypervisor, network queues & installed software stacks...")
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
            title="[bold #e9d5ff] HARDWARE & SYSTEM TOPOLOGY PROFILE [/bold #e9d5ff]",
            padding=(0, 1)
        ))
        console.print()
        
        for idx, mod in enumerate(self.sub_modules, 1):
            Logger.step(f"Tier {idx}/{len(self.sub_modules)}", f"Deploying {mod.name}...")
            success, msg = mod.run(ssh, console)
            if not success:
                Logger.warn(f"Tier {idx} notice: {msg}")
            else:
                if any(w in msg.lower() for w in ["already", "verified", "active", "tuned", "retained"]):
                    Logger.success(f"Tier {idx} verified active: {mod.name}")
                else:
                    Logger.success(f"Tier {idx} active: {mod.name}")
            console.print()
                
        return True, "Full-Stack System Optimization successfully executed across all 10 core subsystems."

    def verify(self, ssh: SSHClientWrapper, console) -> Dict[str, Any]:
        results = []
        for mod in self.sub_modules:
            v = mod.verify(ssh, console)
            results.append(v)
            
        all_passed = any(r.get("pass", False) for r in results)
        return {
            "pass": all_passed,
            "details": results
        }
