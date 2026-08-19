"""
OVERDRIVE - Core Logger Subsystem (Specify-Inspired Neon-Purple & Pastel Aesthetic)
Designed for high-contrast legibility, eye comfort, and professional systems feedback.
"""
import sys
import os
from datetime import datetime

# Enforce UTF-8 on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.theme import Theme

# Theme matching the modern Neon-Purple gradient & pastel semantic palette
custom_theme = Theme({
    "info": "#a78bfa",
    "warning": "#fbbf24",
    "error": "#f43f5e",
    "success": "#34d399",
    "highlight": "#c084fc",
    "purple": "#a855f7",
    "lavender": "#c084fc",
    "lilac": "#e9d5ff",
    "muted": "#a1a1aa",
    "dim": "#71717a"
})

console = Console(theme=custom_theme, force_terminal=True)

class Logger:
    @staticmethod
    def _timestamp() -> str:
        return f"[dim #71717a]{datetime.now().strftime('%H:%M:%S')}[/dim #71717a]"

    @staticmethod
    def info(msg: str):
        console.print(f"{Logger._timestamp()} [bold black on #c084fc] INFO [/bold black on #c084fc] [white]{msg}[/white]")

    @staticmethod
    def success(msg: str):
        console.print(f"{Logger._timestamp()} [bold black on #34d399] DONE [/bold black on #34d399] [bold white]{msg}[/bold white]")

    @staticmethod
    def warn(msg: str):
        console.print(f"{Logger._timestamp()} [bold black on #fbbf24] WARN [/bold black on #fbbf24] [#fef08a]{msg}[/#fef08a]")

    @staticmethod
    def error(msg: str):
        console.print(f"{Logger._timestamp()} [bold white on #f43f5e] FAIL [/bold white on #f43f5e] [#fecdd3]{msg}[/#fecdd3]")

    @staticmethod
    def step(step_name: str, detail: str = ""):
        detail_str = f" [dim #a1a1aa]{detail}[/dim #a1a1aa]" if detail else ""
        console.print(f"{Logger._timestamp()} [bold black on #a855f7] STEP [/bold black on #a855f7] [bold #e9d5ff]{step_name}[/bold #e9d5ff]{detail_str}")

    @staticmethod
    def header(title: str):
        console.print()
        console.rule(f"[bold #e9d5ff] {title.upper()} [/bold #e9d5ff]", style="#581c87")
        console.print()

