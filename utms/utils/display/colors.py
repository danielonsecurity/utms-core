from typing import Union

from colorama import Back, Fore, Style, init
from colorama.ansi import AnsiBack, AnsiFore, AnsiStyle

init()

ColorCode = Union[str, AnsiFore, AnsiBack, AnsiStyle]


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
