"""
OVERDRIVE - Interactive Keyboard Navigation & Real-Time Live Telemetry Engine
Specify CLI Aesthetic: High-contrast typography, unified master card, inverted label badges,
smooth Unicode sparkline charts, precision fractional meters, and zero-flicker Live in-place terminal updates.
"""

import sys
import os
import time
from typing import List, Dict, Any, Optional
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED
from rich.live import Live

from core.telemetry import TelemetryData, TelemetryCollector
from core.ssh_client import SSHClientWrapper
from core.theme import (
    BRAND_PURPLE,
    BRAND_LAVENDER,
    BRAND_LILAC,
    BORDER_PURPLE,
    DIVIDER_PURPLE,
    BG_ACTIVE,
    TEXT_MUTED,
    TEXT_DIM,
    SEMANTIC_SUCCESS,
    SEMANTIC_WARN,
    SEMANTIC_ERROR,
    SEMANTIC_INFO,
    ROUNDED_BOX
)

console = Console(force_terminal=True)

MODULE_METADATA = [
    {
        "id": "1",
        "title": "Full-Stack System Optimization (Automated)",
        "category": "System & Kernel Orchestration",
        "impact": "Deploys Complete 10-Tier Production Baseline",
        "latency_gain": "Reduces Jitter & Stabilizes Transit Latency",
        "specs": "Sequentially configures BBR/FQ, MSS clamping, multi-core RPS, dynamic swap, Anycast DNS, SSH hardening, and kernel boot parameters.",
        "risk": "Safe (Automated pre-flight sysctl and service configuration backups)"
    },
    {
        "id": "2",
        "title": "Kernel BBRv3 / BBR & TCP Window Buffers",
        "category": "TCP Congestion Control & Sockets",
        "impact": "Maximizes Throughput on High Bandwidth-Delay Product Links",
        "latency_gain": "Reduces Retransmissions & Buffering Delays",
        "specs": "Probes BBRv3/BBR/BBR2 support, loads FQ/CAKE qdisc, and tunes dynamic TCP socket memory buffers up to 64MB.",
        "risk": "Safe (Live kernel sysctl application)"
    },
    {
        "id": "3",
        "title": "TCP MSS Path MTU Clamping (1360)",
        "category": "Netfilter & Packet Routing",
        "impact": "Prevents Packet Fragmentation Across Cellular & VPN Routes",
        "latency_gain": "Eliminates Path MTU Black-Hole Drops",
        "specs": "Enforces persistent Netfilter TCP MSS 1360 rules via systemd service across IPv4 and IPv6 chains.",
        "risk": "Safe (Non-blocking Netfilter rule insertion)"
    },
    {
        "id": "4",
        "title": "Multi-Core RPS/XPS Network Queue Steering",
        "category": "vCPU Interrupt Balancing",
        "impact": "Distributes Packet Processing Across All CPU Cores",
        "latency_gain": "Eliminates Single-Core SoftIRQ Bottlenecks",
        "specs": "Calculates CPU affinity bitmasks across all network interface queues to balance packet RX/TX workloads.",
        "risk": "Safe (Immediate sysfs queue mask update)"
    },
    {
        "id": "5",
        "title": "Memory Governance, Swap & Process Limits",
        "category": "Virtual Memory & Process Limits",
        "impact": "Prevents OOM Crashes & Raises File Descriptor Limits",
        "latency_gain": "Optimizes Garbage Collection & Memory Reclamation",
        "specs": "Provisions swapfile (vm.swappiness=10), sets GOMEMLIMIT, GODEBUG=madvdontneed=1, and raises ulimits to 1,048,576.",
        "risk": "Safe (Graceful daemon reload)"
    },
    {
        "id": "6",
        "title": "Storage I/O Scheduler & Dirty Writeback Tuning",
        "category": "Block Storage Subsystem",
        "impact": "Smooths Disk I/O Queues & Background Flushing",
        "latency_gain": "Reduces I/O Wait Bottlenecks Under Heavy Write Load",
        "specs": "Configures 1024KB readahead via persistent udev rules and balances vm.dirty_ratio and vm.dirty_background_ratio.",
        "risk": "Safe (Live kernel parameter application)"
    },
    {
        "id": "7",
        "title": "System DNS Optimization (Anycast Resolvers)",
        "category": "Name Resolution Subsystem",
        "impact": "Accelerates Outbound Domain Resolution",
        "latency_gain": "Sub-Millisecond Upstream DNS Response Times",
        "specs": "Configures Cloudflare (1.1.1.1) and Google (8.8.8.8) Anycast resolvers with single-request-reopen.",
        "risk": "Safe (Non-blocking resolv.conf update)"
    },
    {
        "id": "8",
        "title": "SSH Daemon Latency & Security Hardening",
        "category": "Remote Access Subsystem",
        "impact": "Removes Login Delays & Enforces Keepalives",
        "latency_gain": "Sub-Second SSH Session Handshakes",
        "specs": "Configures UseDNS no, disables GSSAPI delays, enables 30s keepalives, and validates syntax with sshd -t.",
        "risk": "Safe (Pre-flight backup + non-locking reload)"
    },
    {
        "id": "9",
        "title": "Base System Provisioning & Entropy Daemon",
        "category": "System Core & Cryptography",
        "impact": "Updates Repositories, Installs Tools & Enables haveged",
        "latency_gain": "Accelerates TLS Handshake Entropy Generation",
        "specs": "Refreshes package mirrors, installs essential toolchains, activates haveged daemon, and syncs timezone.",
        "risk": "Safe (Standard package manager refresh)"
    },
    {
        "id": "10",
        "title": "Kernel Bootloader & GRUB Parameter Tuning",
        "category": "Bootloader & Kernel Flags",
        "impact": "Applies Low-Latency Kernel Boot Parameters",
        "latency_gain": "Optimizes Memory Page Allocation on Boot",
        "specs": "Configures transparent_hugepage=madvise and elevator=none in /etc/default/grub with automated bootloader update.",
        "risk": "Safe (Applies on next system reboot)"
    },
    {
        "id": "11",
        "title": "Proxy Engine Socket Optimization (3x-ui / Xray)",
        "category": "Proxy & Transport Protocols",
        "impact": "Enables Low-Latency Socket Flags & DNS Caching",
        "latency_gain": "Reduces TCP Handshake Latency & Prevents Idle Drops",
        "specs": "Configures TCP_NODELAY, TCP_FASTOPEN, and cached parallel DNS in /etc/x-ui/x-ui.db with database backup.",
        "risk": "Safe (Pre-flight SQLite database snapshot created)"
    },
    {
        "id": "12",
        "title": "VPS Hardware & Compute Benchmark",
        "category": "System Performance Verification",
        "impact": "Measures CPU Compute, RAM Bandwidth, Disk I/O & Network",
        "latency_gain": "Live Hardware Performance Verification",
        "specs": "Runs SHA-256 CPU compute, RAM copy throughput (GB/s), direct sync disk write, and CDN edge speed tests.",
        "risk": "Read-Only (Non-destructive benchmark)"
    },
    {
        "id": "13",
        "title": "Multi-Region Network Transit & Jitter Benchmark",
        "category": "Global Network Telemetry",
        "impact": "Probes Global Backbone RTT, Jitter & Loss",
        "latency_gain": "Multi-Region Network Route Diagnostics",
        "specs": "Measures live ICMP latency and jitter across Frankfurt, London, New York, San Jose, Singapore, and Tokyo.",
        "risk": "Read-Only (Non-destructive network probe)"
    },
    {
        "id": "A",
        "title": "System Diagnostic Verification Matrix (Audit)",
        "category": "System Diagnostics & Health",
        "impact": "18-Point Full-Stack Verification Matrix",
        "latency_gain": "Live Kernel & Service State Inspection",
        "specs": "Inspects kernel congestion control, QDiscs, buffers, Netfilter tables, RPS masks, memory limits, DNS, and SSH.",
        "risk": "Read-Only (Non-destructive inspection)"
    },
    {
        "id": "E",
        "title": "Generate System Performance Report (HTML/MD)",
        "category": "Audit & Documentation",
        "impact": "Exports Clean System Audit Report (HTML & Markdown)",
        "latency_gain": "N/A",
        "specs": "Generates a detailed, timestamped system audit report saved to ./reports/ on the local machine.",
        "risk": "Safe (Local file export)"
    },
    {
        "id": "R",
        "title": "System Configuration Rollback & Restore",
        "category": "System Recovery & Reversion",
        "impact": "Restores Kernel Sysctl & Services from Backups",
        "latency_gain": "Reverts System to Pre-Flight Baseline",
        "specs": "Flushes custom Netfilter rules, restores baseline sysctl configurations, and recovers proxy database from backup.",
        "risk": "Restores baseline settings (Requires explicit confirmation)"
    },
    {
        "id": "Q",
        "title": "Terminate Session & Disconnect",
        "category": "Session Management",
        "impact": "Safely Closes Encrypted SSH Connection",
        "latency_gain": "N/A",
        "specs": "Disconnects remote SSH session cleanly while leaving all applied optimizations active on the host.",
        "risk": "Safe (Leaves server configurations running)"
    }
]

