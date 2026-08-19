"""
OVERDRIVE - Automated Release & Update Manager
Checks GitHub releases for new versions, prompts the user on startup,
and executes seamless in-place updates via Git or direct download.
"""

import os
import sys
import json
import subprocess
import urllib.request
from typing import Tuple, Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.version import __version__, __repository__
from core.theme import (
    BRAND_PURPLE,
    BRAND_LAVENDER,
    BRAND_LILAC,
    BORDER_PURPLE,
    SEMANTIC_SUCCESS,
    SEMANTIC_WARN,
    ROUNDED_BOX
)

GITHUB_API_LATEST = "https://api.github.com/repos/nullbytee1/overdrive-cli/releases/latest"
GITHUB_RAW_VERSION = "https://raw.githubusercontent.com/nullbytee1/overdrive-cli/main/core/version.py"

class UpdateManager:
    @staticmethod
    def parse_version_tuple(v_str: str) -> Tuple[int, ...]:
        """Parses a version string like 'v1.2.3' or '1.2.0' into an integer tuple (1, 2, 3)"""
        clean = v_str.strip().lstrip("v").lstrip("V")
        # Extract digits from version segments
        parts = []
        for p in clean.split("."):
            digits = "".join(c for c in p if c.isdigit())
            parts.append(int(digits) if digits else 0)
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)

    @staticmethod
    def is_newer_version(current: str, latest: str) -> bool:
        """Returns True if latest version is strictly greater than current version"""
        try:
            return UpdateManager.parse_version_tuple(latest) > UpdateManager.parse_version_tuple(current)
        except Exception:
            return False

    @staticmethod
    def check_for_update(timeout: float = 2.5) -> Tuple[bool, str, str]:
        """
        Queries GitHub API for the latest release.
        Returns: (update_available: bool, latest_version: str, release_notes: str)
        """
        try:
            req = urllib.request.Request(
                GITHUB_API_LATEST,
                headers={
                    "User-Agent": "OVERDRIVE-UpdateChecker",
                    "Accept": "application/vnd.github+json"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                tag_name = data.get("tag_name", "").strip().lstrip("v")
                body = data.get("body", "Performance improvements and bug fixes.")
                if tag_name and UpdateManager.is_newer_version(__version__, tag_name):
                    return True, tag_name, body
        except Exception:
            # Fallback to checking raw version.py
            try:
                raw_req = urllib.request.Request(
                    GITHUB_RAW_VERSION,
                    headers={"User-Agent": "OVERDRIVE-UpdateChecker"}
                )
                with urllib.request.urlopen(raw_req, timeout=timeout) as resp:
                    content = resp.read().decode("utf-8")
                    for line in content.splitlines():
                        if "__version__" in line and "=" in line:
                            raw_v = line.split("=")[1].strip().strip('"').strip("'").lstrip("v")
                            if raw_v and UpdateManager.is_newer_version(__version__, raw_v):
                                return True, raw_v, "Latest updates from main branch."
            except Exception:
                pass
                
        return False, __version__, ""

    @staticmethod
    def render_update_modal(latest_v: str, notes: str) -> Panel:
        """Renders a sleek Specify-inspired Update Available modal"""
        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(justify="left")
        
        grid.add_row(
            f"[bold black on {SEMANTIC_SUCCESS}] UPDATE AVAILABLE [/bold black on {SEMANTIC_SUCCESS}]  "
            f"[bold {BRAND_LILAC}]OVERDRIVE v{latest_v} is ready for installation[/bold {BRAND_LILAC}]\n"
        )
        
        info_t = Table.grid(expand=True, padding=(0, 2))
        info_t.add_column(style=f"dim {BRAND_LAVENDER}", width=18)
        info_t.add_column(style="bold white")
        
        info_t.add_row("Current Version:", f"v{__version__}")
        info_t.add_row("Latest Release:", f"[bold {SEMANTIC_SUCCESS}]v{latest_v}[/bold {SEMANTIC_SUCCESS}]")
        info_t.add_row("Repository:", f"[dim]{__repository__}[/dim]\n")
        grid.add_row(info_t)
        
        if notes:
            # Clean first 3 lines of release notes
            clean_lines = [l for l in notes.splitlines() if l.strip() and not l.startswith("#")][:3]
            if clean_lines:
                grid.add_row(f"[dim {BRAND_LAVENDER}]Release Highlights:[/dim {BRAND_LAVENDER}]")
                for cl in clean_lines:
                    grid.add_row(f"  [dim #a855f7]•[/dim #a855f7] [white]{cl.strip()}[/white]")
                grid.add_row("")
                
        grid.add_row(f"[dim #a1a1aa]Would you like to install this update now? Automatically updates in-place.[/dim #a1a1aa]")
        
        return Panel(
            grid,
            box=ROUNDED_BOX,
            border_style=BORDER_PURPLE,
            title=f"[bold {BRAND_LILAC}] 🚀 OVERDRIVE SYSTEM UPDATE [/bold {BRAND_LILAC}]",
            padding=(1, 2)
        )

    @staticmethod
    def apply_update(console: Console) -> bool:
        """Applies the update via git pull and reinstall dependencies"""
        console.print(f"\n  [bold black on {BRAND_LAVENDER}] UPDATING [/bold black on {BRAND_LAVENDER}] [white]Pulling latest changes from GitHub repository...[/white]")
        
        # 1. Check if git is available in project root
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_dir = os.path.join(app_dir, ".git")
        
        if os.path.exists(git_dir):
            try:
                res = subprocess.run(["git", "pull", "origin", "main"], cwd=app_dir, capture_output=True, text=True, timeout=15)
                if res.returncode == 0:
                    console.print(f"  [bold {SEMANTIC_SUCCESS}]✔[/bold {SEMANTIC_SUCCESS}] [white]Codebase updated successfully.[/white]")
                    # Update requirements
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"], cwd=app_dir, timeout=20)
                    console.print(f"  [bold black on {SEMANTIC_SUCCESS}] SUCCESS [/bold black on {SEMANTIC_SUCCESS}] [bold white]OVERDRIVE has been updated to the latest release![/bold white]\n")
                    return True
                else:
                    console.print(f"  [dim #f43f5e]Git pull notice: {res.stderr.strip()}[/dim #f43f5e]")
            except Exception as e:
                console.print(f"  [dim #f43f5e]Update error: {e}[/dim #f43f5e]")
                
        console.print(f"  [dim #a1a1aa]Manual update: run [bold white]git pull[/bold white] or re-run the install script.[/dim #a1a1aa]\n")
        return False

    @staticmethod
    def check_and_prompt(console: Console) -> bool:
        """
        Startup update check hook.
        If an update is found and user chooses to update, applies it and returns True (should restart/exit).
        Otherwise returns False (continue normal boot).
        """
        has_update, latest_v, notes = UpdateManager.check_for_update(timeout=2.0)
        if not has_update:
            return False
            
        console.print()
        console.print(UpdateManager.render_update_modal(latest_v, notes))
        console.print()
        
        try:
            choice = console.input(f"  [bold {BRAND_LAVENDER}]Install update v{latest_v} now? [Y/n]: [/bold {BRAND_LAVENDER}]").strip().lower()
            if choice in ("", "y", "yes"):
                success = UpdateManager.apply_update(console)
                if success:
                    console.input(f"  [dim #a1a1aa]Press Enter to restart OVERDRIVE...[/dim #a1a1aa]")
                    # Restart current script
                    try:
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    except Exception:
                        sys.exit(0)
                else:
                    console.input(f"  [dim #a1a1aa]Press Enter to continue with current version...[/dim #a1a1aa]")
            else:
                console.print(f"  [dim #a1a1aa]Update deferred. Continuing to OVERDRIVE...[/dim #a1a1aa]\n")
        except (KeyboardInterrupt, EOFError):
            pass
            
        return False
