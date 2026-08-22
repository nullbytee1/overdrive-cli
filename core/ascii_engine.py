"""
OVERDRIVE - Neon-Purple Gradient Motion Engine
Mathematical ASCII Banner centering, dynamic terminal cell-width calculation,
and smooth wave-cycle animation.
"""

import os
import sys
import time
import math
import re
import shutil
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.panel import Panel
from rich.box import ROUNDED
from rich.cells import cell_len

from core.version import __version__

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True)

# Neon-Purple Gradient Palette
PURPLE_PALETTE = [
    "#3b0764",  # Deep Plum
    "#581c87",  # Royal Violet
    "#7e22ce",  # Neon Violet
    "#a855f7",  # Electric Purple
    "#c084fc",  # Glowing Lavender
    "#e9d5ff",  # Soft Lilac
]

BORDER_PURPLE = "#6d28d9"
TEXT_LILAC = "#e9d5ff"
TEXT_LAVENDER = "#c084fc"
TEXT_MUTED = "#a1a1aa"

BANNER_BOX_INNER_WIDTH = 76
BANNER_HEADER_TITLE = "OVERDRIVE // PERFORMANCE PLATFORM"

OVERDRIVE_BANNER = [
    r"  ██████╗ ██╗   ██╗███████╗██████╗ ██████╗ ██████╗ ██╗██╗   ██╗███████╗",
    r" ██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║██║   ██║██╔════╝",
    r" ██║   ██║██║   ██║█████╗  ██████╔╝██║  ██║██████╔╝██║██║   ██║█████╗  ",
    r" ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝  ",
    r" ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║██████╔╝██║  ██║██║ ╚████╔╝ ███████╗",
    r"  ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝"
]

_ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def strip_ansi(text: str) -> str:
    """Strips ANSI escape sequences from a string before measuring."""
    return _ANSI_ESCAPE_RE.sub('', text)

def get_display_cell_width(text: str) -> int:
    """Calculates true terminal display-cell width of text without ANSI sequences."""
    return cell_len(strip_ansi(text))

class AsciiMotion:
    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def generate_gradient_text(lines, color_gradient, offset=0, wave=False):
        """Applies a vertical and horizontal chromatic gradient across text lines"""
        result = Text()
        num_lines = len(lines)
        num_colors = len(color_gradient)
        
        for row_idx, line in enumerate(lines):
            line_text = Text()
            for col_idx, char in enumerate(line):
                if char in " ░":
                    line_text.append(char)
                    continue
                
                if wave:
                    wave_val = math.sin((col_idx * 0.14) + offset + (row_idx * 0.5))
                    color_idx = int(((wave_val + 1) / 2) * (num_colors - 1))
                else:
                    color_idx = int((row_idx / max(1, num_lines - 1)) * (num_colors - 1))
                
                color_idx = max(0, min(num_colors - 1, color_idx))
                color = color_gradient[color_idx]
                
                line_text.append(char, style=f"bold {color}")
                    
            result.append(line_text)
            if row_idx < num_lines - 1:
                result.append("\n")
        return result

    @staticmethod
    def render_centered_banner_frame(offset: float = 0.0, wave: bool = False, optical_offset: int = 0) -> Text:
        """
        Constructs the entire banner box with the large ASCII logo mathematically centered
        against the exact inner width of the surrounding box using terminal display-cell widths.
        """
        inner_width = BANNER_BOX_INNER_WIDTH
        
        # 1. Measure and center top title
        title_w = get_display_cell_width(BANNER_HEADER_TITLE)
        left_title_pad = max(0, (inner_width - title_w) // 2)
        right_title_pad = max(0, inner_width - title_w - left_title_pad)
        
        # 2. Measure artwork lines using terminal display-cell width (stripping ANSI)
        max_artwork_w = max(get_display_cell_width(line) for line in OVERDRIVE_BANNER)
        
        # 3. Calculate exact left padding to mathematically center artwork in inner box
        artwork_left_pad = max(0, ((inner_width - max_artwork_w) // 2) + optical_offset)
        
        # 4. Apply left padding to each artwork line
        padded_lines = [(" " * artwork_left_pad) + line for line in OVERDRIVE_BANNER]
        banner_text = AsciiMotion.generate_gradient_text(padded_lines, PURPLE_PALETTE, offset=offset, wave=wave)
        
        # 5. Assemble composite banner box
        frame_box = Text()
        frame_box.append("╭" + "─" * inner_width + "╮\n", style=f"{BORDER_PURPLE}")
        frame_box.append("│" + " " * left_title_pad + BANNER_HEADER_TITLE + " " * right_title_pad + "│\n", style="bold #c084fc")
        frame_box.append(banner_text)
        frame_box.append("\n╰" + "─" * inner_width + "╯", style=f"{BORDER_PURPLE}")
        
        return frame_box

    @staticmethod
    def play_boot_animation(duration: float = 1.4):
        """Plays a smooth wave-cycle gradient intro animation with rounded container"""
        frames = 12
        delay = duration / frames
        
        boot_stages = [
            "Initializing Linux Kernel BBR & High-BDP TCP Buffers...",
            "Synchronizing Universal 1360 MSS Network MTU Profiles...",
            "Balancing Multi-Core RPS/XPS Queue Routing Steers...",
            "Stabilizing Process Memory Bounds & Go Runtime Heap...",
            "Production Environment Ready • Telemetry Engine Active."
        ]
        
        for frame in range(frames):
            AsciiMotion.clear()
            term_w = max(80, shutil.get_terminal_size((80, 24)).columns)
            offset = (frame / frames) * math.pi * 2
            
            frame_box = AsciiMotion.render_centered_banner_frame(offset=offset, wave=True)
            console.print(Align.center(frame_box, width=term_w))
            
            # Subtitle pulse (shared center axis)
            stage_idx = min(frame // 3, len(boot_stages) - 1)
            stage_text = boot_stages[stage_idx]
            console.print(Align.center(f"[bold black on #a855f7] BOOT [/bold black on #a855f7] [white]{stage_text}[/white]\n", width=term_w))
            time.sleep(delay)
            
        AsciiMotion.clear()
        
        # Final static presentation (shared center axis)
        term_w = max(80, shutil.get_terminal_size((80, 24)).columns)
        frame_box = AsciiMotion.render_centered_banner_frame(wave=False)
        
        console.print(Align.center(frame_box, width=term_w))
        console.print(Align.center(f"[bold #c084fc]OVERDRIVE[/bold #c084fc] [dim #71717a]•[/dim #71717a] [white]Enterprise Linux Telemetry & Network Optimization[/white] [dim #a1a1aa][v{__version__}][/dim #a1a1aa]", width=term_w))
        console.print(Align.center("[dim #a1a1aa]Universal Cloud • Bare-Metal • Low-Latency Real-Time Telemetry Pipeline[/dim #a1a1aa]\n", width=term_w))

    @staticmethod
    def show_spinner_step(message: str, duration: float = 0.8):
        """Displays a modern snake-dots loading spinner with neon-purple gradient"""
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        end_time = time.time() + duration
        idx = 0
        while time.time() < end_time:
            c = chars[idx % len(chars)]
            sys.stdout.write(f"\r  \033[38;2;168;85;247m{c}\033[0m \033[38;2;233;213;255m{message}\033[0m")
            sys.stdout.flush()
            time.sleep(0.06)
            idx += 1
        sys.stdout.write(f"\r  \033[1;30;48;2;52;211;153m READY \033[0m \033[1;37m{message}\033[0m \033[38;2;192;132;252m\033[0m\n")
        sys.stdout.flush()

