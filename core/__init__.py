"""
OVERDRIVE - Core Engine Package
"""

from .logger import console, Logger
from .ascii_engine import AsciiMotion
from .ansi_colorizer import AnsiColorizer
from .ssh_client import SSHClientWrapper
from .interactive_menu import InteractiveMenu
from .session_manager import SessionManager
from .system_detector import SystemDetector
from .telemetry import TelemetryData, TelemetryCollector
from .report_generator import ReportGenerator
from .ui_components import render_server_badge, render_audit_table
from .theme import (
    BRAND_PURPLE,
    BRAND_LAVENDER,
    BRAND_LILAC,
    BORDER_PURPLE,
    DIVIDER_PURPLE,
    HEADER_BG,
    BG_ACTIVE,
    TEXT_LILAC,
    TEXT_LAVENDER,
    TEXT_WHITE,
    TEXT_MUTED,
    TEXT_DIM,
    SEMANTIC_SUCCESS,
    SEMANTIC_WARN,
    SEMANTIC_ERROR,
    SEMANTIC_INFO,
    HEADER_RULE,
    ROUNDED_BOX,
    PRESET_PALETTES
)

from .updater import UpdateManager
from .version import __version__, __author__, __repository__

__all__ = [
    "__version__",
    "__author__",
    "__repository__",
    "UpdateManager",
    "console",
    "Logger",
    "AsciiMotion",
    "AnsiColorizer",
    "SSHClientWrapper",
    "InteractiveMenu",
    "SessionManager",
    "SystemDetector",
    "TelemetryData",
    "TelemetryCollector",
    "ReportGenerator",
    "render_server_badge",
    "render_audit_table",
    "BRAND_PURPLE",
    "BRAND_LAVENDER",
    "BRAND_LILAC",
    "BORDER_PURPLE",
    "DIVIDER_PURPLE",
    "HEADER_BG",
    "BG_ACTIVE",
    "TEXT_LILAC",
    "TEXT_LAVENDER",
    "TEXT_WHITE",
    "TEXT_MUTED",
    "TEXT_DIM",
    "SEMANTIC_SUCCESS",
    "SEMANTIC_WARN",
    "SEMANTIC_ERROR",
    "SEMANTIC_INFO",
    "HEADER_RULE",
    "ROUNDED_BOX",
    "PRESET_PALETTES"
]

