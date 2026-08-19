"""
OVERDRIVE - ANSI & TrueColor Gradient Colorizer Subsystem
Implements alignment-safe whitespace handling, multi-palette RGB linear interpolation,
and plain-text fallback for NO_COLOR.
"""

from __future__ import annotations
import os
import sys
from typing import List, Tuple, Sequence

from core.theme import PRESET_PALETTES

def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp_rgb(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        int(round(c1[0] + (c2[0] - c1[0]) * t)),
        int(round(c1[1] + (c2[1] - c1[1]) * t)),
        int(round(c1[2] + (c2[2] - c1[2]) * t))
    )

class AnsiColorizer:
    @staticmethod
    def is_no_color_enabled() -> bool:
        return bool(os.environ.get("NO_COLOR") or "--no-color" in sys.argv)

    @staticmethod
    def colorize_text(
        text: str,
        palette: str = "synthwave-purple",
        direction: str = "lr",
        mode: str = "gradient",
        keep_spaces: bool = False
    ) -> Tuple[str, str]:
        """
        Colorizes text alignment-safely and returns (coloredText, plainTextFallback)
        """
        lines = text.splitlines()
        plain_text = "\n".join(lines)
        
        if AnsiColorizer.is_no_color_enabled():
            return plain_text, plain_text
            
        palette_hex = PRESET_PALETTES.get(palette, PRESET_PALETTES["synthwave-purple"])
        palette_rgb = [hex_to_rgb(c) if isinstance(c, str) else (255, 255, 255) for c in palette_hex]
        
        reset = "\x1b[0m"
        max_len = max(len(l.rstrip("\n")) for l in lines) if lines else 1
        total_lines = len(lines)
        
        out_lines = []
        for y, raw in enumerate(lines):
            line = raw.rstrip("\n")
            out = []
            for x, ch in enumerate(line):
                if ch in " \t" and not keep_spaces:
                    out.append(ch)
                    continue
                    
                if direction == "tb":
                    t = 0.0 if total_lines <= 1 else y / (total_lines - 1)
                else:
                    t = 0.0 if max_len <= 1 else x / (max_len - 1)
                    
                t = max(0.0, min(1.0, t))
                
                if mode == "rainbow":
                    r_colors = PRESET_PALETTES["rainbow-256"]
                    idx = (x if direction == "lr" else y) % len(r_colors)
                    out.append(f"\x1b[38;5;{r_colors[idx]}m{ch}{reset}")
                else:
                    seg = t * (len(palette_rgb) - 1)
                    idx1 = int(seg)
                    idx2 = min(idx1 + 1, len(palette_rgb) - 1)
                    sub_t = seg - idx1
                    r, g, b = lerp_rgb(palette_rgb[idx1], palette_rgb[idx2], sub_t)
                    out.append(f"\x1b[38;2;{r};{g};{b}m{ch}{reset}")
                    
            out_lines.append("".join(out))
            
        colored_text = "\n".join(out_lines)
        return colored_text, plain_text
