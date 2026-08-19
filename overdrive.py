"""
OVERDRIVE - Enterprise Autonomous Linux Systems Optimization & Telemetry Platform
Specify CLI Aesthetic: High-contrast typography, unified master card, inverted label badges,
real-time Unicode sparkline charts, and zero-flicker Live in-place terminal updates.
"""

import sys
import os
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.box import ROUNDED

from core.logger import Logger
from core.ssh_client import SSHClientWrapper
from core.session_manager import SessionManager
from core.ascii_engine import AsciiMotion
from core.interactive_menu import InteractiveMenu
from core.system_detector import SystemDetector
from core.report_generator import ReportGenerator
from core.ui_components import render_rollback_warning
from core.updater import UpdateManager
from audits.system_auditor import SystemAuditor

from modules.overdrive_master import OverdriveMasterOptimizer
from modules.kernel_bbr import KernelBBROptimizer
from modules.carrier_mss import CarrierMSSOptimizer
from modules.multicore_rps import MultiCoreRPSOptimizer
from modules.memory_limits import MemoryLimitsOptimizer
from modules.storage_io import StorageIOOptimizer
from modules.dns_accelerator import DNSAcceleratorOptimizer
from modules.ssh_hardening import SSHHardenOptimizer
from modules.system_provisioning import SystemProvisioningOptimizer
from modules.grub_tuning import GRUBPerformanceOptimizer
from modules.xray_3xui import Xray3xuiOptimizer
from modules.vps_benchmark import VPSBenchmarkOptimizer
from modules.benchmark_module import BenchmarkModule
from modules.rollback_module import RollbackModule

from core.theme import (
    BORDER_PURPLE,
    TEXT_LILAC,
    TEXT_LAVENDER,
    HEADER_RULE,
    ROUNDED_BOX
)

console = Console(force_terminal=True)

