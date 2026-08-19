"""
OVERDRIVE - UI Components & Diagnostic Widgets
Specify-Inspired: Rounded borders, high-contrast inverted badges, and muted secondary data.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.theme import (
    BORDER_PURPLE,
    HEADER_BG,
    TEXT_LILAC,
    TEXT_LAVENDER,
    TEXT_MUTED,
    SEMANTIC_SUCCESS,
    SEMANTIC_ERROR,
    ROUNDED_BOX
)

console = Console(force_terminal=True)

def render_server_badge(ip: str, port: int, user: str, status: str = "CONNECTED"):
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")
    
    grid.add_row(
        f"[bold black on #c084fc] TARGET NODE [/bold black on #c084fc]  [bold white]{user}@{ip}:{port}[/bold white]",
        f"[dim #a1a1aa]STATUS:[/dim #a1a1aa] [bold black on #34d399] {status} [/bold black on #34d399]  [dim #a1a1aa]ED25519 Link[/dim #a1a1aa]"
    )
    
    return Panel(
        grid,
        box=ROUNDED_BOX,
        border_style=BORDER_PURPLE,
        title=f"[bold {TEXT_LILAC}] TELEMETRY BRIDGE ACTIVE [/bold {TEXT_LILAC}]",
        padding=(0, 1)
    )

def render_audit_table(audit_data: list):
    table = Table(
        title=f"\n[bold {TEXT_LILAC}] SYSTEM VERIFICATION AUDIT MATRIX [/bold {TEXT_LILAC}]\n",
        box=ROUNDED_BOX,
        border_style=BORDER_PURPLE,
        header_style=f"bold white on {HEADER_BG}",
        show_lines=False,
        padding=(0, 1)
    )
    
    table.add_column("Subsystem / Domain", style=f"bold {TEXT_LILAC}", width=26)
    table.add_column("Directive / Kernel Parameter", style=TEXT_MUTED, width=36)
    table.add_column("Live Verified State", style="bold white", width=32)
    table.add_column("Status", justify="center", width=12)
    
    for row in audit_data:
        is_pass = row.get("pass", True)
        if is_pass:
            status_badge = "[bold black on #34d399] PASS [/bold black on #34d399]"
        else:
            status_badge = "[bold white on #f43f5e] FAIL [/bold white on #f43f5e]"
        table.add_row(row["layer"], row["param"], str(row["value"]), status_badge)
        
    return table

def render_rollback_warning() -> Panel:
    """Renders a sleek, high-visibility warning panel for destructive/revert operations"""
    content = Table.grid(expand=True, padding=(0, 1))
    content.add_column(justify="left")
    
    content.add_row(
        f"[bold white on #ef4444] ⚠ CRITICAL SAFETY ADVISORY [/bold white on #ef4444]  "
        f"[bold #fbbf24]IRREVERSIBLE SYSTEM ACTION[/bold #fbbf24]\n"
    )
    content.add_row(
        f"[bold white]You are about to execute a full factory rollback on the remote server.[/bold white]"
    )
    content.add_row(
        f"[dim #a1a1aa]This operation will perform the following actions:[/dim #a1a1aa]"
    )
    content.add_row(
        f"  [dim #e9d5ff]•[/dim #e9d5ff] [bold #e9d5ff]Revert Kernel Sysctl[/bold #e9d5ff]: Delete /etc/sysctl.d/99-vps-optimization.conf and reload baseline sysctls"
    )
    content.add_row(
        f"  [dim #e9d5ff]•[/dim #e9d5ff] [bold #e9d5ff]Flush Netfilter Rules[/bold #e9d5ff]: Disable apply-mss-clamping.service and purge TCPMSS mangle tables"
    )
    content.add_row(
        f"  [dim #e9d5ff]•[/dim #e9d5ff] [bold #e9d5ff]Disable RPS/XPS Queues[/bold #e9d5ff]: Terminate set-rps.service and remove multi-core network steering scripts"
    )
    content.add_row(
        f"  [dim #e9d5ff]•[/dim #e9d5ff] [bold #e9d5ff]Restore Proxy Database[/bold #e9d5ff]: Recover /etc/x-ui/x-ui.db from the latest pre-flight backup snapshot\n"
    )
    content.add_row(
        f"[bold #f43f5e]⚠ WARNING:[/bold #f43f5e] [bold white]This action CANNOT be undone once completed.[/bold white] "
        f"[dim #a1a1aa]All current performance optimizations will be permanently stripped.[/dim #a1a1aa]"
    )
    
    return Panel(
        content,
        box=ROUNDED_BOX,
        border_style="#ef4444",
        title=f"[bold #f43f5e] ⚠ SYSTEM FACTORY ROLLBACK CONFIRMATION [/bold #f43f5e]",
        subtitle=f"[dim #a1a1aa]Press Enter or type 'N' to cancel safely[/dim #a1a1aa]",
        padding=(1, 2)
    )


