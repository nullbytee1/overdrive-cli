"""
OVERDRIVE - Multi-Node Server Bookmarks & Session Manager
Stores, manages, and restores multiple remote server connection profiles with 1-click selection,
custom node labels, and Specify CLI aesthetic presentation.
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED

CONFIG_DIR = os.path.expanduser("~/.overdrive")
SERVERS_FILE = os.path.join(CONFIG_DIR, "servers.json")

# Styling Tokens
BRAND_PURPLE = "#a855f7"
BRAND_LAVENDER = "#c084fc"
BRAND_LILAC = "#e9d5ff"
BORDER_PURPLE = "#6d28d9"
DIVIDER_PURPLE = "#581c87"
TEXT_MUTED = "#a1a1aa"
TEXT_DIM = "#71717a"
SEMANTIC_SUCCESS = "#34d399"
SEMANTIC_WARN = "#fbbf24"

class SessionManager:
    @staticmethod
    def get_all_servers() -> List[Dict[str, Any]]:
        """Retrieves all saved server bookmark profiles ordered by most recently active"""
        try:
            if not os.path.exists(SERVERS_FILE):
                return []
            with open(SERVERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                # Sort by last_connected descending
                return sorted(data, key=lambda s: s.get("last_connected", ""), reverse=True)
        except Exception:
            return []
        return []

    @staticmethod
    def get_last_server() -> Optional[Dict[str, Any]]:
        """Retrieves the single most recently active server profile"""
        servers = SessionManager.get_all_servers()
        return servers[0] if servers else None

    # Backward compatibility alias
    get_last_session = get_last_server

    @staticmethod
    def save_server(host: str, port: int, username: str, auth_type: str, key_path: Optional[str] = None, label: Optional[str] = None) -> bool:
        """Saves or updates a server connection profile in ~/.overdrive/servers.json"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            servers = SessionManager.get_all_servers()
            
            # Find if server already exists by host:port:user
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = False
            for s in servers:
                if s.get("host") == host and s.get("port") == port and s.get("username") == username:
                    s["auth_type"] = auth_type
                    s["key_path"] = key_path
                    s["last_connected"] = now_str
                    if label:
                        s["label"] = label
                    found = True
                    break
                    
            if not found:
                node_label = label or f"Node-{len(servers) + 1} ({host})"
                servers.insert(0, {
                    "label": node_label,
                    "host": host,
                    "port": port,
                    "username": username,
                    "auth_type": auth_type,
                    "key_path": key_path,
                    "last_connected": now_str
                })
                
            # Limit stored profiles to 20
            servers = servers[:20]
            with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                json.dump(servers, f, indent=2)
            return True
        except Exception:
            return False

    # Backward compatibility alias
    save_session = save_server

    @staticmethod
    def delete_server(index: int) -> bool:
        """Deletes a saved server bookmark by index (0-based)"""
        try:
            servers = SessionManager.get_all_servers()
            if 0 <= index < len(servers):
                servers.pop(index)
                with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(servers, f, indent=2)
                return True
        except Exception:
            return False
        return False

    @staticmethod
    def render_server_selector(servers: List[Dict[str, Any]]) -> Panel:
        """Renders an interactive multi-node server profile table"""
        table = Table(box=None, expand=True, padding=(0, 1), show_header=True)
        table.add_column("#", justify="center", style="bold #c084fc", width=4)
        table.add_column("Node Alias / Label", style="bold white", width=22)
        table.add_column("Target Endpoint", style=f"bold {BRAND_LILAC}")
        table.add_column("Auth Scheme", style=f"bold {SEMANTIC_SUCCESS}", width=18)
        table.add_column("Last Sync", style=f"dim {TEXT_MUTED}", width=20)
        
        for idx, s in enumerate(servers, 1):
            auth_desc = "SSH Key Link" if s.get("auth_type") == "key" else "Password"
            label = s.get("label") or f"Node-{idx}"
            endpoint = f"{s.get('username', 'root')}@{s.get('host')}:{s.get('port', 22)}"
            last_conn = s.get("last_connected", "Recent")
            
            badge = f"[bold black on #c084fc] {idx} [/bold black on #c084fc]"
            table.add_row(badge, label, endpoint, auth_desc, last_conn)
            
        return Panel(
            table,
            box=ROUNDED,
            border_style=BORDER_PURPLE,
            title=f"[bold {BRAND_LILAC}] SAVED SERVER BOOKMARKS & PROFILES [/bold {BRAND_LILAC}]",
            padding=(0, 1)
        )

    @staticmethod
    def render_session_card(session: Dict[str, Any]) -> Panel:
        """Renders a sleek single-server profile summary card"""
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(style="dim #a1a1aa", width=16)
        grid.add_column(style="bold white")
        grid.add_column(style="dim #a1a1aa", width=16)
        grid.add_column(style="bold white")

        auth_desc = "SSH Key Discovery" if session.get("auth_type") == "key" else "Password Authentication"
        key_desc = session.get("key_path") or "Encrypted Stream"
        if len(key_desc) > 36:
            key_desc = "..." + key_desc[-33:]

        grid.add_row(
            "TARGET NODE:",
            f"[bold #e9d5ff]{session.get('username')}@{session.get('host')}:{session.get('port', 22)}[/bold #e9d5ff]",
            "AUTH SCHEME:",
            f"[bold {SEMANTIC_SUCCESS}]{auth_desc}[/bold {SEMANTIC_SUCCESS}]"
        )
        grid.add_row(
            "CREDENTIAL:",
            f"[bold {BRAND_LAVENDER}]{key_desc}[/bold {BRAND_LAVENDER}]",
            "LAST ACTIVE:",
            f"[dim #a1a1aa]{session.get('last_connected', 'Recent')}[/dim #a1a1aa]"
        )

        return Panel(
            grid,
            box=ROUNDED,
            border_style=BORDER_PURPLE,
            title=f"[bold {BRAND_LILAC}] PREVIOUS CONNECTION PROFILE DETECTED [/bold {BRAND_LILAC}]",
            padding=(0, 1)
        )
