"""
This module provides functionality for creating and updating both analog and decimal clocks
using the Tkinter GUI framework. It supports the display of time in traditional 24-hour format
as well as in decimal time (divided into decidays, centidays, and seconds).

The clocks are drawn on a canvas with customizable styles for various components such as hands,
ticks, and backgrounds. The module uses a global `styles` dictionary to control colors, fonts,
and other visual aspects, ensuring a consistent look across the clocks.

Main Features:
---------------
- Analog clock with 24-hour format and decimal clock using the Swatch Internet Time system.
- Customizable clock hands (hour, minute, second, deciday, centiday) with different lengths and
  colors.
- Digital time display below the clock with configurable font and color.
- Inner circular scale displaying ticks and numbers for both analog and decimal clocks.
- Real-time updates with smooth transitions using the `update_clock` function.
- Modular approach with helper functions to handle specific parts of the clock, such as drawing
  hands, updating kiloseconds/decidays, and drawing the clock face.

Functions:
----------
- `update_clock`: Updates clock hands and digital time, switching between analog and decimal time.
- `draw_hand`: Draws a clock hand as a trapezoid with a triangular tip.
- `draw_inner_scale`: Draws an inner circular scale with ticks for time tracking.
- `draw_clock_face`: Draws the clock face, including tick marks and numbers.
- `update_kiloseconds`: Displays kiloseconds below the clock in the analog time format.
- `update_decidays`: Displays decidays below the clock in decimal time format.
- `run_clock`: Main function to initialize the Tkinter window and start both analog and decimal
  clocks.

The module allows users to run a clock that displays time in either the traditional 24-hour format
or in a decimal-based time system, providing a visually appealing and functional experience.

Dependencies:
------------
- `math`: For trigonometric calculations used in drawing hands and clock ticks.
- `os`: Used for system-level operations (though not explicitly used in this module).
- `time`: For time-related functions and to retrieve the current system time.
- `tkinter`: For creating and updating the graphical user interface.
- `datetime`: For working with date and time, especially in retrieving the current time.
"""

import math
import tkinter as tk
from typing import Dict, List, NamedTuple, Optional, Tuple, TypedDict, Union

from utms.utils import get_seconds_since_midnight


class CanvasConfig(NamedTuple):
    """
    Configuration for the canvas used to draw the clock.

    Attributes:
        canvas (tk.Canvas): The tkinter canvas object where the clock is drawn.
        width (int): The width of the canvas in pixels.
        height (int): The height of the canvas in pixels.
        center (Tuple[int, int]): The coordinates of the canvas center as (x, y).
    """

    canvas: tk.Canvas
    width: int
    height: int
    center: Tuple[int, int]


class HandConfig(NamedTuple):
    """
    Configuration for a clock hand.

    Attributes:
        length (float): The length of the clock hand in pixels.
        angle (float): The angle of the clock hand in radians, relative to 12 o'clock.
        base_width (int): The base width of the clock hand in pixels.
        color (str): The color of the clock hand as a hexadecimal or color name.
        tag (str): The tag used for grouping the clock hand in the canvas.
    """

    length: float
    angle: float
    base_width: int
    color: str
    tag: str


class Styles(TypedDict):
    """
    Configuration for the visual styles of the clock.

    Attributes:
        background_color (str): The background color of the clock as a hexadecimal or color name.
        inner_color (str): The inner color of the clock face as a hexadecimal or color name.
        frame_color (str): The color of the clock frame as a hexadecimal or color name.
        center_circle_color (str): The color of the clock's center circle.
        hand_colors (Dict[str, str]): A mapping of hand names ('hour', 'minute', etc.) to their
        colors.
        hand_widths (Dict[str, int]): A mapping of hand names to their widths in pixels.
        tick_color (str): The color of the clock's tick marks.
        outline_color (str): The color of the clock's outline.
        digit_color (str): The color of the clock's digits.
        font (Tuple[str, int]): The font and size used for the clock's digits.
        digital_time_color (str): The color of the digital time display.
        digital_font (Tuple[str, int]): The font and size used for the digital time display.
        scale_tick_color (str): The color of the scale tick marks.
        scale_digit_color (str): The color of the scale digits.
        kilosecond_color (str): The color of the kilosecond hand.
        deciday_color (str): The color of the deciday hand.
    """

    background_color: str
    inner_color: str
    frame_color: str
    center_circle_color: str
    hand_colors: Dict[str, str]
    hand_widths: Dict[str, int]
    tick_color: str
    outline_color: str
    digit_color: str
    font: Tuple[str, int]
    digital_time_color: str
    digital_font: Tuple[str, int]
    scale_tick_color: str
    scale_digit_color: str
    kilosecond_color: str
    deciday_color: str


