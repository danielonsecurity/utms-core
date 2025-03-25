import re

from .colors import ColorFormatter


def ansi_to_html(text: str) -> str:
    """Convert ANSI color codes to HTML span elements with appropriate classes."""

    # ANSI color to CSS class mapping
    color_map = {
        # Reset
        "\033[0m": "</span>",
        # Foreground colors
        "\033[30m": '<span class="ansi-black">',  # Black
        "\033[31m": '<span class="ansi-red">',  # Red
        "\033[32m": '<span class="ansi-green">',  # Green
        "\033[33m": '<span class="ansi-yellow">',  # Yellow
        "\033[34m": '<span class="ansi-blue">',  # Blue
        "\033[35m": '<span class="ansi-magenta">',  # Magenta
        "\033[36m": '<span class="ansi-cyan">',  # Cyan
        "\033[37m": '<span class="ansi-white">',  # White
        # Background colors
        "\033[40m": '<span class="ansi-bg-black">',  # Black Background
        "\033[41m": '<span class="ansi-bg-red">',  # Red Background
        "\033[42m": '<span class="ansi-bg-green">',  # Green Background
        "\033[43m": '<span class="ansi-bg-yellow">',  # Yellow Background
        "\033[44m": '<span class="ansi-bg-blue">',  # Blue Background
        "\033[45m": '<span class="ansi-bg-magenta">',  # Magenta Background
        "\033[46m": '<span class="ansi-bg-cyan">',  # Cyan Background
        "\033[47m": '<span class="ansi-bg-white">',  # White Background
        # Styles
        "\033[1m": '<span class="ansi-bright">',  # Bright
        "\033[2m": '<span class="ansi-dim">',  # Dim
        "\033[22m": '<span class="ansi-normal">',  # Normal
    }

    # Replace ANSI codes with HTML
    for ansi, html in color_map.items():
        text = text.replace(ansi, html)

    # Clean up any remaining ANSI codes
    text = re.sub(r"\033\[\d+m", "", text)

    return text