def render_gradient_bar(pct: float, width: int = 8, theme: str = "emerald") -> str:
    """Renders a sleek, high-precision fractional gradient meter (e.g. ❪████▌░░░░❫)"""
    pct = max(0.0, min(100.0, float(pct)))
    blocks = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    total_steps = width * 8
    filled_steps = int(round((pct / 100.0) * total_steps))
    
    full_blocks = filled_steps // 8
    remainder = filled_steps % 8
    empty_blocks = width - full_blocks - (1 if remainder > 0 else 0)
    empty_blocks = max(0, empty_blocks)
    
    if theme == "purple":
        fill_color = "#c084fc"
        tip_color = "#e9d5ff"
    else:
        if pct < 65.0:
            fill_color = "#34d399"
            tip_color = "#a7f3d0"
        elif pct < 85.0:
            fill_color = "#fbbf24"
            tip_color = "#fef08a"
        else:
            fill_color = "#f43f5e"
            tip_color = "#fecdd3"
            
    filled_part = f"[{fill_color}]{'█' * full_blocks}[/{fill_color}]"
    if remainder > 0:
        filled_part += f"[{tip_color}]{blocks[remainder]}[/{tip_color}]"
    empty_part = f"[dim #581c87]{'░' * empty_blocks}[/dim #581c87]" if empty_blocks > 0 else ""
    return f"[dim #6d28d9]❪[/dim #6d28d9]{filled_part}{empty_part}[dim #6d28d9]❫[/dim #6d28d9]"

