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

    # Convenience methods for common colors
    @staticmethod
    def red(text: str) -> str:
        return ColorFormatter.format(text, Fore.RED)

    @staticmethod
    def red_bg(text: str) -> str:
        return ColorFormatter.format(text, Back.RED)

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
    def bright(text: str) -> str:
        return ColorFormatter.format(text, Style.BRIGHT)

    @staticmethod
    def format_if(text: str, condition: bool, *colors: ColorCode) -> str:
        return ColorFormatter.format(text, *colors) if condition else text