styles: Styles = {
    "background_color": "#B0B0B0",
    "inner_color": "#E8E8E8",
    "frame_color": "#636363",
    "center_circle_color": "#636363",
    "hand_colors": {
        "hour": "#4A4A4A",
        "minute": "#000000",
        "second": "#FF3131",
        "deciday": "#4A4A4A",
        "centiday": "#000000",
    },
    "hand_widths": {
        "hour": 4,
        "minute": 2,
        "second": 1,
        "deciday": 4,
        "centiday": 2,
    },
    "tick_color": "#636363",
    "outline_color": "#000000",
    "digit_color": "#000000",
    "font": ("Orbitron", 16),
    "digital_time_color": "#000000",
    "digital_font": ("Orbitron", 16),
    "scale_tick_color": "#636363",
    "scale_digit_color": "#000000",
    "kilosecond_color": "#000000",
    "deciday_color": "#000000",
}


def calculate_angles(
    seconds_since_midnight: int, is_decimal: bool
) -> Tuple[float, float, float, Union[float, None], Union[float, None]]:
    """
    Calculates the angles of the clock hands based on whether it's decimal time or not.
    """
    if not is_decimal:
        # Analog time (24-hour format)
        hour = (seconds_since_midnight // 3600) % 24  # 24-hour format, not 12-hour
        minute = (seconds_since_midnight // 60) % 60
        second = seconds_since_midnight % 60

        # Angles for hands
        hour_angle = math.radians(
            (360 / 12) * (hour % 12) + (360 / 12) * (minute / 60) + (360 / 12) * (second / 3600)
        )
        minute_angle = math.radians((360 / 60) * minute + (360 / 60) * (second / 60))
        second_angle = math.radians((360 / 60) * second)
        return hour_angle, minute_angle, second_angle, None, None

    # Decimal time calculations
    deciday = seconds_since_midnight // 8640
    centiday = (seconds_since_midnight % 8640) // 864
    seconds_in_centiday = (seconds_since_midnight % 8640) % 864

    # Angles for decimal time
    deciday_angle = math.radians(360 * (deciday + (seconds_since_midnight % 8640) / 8640) / 10)
    centiday_angle = math.radians(360 * (centiday + (seconds_since_midnight % 864) / 864) / 10)
    second_angle = math.radians((360 / 864) * seconds_in_centiday)

    return deciday_angle, centiday_angle, second_angle, deciday, centiday


def prepare_hands_and_angles(
    hands: Dict[str, float],
    angles: Tuple[float, float, float, Optional[float], Optional[float]],
    is_decimal: bool,
) -> List[Tuple[str, float, float]]:
    """
    Prepare the hands to draw based on the mode (decimal vs. analog).
    Returns a list of hands and associated angles to draw.
    """
    hands_to_draw = []
    angles_to_draw = []

    if is_decimal:
        # Decimal time: Deciday, Centiday, Second
        hands_to_draw = ["deciday", "centiday", "second"]
        angles_to_draw = [angles[0], angles[1], angles[2]]
    else:
        # Analog time: Hour, Minute, Second
        hands_to_draw = ["hour", "minute", "second"]
        angles_to_draw = [angles[0], angles[1], angles[2]]

    # Now we have hands_to_draw and angles_to_draw ready for drawing
    hands_and_angles = []
    for name, angle in zip(hands_to_draw, angles_to_draw):
        # Fetch the corresponding length from the hands dictionary
        length = hands[name]
        hands_and_angles.append((name, length, angle))

    return hands_and_angles


def draw_clock_hands(
    canvas_config: CanvasConfig, hands_and_angles: List[Tuple[str, float, float]], tag_prefix: str
) -> None:
    """
    Draw the clock hands based on the calculated hands and angles.
    """
    center = canvas_config.center
    canvas_config.canvas.delete(f"{tag_prefix}_hands")

    # Draw each clock hand
    for name, length, angle in hands_and_angles:

        if name == "second":
            hand_config = HandConfig(
                length, angle, 3, styles["hand_colors"][name], f"{tag_prefix}_hands"
            )
            draw_hand(canvas_config, hand_config)
        else:
            base_width = 15 if (name in ("hour", "deciday")) else 10
            hand_config = HandConfig(
                length, angle, base_width, styles["hand_colors"][name], f"{tag_prefix}_hands"
            )

            draw_hand(canvas_config, hand_config)

    # Draw the center circle for aesthetics
    canvas_config.canvas.create_oval(
        center[0] - 7,
        center[1] - 7,
        center[0] + 7,
        center[1] + 7,
        fill=styles["center_circle_color"],
        outline="",
        tags=f"{tag_prefix}_hands",
    )


def update_digital_time(
    canvas_config: CanvasConfig,
    hands: Dict[str, float],
    tag_prefix: str,
    is_decimal: bool,
    seconds_since_midnight: int,
) -> None:
    """
    Updates and displays the digital time (either analog or decimal).
    """
    canvas = canvas_config.canvas
    center = canvas_config.center
    canvas.delete(f"{tag_prefix}_digital")
    if not is_decimal:
        # Analog time (24-hour format)
        hour = (seconds_since_midnight // 3600) % 24
        minute = (seconds_since_midnight // 60) % 60
        second = seconds_since_midnight % 60
        digital_time = f"{hour:02}:{minute:02}:{second:02}"  # 24-hour format
    else:
        # Decimal time
        deciday = seconds_since_midnight // 8640
        centiday = (seconds_since_midnight % 8640) // 864
        seconds_in_centiday = (seconds_since_midnight % 8640) % 864
        digital_time = f"{deciday}.{centiday}.{seconds_in_centiday:03}"

    # Display digital time below the clock
    digital_time_y = center[1] + hands["second"] + 60  # Adjust vertical position
    canvas.create_text(
        center[0],
        digital_time_y,
        text=digital_time,
        font=styles["digital_font"],
        fill=styles["digital_time_color"],
        tags=f"{tag_prefix}_digital",
    )


def update_clock(
    canvas_config: CanvasConfig, hands: Dict[str, float], tag_prefix: str, is_decimal: bool = False
) -> None:
    """
    Updates the positions of the clock hands and the digital time display.
    Uses the styles dictionary for colors and font.
    """
    seconds_since_midnight = get_seconds_since_midnight()

    # Calculate angles for the clock hands based on time
    angles = calculate_angles(seconds_since_midnight, is_decimal)

    # Prepare hands and angles for drawing
    hands_and_angles = prepare_hands_and_angles(hands, angles, is_decimal)

    # Draw clock hands
    draw_clock_hands(canvas_config, hands_and_angles, tag_prefix)

    # Update digital time
    update_digital_time(canvas_config, hands, tag_prefix, is_decimal, seconds_since_midnight)

    if not is_decimal:
        update_kiloseconds(canvas_config, tag_prefix, int(seconds_since_midnight))
    else:
        update_decidays(canvas_config, tag_prefix, int(seconds_since_midnight))
    canvas_config.canvas.after(
        500, update_clock, canvas_config, hands, tag_prefix, is_decimal
    )  # Update every 500ms


def calculate_hand_geometry(
    center: Tuple[int, int], length: float, angle: float, base_width: float
) -> Dict[str, Tuple[float, float]]:
    """
    Calculates the geometry of the clock hand.

    Args:
        center (tuple): Center of the clock (x, y).
        length (int): Length of the hand.
        angle (float): Angle of the hand in radians.
        base_width (int): Width of the hand base.

    Returns:
        dict: Coordinates of the hand's key points.
    """
    tip = (
        center[0] + length * math.sin(angle),
        center[1] - length * math.cos(angle),
    )
    middle = (
        center[0] + (length / 2) * math.sin(angle),
        center[1] - (length / 2) * math.cos(angle),
    )
    middle_offset = (
        (base_width / 2) * math.cos(angle),
        (base_width / 2) * math.sin(angle),
    )
    base_offset = (
        (base_width / 4) * math.cos(angle),
        (base_width / 4) * math.sin(angle),
    )

    return {
        "tip": tip,
        "middle_right": (middle[0] + middle_offset[0], middle[1] + middle_offset[1]),
        "middle_left": (middle[0] - middle_offset[0], middle[1] - middle_offset[1]),
        "base_right": (center[0] + base_offset[0], center[1] + base_offset[1]),
        "base_left": (center[0] - base_offset[0], center[1] - base_offset[1]),
    }


def draw_hand(canvas_config: CanvasConfig, hand_config: HandConfig) -> None:
    """
    Draws a clock hand with an arrow-like shape, where the tip is a single point,
    and the hand widens to its base near the center.

    Args:
        canvas (tk.Canvas): Canvas to draw on.
        center (tuple): Center of the clock (x, y).
        length (int): Length of the hand.
        angle (float): Angle of the hand in radians.
        base_width (int): Maximum width of the hand at the middle.
        color (str): Color of the hand.
        tag (str): Unique tag for the hand.
    """
    canvas = canvas_config.canvas
    center = canvas_config.center

    # Calculate geometry
    geometry = calculate_hand_geometry(
        center, hand_config.length, hand_config.angle, hand_config.base_width
    )

    # Draw the hand as a polygon
    canvas.create_polygon(
        geometry["tip"][0],
        geometry["tip"][1],
        geometry["middle_right"][0],
        geometry["middle_right"][1],
        geometry["base_right"][0],
        geometry["base_right"][1],
        geometry["base_left"][0],
        geometry["base_left"][1],
        geometry["middle_left"][0],
        geometry["middle_left"][1],
        fill=hand_config.color,
        tags=hand_config.tag,
    )


def calculate_tick_coordinates(
    center: Tuple[int, int], radius: float, angle: float, tick_length: float
) -> Tuple[float, float, float, float]:
    """
    Calculates the coordinates for the ends of a tick line.

    Args:
        center (tuple): Center of the circle (x, y).
        radius (int): Radius of the circle.
        angle (float): Angle of the tick in radians.
        tick_length (int): Length of the tick.

    Returns:
        tuple: Coordinates of the tick line's start and end points.
    """
    x1 = center[0] + radius * math.sin(angle)
    y1 = center[1] - radius * math.cos(angle)
    x2 = center[0] + tick_length * math.sin(angle)
    y2 = center[1] - tick_length * math.cos(angle)
    return (x1, y1, x2, y2)


def calculate_digit_coordinates(
    center: Tuple[int, int], tick_length: float, angle: float, offset: int = 5
) -> Tuple[float, float]:
    """
    Calculates the coordinates for positioning a digit near a tick.

    Args:
        center (tuple): Center of the circle (x, y).
        tick_length (int): Length of the tick.
        angle (float): Angle of the tick in radians.
        offset (int): Offset from the tick's end for placing the digit.

    Returns:
        tuple: Coordinates for the digit's placement.
    """
    digit_x = center[0] + (tick_length - offset) * math.sin(angle)
    digit_y = center[1] - (tick_length - offset) * math.cos(angle)
    return (digit_x, digit_y)


def draw_inner_scale(
    canvas_config: CanvasConfig, radius: float, num_ticks: int, scale_tag: str
) -> None:
    """
    Draws an inner circular scale with ticks, using the styles dictionary for tick colors and font.

    Args:
        canvas_config (CanvasConfig): Canvas and center configuration.
        radius (int): Radius of the scale.
        num_ticks (int): Number of ticks to draw.
        scale_tag (str): Tag for identifying scale elements.
        scale_type (str): Type of scale (e.g., "seconds", "centidays").
    """
    for i in range(num_ticks):
        angle = math.radians(i * (360 / num_ticks))

        # Determine tick length
        if i % 100 == 0:
            tick_length = radius - 15
        elif i % 10 == 0:
            tick_length = radius - 10
        else:
            tick_length = radius

        # Draw the tick
        x1, y1, x2, y2 = calculate_tick_coordinates(
            canvas_config.center, radius, angle, tick_length
        )
        canvas_config.canvas.create_line(
            x1, y1, x2, y2, fill=styles["scale_tick_color"], tags=scale_tag
        )

        # Draw the digit for major ticks
        if i % 100 == 0:
            digit_x, digit_y = calculate_digit_coordinates(canvas_config.center, tick_length, angle)
            canvas_config.canvas.create_text(
                digit_x,
                digit_y,
                text=f"{int(i)}",
                font=("Orbitron", 8, "bold"),
                fill=styles["scale_digit_color"],
                tags=scale_tag,
            )


def draw_outer_frame(canvas_config: CanvasConfig, radius: float, tag: str) -> None:
    """
    Draws the metallic outer frame of the clock.

    Args:
        canvas (tk.Canvas): Canvas to draw on.
        center (tuple): Center of the clock (x, y).
        radius (int): Radius of the clock.
        tag (str): Unique tag for the outer frame.
    """
    center = canvas_config.center
    canvas_config.canvas.create_oval(
        center[0] - radius - 5,
        center[1] - radius - 5,
        center[0] + radius + 5,
        center[1] + radius + 5,
        outline=styles["frame_color"],
        width=5,
        tags=tag,
    )


def draw_inner_circle(canvas_config: CanvasConfig, radius: float, tag: str) -> None:
    """
    Draws the inner circle of the clock (background).

    Args:
        canvas (tk.Canvas): Canvas to draw on.
        center (tuple): Center of the clock (x, y).
        radius (int): Radius of the clock.
        tag (str): Unique tag for the inner circle.
    """
    center = canvas_config.center
    canvas_config.canvas.create_oval(
        center[0] - radius,
        center[1] - radius,
        center[0] + radius,
        center[1] + radius,
        fill=styles["inner_color"],
        outline="",
        tags=tag,
    )


def draw_tick(
    canvas_config: CanvasConfig, radius: float, angle: float, is_major: bool, tag: str
) -> None:
    """
    Draws a single tick on the clock face.

    Args:
        canvas (tk.Canvas): Canvas to draw on.
        center (tuple): Center of the clock (x, y).
        radius (int): Radius of the clock.
        angle (float): Angle of the tick in radians.
        is_major (bool): Whether the tick is a major (large) tick.
        tag (str): Unique tag for the ticks.
    """
    center = canvas_config.center
    offset = 10 if is_major else 5
    x_outer = center[0] + radius * math.sin(angle)
    y_outer = center[1] - radius * math.cos(angle)
    x_inner = center[0] + (radius - offset) * math.sin(angle)
    y_inner = center[1] - (radius - offset) * math.cos(angle)

    canvas_config.canvas.create_line(
        x_inner,
        y_inner,
        x_outer,
        y_outer,
        fill=styles["tick_color"],
        width=2 if is_major else 1,
        tags=tag,
    )


def draw_tick_label(
    canvas_config: CanvasConfig, radius: float, angle: float, label: str, tag: str
) -> None:
    """
    Draws a label (number) next to a major tick.

    Args:
        canvas (tk.Canvas): Canvas to draw on.
        center (tuple): Center of the clock (x, y).
        radius (int): Radius of the clock.
        angle (float): Angle of the tick in radians.
        label (str): Label text.
        tag (str): Unique tag for the labels.
    """
    center = canvas_config.center
    x = center[0] + radius * 0.9 * math.sin(angle)
    y = center[1] - radius * 0.9 * math.cos(angle)
    canvas_config.canvas.create_text(
        x,
        y,
        text=label,
        font=("Orbitron", 16, "bold"),
        fill=styles["digit_color"],
        tags=tag,
    )


def draw_clock_face(canvas_config: CanvasConfig, radius: float, is_decimal: bool = False) -> None:
    """
    Draws the clock face with tick marks, labels, and a chrome-style frame.

    Args:
        canvas_config (CanvasConfig): Canvas and center configuration.
        radius (int): Radius of the clock.
        is_decimal (bool): Whether this clock uses the decimal time system.
    """
    center = canvas_config.center

    # Draw outer frame and inner circle
    draw_outer_frame(canvas_config, radius, tag=f"{center}_outer_frame")
    draw_inner_circle(canvas_config, radius, tag=f"{center}_inner_circle")

    # Determine the number of divisions
    divisions = 10 if is_decimal else 12

    for i in range(divisions):
        for j in range(5):  # Subdivisions for minor ticks
            angle = math.radians((i * 360 / divisions) + (j * (360 / divisions) / 5))
            is_major = j == 0

            # Draw ticks
            draw_tick(canvas_config, radius, angle, is_major, tag=f"{center}_ticks")

            # Draw labels for major ticks
            if is_major:
                label = str(i if is_decimal else (i if i != 0 else 12))
                draw_tick_label(canvas_config, radius, angle, label, tag=f"{center}_ticks")


def update_clock_with_inner_scale(
    canvas_config: CanvasConfig, hands: Dict[str, float], tag_prefix: str, is_decimal: bool = False
) -> None:
    """
    Updates the clock with an inner scale for tracking seconds within centiday with neon effects.

    Args:
        canvas (tk.Canvas): The canvas to draw on.
        width (int): The width of the canvas.
        height (int): The height of the canvas.
        center (tuple): The center of the clock as (x, y).
        hands (dict): A dictionary with keys 'hour', 'minute', 'second' or 'deciday', 'centiday',
        'second'.
        tag_prefix (str): A unique tag prefix to manage hands and digital time for each clock.
        is_decimal (bool): Whether this clock uses the decimal time system.
    """
    # Update the clock hands and digital time
    update_clock(canvas_config, hands, tag_prefix, is_decimal)

    # Add inner scale and marker for decimal clock
    if is_decimal:
        draw_inner_scale(canvas_config, hands["second"] * 0.8, 864, f"{tag_prefix}_inner_scale")


def update_kiloseconds(canvas_config: CanvasConfig, scale_tag: str, clock_time: int) -> None:
    """
    Update and display the kiloseconds at the bottom of the right clock, below the current time.

    Args:
        canvas (tk.Canvas): The canvas to draw on.
        center (tuple): The center of the clock as (x, y).
        radius (int): The radius of the inner scale.
        scale_tag (str): A unique tag to manage the scale.
        clock_time (int): The number of seconds since midnight.
    """
    canvas = canvas_config.canvas
    center = canvas_config.center
    radius = canvas_config.height * 1.8
    # Calculate the kiloseconds (1 Ks = 1000 seconds)
    kiloseconds = (
        clock_time % 86400
    ) / 1000  # Kiloseconds since the start of the day (86400 seconds in a day)

    # Get the position for displaying the kiloseconds (below the current time)
    digit_x = center[0]  # Align with the center horizontally
    digit_y = center[1] + 0.25 * radius  # Position it below the current time

    # Clear old kiloseconds text (optional, but useful for updates)
    canvas.delete(f"{scale_tag}_ks")

    # Display the kiloseconds number (formatted to 3 decimal places)
    canvas.create_text(
        digit_x,
        digit_y,
        text=f"{kiloseconds:.3f} Ks",
        font=styles["font"],
        fill=styles["kilosecond_color"],
        tags=f"{scale_tag}_ks",
    )


def update_decidays(canvas_config: CanvasConfig, scale_tag: str, clock_time: int) -> None:
    """
    Update the display of decidays on a canvas.

    This function calculates the decidays (1 deciday = 8640 seconds) based on the current
    `clock_time`, and updates the specified canvas with the calculated value. The deciday
    value is displayed below the kiloseconds on the canvas.

    Args:
        canvas_config: A configuration object containing the canvas, center, and height
            information for rendering.
            - canvas: The drawing canvas where the decidays text will be displayed.
            - center: A tuple of (x, y) coordinates representing the center of the canvas.
            - height: The base height used for scaling the display radius.
        scale_tag (str): A unique tag used to identify and update the decidays text
            element on the canvas.
        clock_time (int): The current time in seconds since midnight.

    Returns:
        None

    Notes:
        - The decidays are calculated as:
          `decidays = (clock_time % 86400) / 8640`
          where 86400 seconds represents a full day.
        - The text is formatted to 5 decimal places for precision.

    Example:
        Assuming `canvas_config` has a canvas centered at (100, 100) and a height of 50:

        >>> update_decidays(canvas_config, "time_display", 43200)
        # Displays "5.00000 dd" on the canvas centered at (100, 100 + 0.25 * radius).

    """
    # Calculate the decidays (1 deciday = 8640 seconds)
    canvas = canvas_config.canvas
    center = canvas_config.center
    radius = canvas_config.height * 1.8

    decidays = (
        clock_time % 86400
    ) / 8640  # Decidays since the start of the day (86400 seconds in a day)

    # Get the position for displaying the decidays (below the kiloseconds)
    digit_x = center[0]  # Align with the center horizontally
    digit_y = center[1] + 0.25 * radius

    # Clear old decidays text (optional, but useful for updates)
    canvas.delete(f"{scale_tag}_dd")

    # Display the decidays number (formatted to 3 decimal places)
    canvas.create_text(
        digit_x,
        digit_y,
        text=f"{decidays:.5f} dd",
        font=styles["font"],
        fill=styles["deciday_color"],
        tags=f"{scale_tag}_dd",
    )


def run_clock() -> None:
    """
    Main function to set up the clock window and start the clocks.
    """
    # Window dimensions
    width, height = 800, 500  # Increased height to accommodate digital time
    clock_radius = 150  # Radius for each clock
    clock1_center = (200, height // 2 - 50)  # Center of first clock
    clock2_center = (600, height // 2 - 50)  # Center of second clock

    # Hand configurations
    hands = {
        "hour": clock_radius * 0.5,
        "minute": clock_radius * 0.8,
        "second": clock_radius * 0.9,
        "deciday": clock_radius * 0.5,
        "centiday": clock_radius * 0.8,
    }

    # Tkinter setup
    root = tk.Tk()
    root.title("Analog Clocks")

    canvas = tk.Canvas(root, width=width, height=height, bg=styles["background_color"])
    canvas.pack()

    # Draw clock faces and update each clock
    for center, tag_prefix, is_decimal in zip(
        [clock1_center, clock2_center], ["duodecimal", "decimal"], [False, True]
    ):
        canvas_config = CanvasConfig(canvas, width, height, center)
        # Draw clock face (outer circle)
        canvas.create_oval(
            center[0] - clock_radius,
            center[1] - clock_radius,
            center[0] + clock_radius,
            center[1] + clock_radius,
            outline=styles["outline_color"],
            width=3,  # Wider outline for emphasis
        )
        draw_clock_face(canvas_config, clock_radius, is_decimal)
        # draw_circuit_lines(canvas, center, clock_radius)

        # Update the clocks
        if is_decimal:
            # Update the decimal clock with inner scale and seconds marker
            update_clock_with_inner_scale(canvas_config, hands, tag_prefix, is_decimal)
        else:
            # Update the standard clock
            update_clock(canvas_config, hands, tag_prefix, is_decimal)

    root.mainloop()