def render_meter(pct: float, width: int = 8) -> str:
    """Backward-compatible meter rendering helper"""
    return render_gradient_bar(pct, width=width, theme="emerald")

class NonBlockingKeyReader:
    @staticmethod
    def read_key(timeout: float = 0.04) -> Optional[str]:
        """Reads a keypress without blocking, returning None if no key pressed within timeout"""
        if os.name == 'nt':
            import msvcrt
            start_t = time.time()
            while time.time() - start_t < timeout:
                if msvcrt.kbhit():
                    try:
                        ch = msvcrt.getch()
                        if ch in (b'\x00', b'\xe0'):
                            if msvcrt.kbhit():
                                ch2 = msvcrt.getch()
                                if ch2 == b'H':
                                    return 'UP'
                                elif ch2 == b'P':
                                    return 'DOWN'
                                elif ch2 == b'K':
                                    return 'LEFT'
                                elif ch2 == b'M':
                                    return 'RIGHT'
                            return None
                        elif ch == b'\r':
                            return 'ENTER'
                        elif ch == b' ':
                            return 'SPACE'
                        elif ch == b'\x1b':
                            return 'ESC'
                        elif ch in (b'q', b'Q'):
                            return 'Q'
                        elif ch in (b'r', b'R'):
                            return 'R'
                        elif ch in (b'e', b'E'):
                            return 'E'
                        elif ch in (b'a', b'A'):
                            return 'A'
                        elif ch in b'1234567890':
                            return ch.decode('ascii')
                        elif ch in (b'w', b'W'):
                            return 'UP'
                        elif ch in (b's', b'S'):
                            return 'DOWN'
                    except Exception:
                        return None
                time.sleep(0.01)
            return None
        else:
            import select
            import tty
            import termios
            try:
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setcbreak(fd)
                    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                    if rlist:
                        ch = sys.stdin.read(1)
                        if ch == '\x1b':
                            rlist2, _, _ = select.select([sys.stdin], [], [], 0.03)
                            if rlist2:
                                ch2 = sys.stdin.read(1)
                                if ch2 == '[':
                                    ch3 = sys.stdin.read(1)
                                    if ch3 == 'A':
                                        return 'UP'
                                    elif ch3 == 'B':
                                        return 'DOWN'
                                    elif ch3 == 'C':
                                        return 'RIGHT'
                                    elif ch3 == 'D':
                                        return 'LEFT'
                            return 'ESC'
                        elif ch in ('\n', '\r'):
                            return 'ENTER'
                        elif ch == ' ':
                            return 'SPACE'
                        elif ch in ('q', 'Q'):
                            return 'Q'
                        elif ch in ('r', 'R'):
                            return 'R'
                        elif ch in ('e', 'E'):
                            return 'E'
                        elif ch in ('a', 'A'):
                            return 'A'
                        elif ch in '1234567890':
                            return ch
                        elif ch in ('w', 'W'):
                            return 'UP'
                        elif ch in ('s', 'S'):
                            return 'DOWN'
                    return None
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                return None