def interactive_connect_wizard() -> SSHClientWrapper:
    """Prompt user for host, port, username, and authentication mode with multi-node bookmark switcher"""
    console.print()
    console.rule(f"[bold {TEXT_LILAC}] REMOTE NODE AUTHENTICATION [/bold {TEXT_LILAC}]", style=HEADER_RULE)
    console.print()
    
    saved_servers = SessionManager.get_all_servers()
    
    if saved_servers:
        console.print(SessionManager.render_server_selector(saved_servers))
        console.print()
        
        choice = console.input(f"  [bold black on #c084fc] CONNECT [/bold black on #c084fc] Select Bookmark [[1-{len(saved_servers)}]], [bold white]ENTER[/bold white] for [01], [[+]] New Node, [[D]] Delete: ").strip()
        
        if choice.lower() == 'd':
            del_idx_str = console.input(f"  [bold black on #f43f5e] DELETE [/bold black on #f43f5e] Enter index to delete [1-{len(saved_servers)}]: ").strip()
            if del_idx_str.isdigit():
                d_idx = int(del_idx_str) - 1
                if 0 <= d_idx < len(saved_servers):
                    SessionManager.delete_server(d_idx)
                    Logger.success("Server profile removed.")
            return interactive_connect_wizard()
            
        elif choice == "" or choice == "1":
            srv = saved_servers[0]
            host = srv.get("host")
            port = int(srv.get("port", 22))
            username = srv.get("username", "root")
            auth_type = srv.get("auth_type", "key")
            key_path = srv.get("key_path")
            
            console.print(SessionManager.render_session_card(srv))
            console.print()
            
            pwd = None
            if auth_type == "password":
                import getpass
                pwd = getpass.getpass("  Enter SSH Password: ")
                
            ssh = SSHClientWrapper(host=host, port=port, username=username, key_path=key_path, password=pwd)
            Logger.step("Authentication Link", f"Establishing encrypted session to {username}@{host}:{port}...")
            success, msg = ssh.connect()
            if success:
                Logger.success(f"Encrypted session established with {username}@{host}:{port}")
                time.sleep(0.6)
                return ssh
            else:
                Logger.error(f"Authentication failed: {msg}")
                return None
                
        elif choice.isdigit():
            c_idx = int(choice) - 1
            if 0 <= c_idx < len(saved_servers):
                srv = saved_servers[c_idx]
                host = srv.get("host")
                port = int(srv.get("port", 22))
                username = srv.get("username", "root")
                auth_type = srv.get("auth_type", "key")
                key_path = srv.get("key_path")
                
                console.print(SessionManager.render_session_card(srv))
                console.print()
                
                pwd = None
                if auth_type == "password":
                    import getpass
                    pwd = getpass.getpass("  Enter SSH Password: ")
                    
                ssh = SSHClientWrapper(host=host, port=port, username=username, key_path=key_path, password=pwd)
                Logger.step("Authentication Link", f"Establishing encrypted session to {username}@{host}:{port}...")
                success, msg = ssh.connect()
                if success:
                    Logger.success(f"Encrypted session established with {username}@{host}:{port}")
                    time.sleep(0.6)
                    return ssh
                else:
                    Logger.error(f"Authentication failed: {msg}")
                    return None
                    
    # Manual Node Setup Flow
    host = console.input(f"  [dim #a1a1aa]Enter Remote Target IPv4 / FQDN:[/dim #a1a1aa] [bold white]").strip()
    if not host:
        Logger.error("Target node host cannot be empty.")
        return None
        
    port_in = console.input(f"  [dim #a1a1aa]Enter SSH Port [default: 22]:[/dim #a1a1aa] [bold white]").strip()
    port = int(port_in) if port_in.isdigit() else 22
    
    user_in = console.input(f"  [dim #a1a1aa]Enter SSH Username [default: root]:[/dim #a1a1aa] [bold white]").strip()
    username = user_in if user_in else "root"
    
    label_in = console.input(f"  [dim #a1a1aa]Enter Bookmark Label [e.g. Frankfurt Core]:[/dim #a1a1aa] [bold white]").strip()
    label = label_in if label_in else f"Node-{len(saved_servers)+1}"
    
    local_keys = SSHClientWrapper.discover_local_keys()
    selected_key_path = None
    auth_type = "key"
    
    if local_keys:
        console.print(f"\n  [bold black on #c084fc] DETECTED KEYS [/bold black on #c084fc]  [white]Found {len(local_keys)} local private keys[/white]")
        for idx, k in enumerate(local_keys, 1):
            console.print(f"    [dim #a1a1aa][{idx}][/dim #a1a1aa] [bold #e9d5ff]{k}[/bold #e9d5ff]")
        console.print(f"    [dim #a1a1aa][P][/dim #a1a1aa] [white]Use Password Authentication[/white]")
        console.print(f"    [dim #a1a1aa][M][/dim #a1a1aa] [white]Enter Custom Private Key Path[/white]")
        
        k_choice = console.input(f"\n  [dim #a1a1aa]Select authentication method [default: 1]:[/dim #a1a1aa] ").strip()
        if k_choice.lower() == 'p':
            auth_type = "password"
        elif k_choice.lower() == 'm':
            selected_key_path = console.input(f"  [dim #a1a1aa]Enter full path to private key:[/dim #a1a1aa] ").strip()
        elif k_choice.isdigit() and 1 <= int(k_choice) <= len(local_keys):
            selected_key_path = local_keys[int(k_choice) - 1]
        else:
            selected_key_path = local_keys[0]
    else:
        auth_type = "password"
        
    pwd = None
    if auth_type == "password":
        import getpass
        pwd = getpass.getpass("  Enter SSH Password: ")
        
    ssh = SSHClientWrapper(host=host, port=port, username=username, key_path=selected_key_path, password=pwd)
    
    console.print()
    Logger.step("Authentication Link", f"Establishing encrypted session to {username}@{host}:{port}...")
    success, msg = ssh.connect()
    
    if not success:
        Logger.error(f"Authentication failed: {msg}")
        return None
        
    SessionManager.save_server(host, port, username, auth_type, selected_key_path, label=label)
    Logger.success(f"Encrypted session established with {username}@{host}:{port}")
    time.sleep(0.6)
    return ssh

