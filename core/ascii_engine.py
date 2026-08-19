"""
OVERDRIVE - Neon-Purple Gradient Motion Engine
Specify CLI Aesthetic: High contrast, eye-comforting gradients, zero cyan artifacts,
and smooth UTF-8 snake-dots animations.
"""

import os
import sys
import time
import math
import shutil
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.panel import Panel
from rich.box import ROUNDED

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

OVERDRIVE_BANNER = [
    r"  ██████╗ ██╗   ██╗███████╗██████╗ ██████╗ ██████╗ ██╗██╗   ██╗███████╗",
    r" ██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║██║   ██║██╔════╝",
    r" ██║   ██║██║   ██║█████╗  ██████╔╝██║  ██║██████╔╝██║██║   ██║█████╗  ",
    r" ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝  ",
    r" ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║██████╔╝██║  ██║██║ ╚████╔╝ ███████╗",
    r"  ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝"
]

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
            
            banner = AsciiMotion.generate_gradient_text(OVERDRIVE_BANNER, PURPLE_PALETTE, offset=offset, wave=True)
            
            frame_box = Text()
            frame_box.append("╭" + "─"*76 + "╮\n", style=f"{BORDER_PURPLE}")
            frame_box.append("│" + " "*22 + "OVERDRIVE // PERFORMANCE PLATFORM" + " "*21 + "│\n", style="bold #c084fc")
            frame_box.append(banner)
            frame_box.append("\n╰" + "─"*76 + "╯", style=f"{BORDER_PURPLE}")
            
            console.print(Align.center(frame_box, width=term_w))
            
            # Subtitle pulse
            stage_idx = min(frame // 3, len(boot_stages) - 1)
            stage_text = boot_stages[stage_idx]
            console.print(Align.center(f"[bold black on #a855f7] BOOT [/bold black on #a855f7] [white]{stage_text}[/white]\n", width=term_w))
            time.sleep(delay)
            
        AsciiMotion.clear()
        
        # Final static presentation
        term_w = max(80, shutil.get_terminal_size((80, 24)).columns)
        banner = AsciiMotion.generate_gradient_text(OVERDRIVE_BANNER, PURPLE_PALETTE, wave=False)
        frame_box = Text()
        frame_box.append("╭" + "─"*76 + "╮\n", style=f"{BORDER_PURPLE}")
        frame_box.append("│" + " "*22 + "OVERDRIVE // PERFORMANCE PLATFORM" + " "*21 + "│\n", style="bold #c084fc")
        frame_box.append(banner)
        frame_box.append("\n╰" + "─"*76 + "╯", style=f"{BORDER_PURPLE}")
        
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

