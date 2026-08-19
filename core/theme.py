"""
OVERDRIVE - Central Design System & Theme Tokens
Specify CLI Guidelines: Neon-purple & pastel palette, high-contrast inverted badges,
consistent semantic indicators, and unified rounded card styling.
"""

from rich.box import ROUNDED

# Brand Identity & Pastel Palette Tokens
BRAND_PURPLE = "#a855f7"
BRAND_LAVENDER = "#c084fc"
BRAND_LILAC = "#e9d5ff"
BORDER_PURPLE = "#6d28d9"
DIVIDER_PURPLE = "#581c87"
HEADER_BG = "#3b0764"
BG_ACTIVE = "#581c87"

# Typography & Text Dimming Tokens
TEXT_LILAC = "#e9d5ff"
TEXT_LAVENDER = "#c084fc"
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#a1a1aa"
TEXT_DIM = "#71717a"

# Semantic Status Tokens
SEMANTIC_SUCCESS = "#34d399"
SEMANTIC_WARN = "#fbbf24"
SEMANTIC_ERROR = "#f43f5e"
SEMANTIC_INFO = "#818cf8"

# UI Element Styles
HEADER_RULE = "#6d28d9"
ROUNDED_BOX = ROUNDED

# TrueColor & ANSI 256 Gradient Palettes
PRESET_PALETTES = {
    "neon-purple-gradient": ["#3b0764", "#581c87", "#7e22ce", "#a855f7", "#c084fc", "#e9d5ff"],
    "lavender-glow": ["#581c87", "#7c3aed", "#a78bfa", "#c4b5fd", "#ede9fe"],
    "deep-violet-pastel": ["#2e1065", "#4c1d95", "#6d28d9", "#8b5cf6", "#ddd6fe"],
    "emerald-accent": ["#064e3b", "#047857", "#10b981", "#34d399", "#a7f3d0"],
    "synthwave-purple": ["#3b0764", "#581c87", "#7e22ce", "#a855f7", "#c084fc", "#e9d5ff"],
    "rainbow-256": [196, 202, 208, 214, 220, 46, 51, 39, 27, 93, 129]
}