def main():
    try:
        # 1. Play Neon-Purple Motion Animation
        AsciiMotion.play_boot_animation(duration=1.4)
        
        # 2. Check for latest version updates from GitHub
        UpdateManager.check_and_prompt(console)
        
        # 3. Connection Wizard
        ssh = interactive_connect_wizard()
        if not ssh:
            sys.exit(1)
            
        modules = {
            "1": OverdriveMasterOptimizer(),
            "2": KernelBBROptimizer(),
            "3": CarrierMSSOptimizer(),
            "4": MultiCoreRPSOptimizer(),
            "5": MemoryLimitsOptimizer(),
            "6": StorageIOOptimizer(),
            "7": DNSAcceleratorOptimizer(),
            "8": SSHHardenOptimizer(),
            "9": SystemProvisioningOptimizer(),
            "10": GRUBPerformanceOptimizer(),
            "11": Xray3xuiOptimizer(),
            "12": VPSBenchmarkOptimizer(),
            "13": BenchmarkModule(),
        }
        
        rollback_mod = RollbackModule()
        last_bench_results = None
        last_vps_bench = None
        
        # 3. Interactive Keyboard Navigation Loop with Live Telemetry
        while True:
            choice = InteractiveMenu.prompt_selection(ssh)
            
            if choice == "Q":
                os.system('cls' if os.name == 'nt' else 'clear')
                console.print(f"\n  [bold black on #c084fc] SESSION [/bold black on #c084fc]  [white]Terminating encrypted SSH connection...[/white]")
                ssh.close()
                Logger.success("Remote session safely terminated. All optimization parameters remain active.")
                break
                
            elif choice in ("A", "a"):
                os.system('cls' if os.name == 'nt' else 'clear')
                SystemAuditor.run_full_audit(ssh, console)
                console.input(f"\n  [dim #a1a1aa]Press Enter to return to main menu...[/dim #a1a1aa]")
                
            elif choice in ("R", "r"):
                os.system('cls' if os.name == 'nt' else 'clear')
                console.print()
                console.print(render_rollback_warning())
                console.print()
                
                confirm = console.input(f"  [bold #fbbf24]Type [bold white]'REVERT'[/bold white] or [bold white]'Y'[/bold white] to confirm rollback [or press Enter to cancel]: [/bold #fbbf24]").strip()
                if confirm.upper() in ("REVERT", "Y", "YES"):
                    console.print()
                    success, msg = rollback_mod.run(ssh, console)
                    if success:
                        Logger.success(msg)
                    else:
                        Logger.warn(msg)
                else:
                    console.print()
                    Logger.info("Rollback safely canceled. All system configurations remain active.")
                console.input(f"\n  [dim #a1a1aa]Press Enter to return to main menu...[/dim #a1a1aa]")
                
            elif choice in ("E", "e"):
                os.system('cls' if os.name == 'nt' else 'clear')
                console.print()
                console.rule(f"[bold {TEXT_LILAC}] EXPORT SYSTEM AUDIT & OPTIMIZATION REPORT [/bold {TEXT_LILAC}]", style=HEADER_RULE)
                console.print()
                
                Logger.step("Report Generation", "Collecting host topology, verification matrix & generating documentation...")
                topo = SystemDetector.detect_all(ssh)
                audit_res = SystemAuditor.run_full_audit(ssh, console)
                
                paths = ReportGenerator.export_audit_report(ssh.host, ssh.username, topo, audit_res, last_bench_results, last_vps_bench)
                console.print()
                Logger.success(f"Markdown Audit Report: [bold white]{paths['md_path']}[/bold white]")
                Logger.success(f"Monochrome Terminal HTML Report: [bold white]{paths['html_path']}[/bold white]")
                console.input(f"\n  [dim #a1a1aa]Press Enter to return to main menu...[/dim #a1a1aa]")
                
            elif choice in modules:
                mod = modules[choice]
                os.system('cls' if os.name == 'nt' else 'clear')
                console.print()
                console.rule(f"[bold {TEXT_LILAC}] EXECUTING OPTIMIZATION: {mod.name.upper()} [/bold {TEXT_LILAC}]", style=HEADER_RULE)
                console.print()
                
                try:
                    success, msg = mod.run(ssh, console)
                    if success:
                        Logger.success(msg)
                    else:
                        Logger.error(msg)
                        
                    if choice == "12":
                        last_vps_bench = getattr(mod, "last_benchmark_data", None)
                    elif choice == "13":
                        last_bench_results = getattr(mod, "last_results", None)
                        
                    console.print()
                    Logger.step("Verification Matrix", f"Validating live subsystem state for {mod.name}...")
                    v_res = mod.verify(ssh, console)
                    if v_res and v_res.get("pass", False):
                        Logger.success("Verification Passed: Subsystem configuration confirmed active.")
                    else:
                        Logger.warn("Verification Notice: Subsystem reported non-critical warnings.")
                except Exception as mod_err:
                    Logger.error(f"Execution failed on {mod.name}: {str(mod_err)}")
                    
                console.input(f"\n  [dim #a1a1aa]Press Enter to return to dashboard...[/dim #a1a1aa]")

    except KeyboardInterrupt:
        console.print(f"\n\n  [bold black on #fbbf24] ABORT [/bold black on #fbbf24] [white]Operation cancelled by user. Exiting OVERDRIVE...[/white]\n")
        sys.exit(0)
    except Exception as e:
        Logger.error(f"Fatal error encountered: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