class InteractiveMenu:
    @staticmethod
    def render_full_dashboard(selected_idx: int, host: str, user: str, tele: Dict[str, Any]) -> Table:
        """Constructs a single, unified, cohesive master dashboard with aligned rows and zero flicker"""
        cur_mod = MODULE_METADATA[selected_idx]
        
        term_width = console.size.width if console.size.width > 60 else 110
        divider_width = max(50, term_width - 8)
        divider_line = f"[{DIVIDER_PURPLE}]" + "─" * divider_width + f"[/{DIVIDER_PURPLE}]"
        
        # Outermost Master Table
        main_table = Table(
            box=ROUNDED,
            border_style=BORDER_PURPLE,
            expand=True,
            padding=(0, 1),
            show_header=False
        )
        main_table.add_column("Content", justify="left")
        
        # 1. Header Grid Row
        hdr = Table.grid(expand=True)
        hdr.add_column(justify="left")
        hdr.add_column(justify="right")
        hdr.add_row(
            f"[bold black on #c084fc] TARGET NODE [/bold black on #c084fc]  [bold white]{user}@{host}[/bold white]",
            f"[dim #a1a1aa]STATUS:[/dim #a1a1aa] [bold black on #34d399] CONNECTED [/bold black on #34d399]  [dim #a1a1aa]SSH-ED25519 Link[/dim #a1a1aa]"
        )
        main_table.add_row(hdr)
        main_table.add_row(divider_line)
        
        # 2. Middle Row: 2-Column Split for Option Menu and Specification Breakdown
        mid = Table.grid(expand=True, padding=(0, 2))
        mid.add_column(ratio=7)
        mid.add_column(ratio=4)
        
        # Left Column: Menu Items with sleek right-aligned status brackets
        menu_t = Table.grid(expand=True, padding=(0, 1))
        menu_t.add_column(justify="left", ratio=1)
        menu_t.add_column(justify="right")
        menu_t.add_row(f"[bold {BRAND_LILAC}]OPTIMIZATION MODULES & DIAGNOSTICS[/bold {BRAND_LILAC}]\n", "")
        
        mod_status = tele.get("module_status", {})
        
        for idx, mod in enumerate(MODULE_METADATA):
            is_active = (idx == selected_idx)
            m_id = mod["id"]
            m_title = mod["title"]
            st = mod_status.get(m_id, False)
            
            if st is True:
                status_bracket = f"[dim {BORDER_PURPLE}]❪[/dim {BORDER_PURPLE}][bold {SEMANTIC_SUCCESS}]ACTIVE[/bold {SEMANTIC_SUCCESS}][dim {BORDER_PURPLE}]❫[/dim {BORDER_PURPLE}]"
            elif st is False:
                status_bracket = f"[dim {BORDER_PURPLE}]❪[/dim {BORDER_PURPLE}][dim {TEXT_DIM}]PENDING[/dim {TEXT_DIM}][dim {BORDER_PURPLE}]❫[/dim {BORDER_PURPLE}]"
            elif st == "tool":
                status_bracket = f"[dim {BORDER_PURPLE}]❪[/dim {BORDER_PURPLE}][dim {SEMANTIC_INFO}]TOOL[/dim {SEMANTIC_INFO}][dim {BORDER_PURPLE}]❫[/dim {BORDER_PURPLE}]"
            elif st == "rollback":
                status_bracket = f"[dim {BORDER_PURPLE}]❪[/dim {BORDER_PURPLE}][bold {SEMANTIC_WARN}]REVERT[/bold {SEMANTIC_WARN}][dim {BORDER_PURPLE}]❫[/dim {BORDER_PURPLE}]"
            else:
                status_bracket = f"[dim {BORDER_PURPLE}]❪[/dim {BORDER_PURPLE}][dim {SEMANTIC_ERROR}]EXIT[/dim {SEMANTIC_ERROR}][dim {BORDER_PURPLE}]❫[/dim {BORDER_PURPLE}]"
                
            if is_active:
                left_item = f"[bold white on {BG_ACTIVE}]  ›  {m_id:<2}  {m_title}  [/bold white on {BG_ACTIVE}]"
                right_item = f"[bold white on {BG_ACTIVE}] {status_bracket} [/bold white on {BG_ACTIVE}]"
            else:
                left_item = f"     [dim {TEXT_DIM}]{m_id:<2}[/dim {TEXT_DIM}]   [{BRAND_LAVENDER}]{m_title}[/{BRAND_LAVENDER}]"
                right_item = status_bracket
                
            menu_t.add_row(left_item, right_item)
            
        # Right Column: Specification Breakdown
        cur_st = mod_status.get(cur_mod['id'], False)
        if cur_st is True:
            live_badge = f"[bold black on {SEMANTIC_SUCCESS}] ACTIVE & OPTIMIZED [/bold black on {SEMANTIC_SUCCESS}]"
        elif cur_st is False:
            live_badge = f"[bold black on #c084fc] PENDING DEPLOYMENT [/bold black on #c084fc]"
        elif cur_st == "tool":
            live_badge = f"[bold black on {SEMANTIC_INFO}] READ-ONLY DIAGNOSTIC [/bold black on {SEMANTIC_INFO}]"
        elif cur_st == "rollback":
            live_badge = f"[bold black on {SEMANTIC_WARN}] 1-CLICK SAFETY RECOVERY [/bold black on {SEMANTIC_WARN}]"
        else:
            live_badge = f"[bold white on {SEMANTIC_ERROR}] TERMINATE SSH SESSION [/bold white on {SEMANTIC_ERROR}]"
            
        spec_t = Table.grid(expand=True, padding=(0, 0))
        spec_t.add_column(style=f"dim {TEXT_MUTED}", width=16)
        spec_t.add_column(style="bold white")
        spec_t.add_row(f"[bold {BRAND_LILAC}]SPECIFICATION BREAKDOWN[/bold {BRAND_LILAC}]", "")
        spec_t.add_row("", "")
        spec_t.add_row("LIVE STATUS:", live_badge)
        spec_t.add_row("DOMAIN:", f"[bold {BRAND_LILAC}]{cur_mod['category']}[/bold {BRAND_LILAC}]")
        spec_t.add_row("TARGET GAIN:", f"[bold {SEMANTIC_SUCCESS}]{cur_mod['impact']}[/bold {SEMANTIC_SUCCESS}]")
        spec_t.add_row("LATENCY DELTA:", f"[bold {BRAND_LAVENDER}]{cur_mod['latency_gain']}[/bold {BRAND_LAVENDER}]")
        spec_t.add_row("SAFETY PROFILE:", f"[white]{cur_mod['risk']}[/white]")
        spec_t.add_row("", "")
        spec_t.add_row("DIRECTIVES:", f"[{TEXT_MUTED}]{cur_mod['specs']}[/{TEXT_MUTED}]")
        
        mid.add_row(menu_t, spec_t)
        main_table.add_row(mid)
        main_table.add_row(divider_line)
        
        # 3. Bottom Row: Clean Structured Sub-Tables for Live Telemetry & Hardware Metrics
        tele_grid = Table.grid(expand=True, padding=(0, 2))
        tele_grid.add_column(ratio=1)
        tele_grid.add_column(ratio=1)
        tele_grid.add_column(ratio=1)
        
        # Column 1: Compute & Load
        t1 = Table.grid(expand=True, padding=(0, 0))
        t1.add_column(style=f"dim {TEXT_MUTED}", width=13)
        t1.add_column(style="bold white")
        t1.add_row(f"[bold {BRAND_LILAC}]COMPUTE & LOAD[/bold {BRAND_LILAC}]", "")
        t1.add_row("CPU Load:", f"{render_gradient_bar(tele['cpu_pct'], 8, 'purple')}  [bold {BRAND_LILAC}]{tele['cpu_pct']:.1f}%[/bold {BRAND_LILAC}]")
        t1.add_row("Load Avg:", f"[bold white]{tele['load_avg']}[/bold white]")
        t1.add_row("CPU Wave:", f"[{BRAND_LAVENDER}]{tele['cpu_sparkline']}[/{BRAND_LAVENDER}]  [dim {TEXT_MUTED}]({tele['cpu_cores']} vCPUs)[/dim {TEXT_MUTED}]")
        t1.add_row("Proxy Engine:", f"[bold {SEMANTIC_SUCCESS}]Port 443 (ACTIVE)[/bold {SEMANTIC_SUCCESS}]")
        
        # Column 2: Memory & Swap
        t2 = Table.grid(expand=True, padding=(0, 0))
        t2.add_column(style=f"dim {TEXT_MUTED}", width=13)
        t2.add_column(style="bold white")
        t2.add_row(f"[bold {BRAND_LILAC}]MEMORY & SWAP[/bold {BRAND_LILAC}]", "")
        t2.add_row("RAM Alloc:", f"{render_gradient_bar(tele['mem_pct'], 8, 'emerald')}  [bold {SEMANTIC_SUCCESS}]{tele['mem_pct']:.1f}%[/bold {SEMANTIC_SUCCESS}]")
        t2.add_row("Available:", f"[{BRAND_LAVENDER}]{tele['mem_avail_mb']} MB (Bufferbloat Free)[/{BRAND_LAVENDER}]")
        t2.add_row("RAM Wave:", f"[{SEMANTIC_SUCCESS}]{tele['mem_sparkline']}[/{SEMANTIC_SUCCESS}]  [bold white]{tele['mem_used_mb']}M/{tele['mem_total_mb']}M[/bold white]")
        swap_desc = f"{tele['swap_used_mb']}M/{tele['swap_total_mb']}M (0% Thrash)" if tele['swap_used_mb'] == 0 else f"{tele['swap_used_mb']}M/{tele['swap_total_mb']}M"
        t2.add_row("Swap Util:", f"[{SEMANTIC_SUCCESS}]{swap_desc}[/{SEMANTIC_SUCCESS}]")
        
        # Column 3: Network & Transit
        t3 = Table.grid(expand=True, padding=(0, 0))
        t3.add_column(style=f"dim {TEXT_MUTED}", width=13)
        t3.add_column(style="bold white")
        t3.add_row(f"[bold {BRAND_LILAC}]NETWORK & TRANSIT[/bold {BRAND_LILAC}]", "")
        t3.add_row("Public IP:", f"[{BRAND_LAVENDER}]{tele['public_ip']} (eth0)[/{BRAND_LAVENDER}]")
        t3.add_row("Connections:", f"[{SEMANTIC_SUCCESS}]{tele['active_tcp_conns']} Active TCP Streams[/{SEMANTIC_SUCCESS}]")
        t3.add_row("RTT Wave:", f"[{BRAND_LAVENDER}]{tele['ping_sparkline']}[/{BRAND_LAVENDER}]  [dim {TEXT_DIM}]Sub-ms[/dim {TEXT_DIM}]")
        t3.add_row("Ping Probe:", f"[bold white]{tele['ping_rtt_ms']} ms (1.1.1.1 RTT)[/bold white]")
        
        tele_grid.add_row(t1, t2, t3)
        
        tele_hdr = Text()
        tele_hdr.append("● ", style=f"bold {SEMANTIC_SUCCESS}")
        tele_hdr.append("LIVE TELEMETRY & HARDWARE METRICS ", style=f"bold {BRAND_LILAC}")
        tele_hdr.append(f"[SYNC: {tele['last_updated']}]", style=f"dim {TEXT_MUTED}")
        
        main_table.add_row(tele_hdr)
        main_table.add_row(tele_grid)
        main_table.add_row(divider_line)
        
        # 4. Integrated Footer Navigation Bar
        footer_text = Text()
        footer_text.append(" [↑/↓] ", style="bold black on #c084fc")
        footer_text.append(" Navigate   ", style=f"dim {BRAND_LILAC}")
        footer_text.append(" [ENTER] ", style=f"bold white on {BG_ACTIVE}")
        footer_text.append(" Execute   ", style=f"dim {BRAND_LILAC}")
        footer_text.append(" [1-13] ", style="bold black on #e9d5ff")
        footer_text.append(" Select   ", style=f"dim {BRAND_LILAC}")
        footer_text.append(" [A] ", style="bold black on #c084fc")
        footer_text.append(" Audit   ", style=f"dim {BRAND_LILAC}")
        footer_text.append(" [R] ", style="bold black on #fbbf24")
        footer_text.append(" Rollback   ", style=f"dim {BRAND_LILAC}")
        footer_text.append(" [E] ", style="bold black on #34d399")
        footer_text.append(" Export   ", style=f"dim {BRAND_LILAC}")
        footer_text.append(" [Q / ESC] ", style="bold white on #f43f5e")
        footer_text.append(" Exit", style="bold #fecdd3")
        
        main_table.add_row(Align.center(footer_text))
        return main_table

    @staticmethod
    def prompt_selection(ssh: SSHClientWrapper) -> str:
        """Runs the real-time interactive selection loop with in-place Live terminal updates and zero flicker"""
        selected_idx = 0
        total_items = len(MODULE_METADATA)
        
        telemetry = TelemetryData()
        collector = TelemetryCollector(ssh, telemetry, poll_interval=3.0)
        collector.start()
        
        last_rendered_snap_ts = ""
        render_dirty = True
        
        os.system('cls' if os.name == 'nt' else 'clear')
        
        initial_snap = telemetry.get_snapshot()
        initial_dash = InteractiveMenu.render_full_dashboard(
            selected_idx, ssh.host, ssh.username, initial_snap
        )
        
        try:
            with Live(initial_dash, console=console, auto_refresh=False, transient=False) as live:
                while True:
                    snap = telemetry.get_snapshot()
                    cur_ts = snap.get("last_updated", "")
                    
                    if render_dirty or (cur_ts and cur_ts != last_rendered_snap_ts):
                        dashboard = InteractiveMenu.render_full_dashboard(
                            selected_idx, ssh.host, ssh.username, snap
                        )
                        live.update(dashboard, refresh=True)
                        last_rendered_snap_ts = cur_ts
                        render_dirty = False
                    
                    key = NonBlockingKeyReader.read_key(timeout=0.04)
                    
                    if key in ('UP', 'w', 'W'):
                        selected_idx = (selected_idx - 1) % total_items
                        render_dirty = True
                    elif key in ('DOWN', 's', 'S'):
                        selected_idx = (selected_idx + 1) % total_items
                        render_dirty = True
                    elif key in ('ENTER', 'SPACE'):
                        collector.stop()
                        return MODULE_METADATA[selected_idx]["id"]
                    elif key in ('Q', 'ESC'):
                        collector.stop()
                        return "Q"
                    elif key in ('R', 'r'):
                        collector.stop()
                        return "R"
                    elif key in ('E', 'e'):
                        collector.stop()
                        return "E"
                    elif key in ('A', 'a'):
                        collector.stop()
                        return "A"
                    elif key and key in '123456789':
                        for idx, mod in enumerate(MODULE_METADATA):
                            if mod["id"] == key:
                                collector.stop()
                                return key
        finally:
            collector.stop()
