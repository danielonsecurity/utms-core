import re
from typing import List, Union

from colorama import Back, Fore, Style, init

init()

ColorCode = Union[str, Fore, Back, Style]


class ColorFormatter:
    """Formats text with colorama colors."""

    # Color codes available as class attributes
    RED = Fore.RED
    GREEN = Fore.GREEN
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    YELLOW = Fore.YELLOW
    MAGENTA = Fore.MAGENTA
    WHITE = Fore.WHITE
    BLACK = Fore.BLACK

    RED_BG = Back.RED
    GREEN_BG = Back.GREEN
    BLUE_BG = Back.BLUE
    CYAN_BG = Back.CYAN
    YELLOW_BG = Back.YELLOW
    MAGENTA_BG = Back.MAGENTA
    WHITE_BG = Back.WHITE
    BLACK_BG = Back.BLACK

    BRIGHT = Style.BRIGHT
    DIM = Style.DIM
    NORMAL = Style.NORMAL

    @staticmethod
    def format(text: str, *colors: ColorCode) -> str:
        """Format text with color codes."""
        return "".join(colors) + str(text) + Style.RESET_ALL

    # Foreground colors
    @staticmethod
    def red(text: str) -> str:
        return ColorFormatter.format(text, Fore.RED)

    @staticmethod
    def green(text: str) -> str:
        return ColorFormatter.format(text, Fore.GREEN)

    @staticmethod
    def blue(text: str) -> str:
        return ColorFormatter.format(text, Fore.BLUE)

    @staticmethod
    def cyan(text: str) -> str:
        return ColorFormatter.format(text, Fore.CYAN)

    @staticmethod
    def yellow(text: str) -> str:
        return ColorFormatter.format(text, Fore.YELLOW)

    @staticmethod
    def magenta(text: str) -> str:
        return ColorFormatter.format(text, Fore.MAGENTA)

    @staticmethod
    def white(text: str) -> str:
        return ColorFormatter.format(text, Fore.WHITE)

    @staticmethod
    def black(text: str) -> str:
        return ColorFormatter.format(text, Fore.BLACK)

    # Background colors
    @staticmethod
    def red_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.RED)

    @staticmethod
    def green_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.GREEN)

    @staticmethod
    def blue_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.BLUE)

    @staticmethod
    def cyan_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.CYAN)

    @staticmethod
    def yellow_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.YELLOW)

    @staticmethod
    def magenta_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.MAGENTA)

    @staticmethod
    def white_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.WHITE)

    @staticmethod
    def black_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.BLACK)

    # Style modifiers
    @staticmethod
    def bright(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT)

    @staticmethod
    def dim(text: str) -> str:
        return ColorFormatter.format(text, Style.DIM)

    @staticmethod
    def normal(text: str) -> str:
        return ColorFormatter.format(text, Style.NORMAL)

    # Combined styles with bright
    @staticmethod
    def bright_red(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.RED)

    @staticmethod
    def bright_green(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.GREEN)

    @staticmethod
    def bright_blue(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.BLUE)

    @staticmethod
    def bright_cyan(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.CYAN)

    @staticmethod
    def bright_yellow(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.YELLOW)

    @staticmethod
    def bright_magenta(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.MAGENTA)

    @staticmethod
    def bright_white(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.WHITE)

    @staticmethod
    def bright_black(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT, Fore.BLACK)

    # Combined foreground and background
    @staticmethod
    def on_color(text: str, fore: ColorCode, back: ColorCode) -> str:
        return ColorFormatter.format(text, fore, back)

    # Conditional formatting
    @staticmethod
    def format_if(text: str, condition: bool, *colors: ColorCode) -> str:
        return ColorFormatter.format(text, *colors) if condition else text


def color_scientific_format(number_str: str) -> str:
    """Format scientific notation string with colored 'e' and '+/-' symbols."""
    # Split the string at 'e'
    parts = number_str.split("e")
    if len(parts) != 2:
        return number_str  # Return unchanged if not in scientific notation

    base, exponent = parts
    # Handle the sign in the exponent
    sign = ""
    if exponent.startswith("+") or exponent.startswith("-"):
        sign = exponent[0]
        exponent = exponent[1:]

    # Construct the colored string
    return f"{base}" f"{ColorFormatter.magenta('e')}" f"{ColorFormatter.red(sign)}" f"{exponent}"



def ansi_to_html(text: str) -> str:
    """Convert ANSI color codes to HTML span elements with appropriate classes."""
    
    # ANSI color to CSS class mapping
    color_map = {
        # Reset
        '\033[0m': '</span>',  
        
        # Foreground colors
        '\033[30m': '<span class="ansi-black">',     # Black
        '\033[31m': '<span class="ansi-red">',       # Red
        '\033[32m': '<span class="ansi-green">',     # Green
        '\033[33m': '<span class="ansi-yellow">',    # Yellow
        '\033[34m': '<span class="ansi-blue">',      # Blue
        '\033[35m': '<span class="ansi-magenta">',   # Magenta
        '\033[36m': '<span class="ansi-cyan">',      # Cyan
        '\033[37m': '<span class="ansi-white">',     # White
        
        # Background colors
        '\033[40m': '<span class="ansi-bg-black">',   # Black Background
        '\033[41m': '<span class="ansi-bg-red">',     # Red Background
        '\033[42m': '<span class="ansi-bg-green">',   # Green Background
        '\033[43m': '<span class="ansi-bg-yellow">',  # Yellow Background
        '\033[44m': '<span class="ansi-bg-blue">',    # Blue Background
        '\033[45m': '<span class="ansi-bg-magenta">', # Magenta Background
        '\033[46m': '<span class="ansi-bg-cyan">',    # Cyan Background
        '\033[47m': '<span class="ansi-bg-white">',   # White Background
        
        # Styles
        '\033[1m': '<span class="ansi-bright">',      # Bright
        '\033[2m': '<span class="ansi-dim">',         # Dim
        '\033[22m': '<span class="ansi-normal">',     # Normal
    }
    
    # Replace ANSI codes with HTML
    for ansi, html in color_map.items():
        text = text.replace(ansi, html)
    
    # Clean up any remaining ANSI codes
    text = re.sub(r'\033\[\d+m', '', text)
    
    return text
