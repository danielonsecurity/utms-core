import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from utms.clock import CanvasConfig, HandConfig, draw_clock_hands, styles


class TestDrawClockHands(unittest.TestCase):

    @patch("utms.clock.draw_hand")
    def test_draw_clock_hands(self, mock_draw_hand):
        # Setup a mock canvas object
        mock_canvas = MagicMock()

        # Setup the CanvasConfig with the mock canvas and other attributes
        mock_center = (250, 250)
        canvas_config = CanvasConfig(
            canvas=mock_canvas,
            width=500,  # Assuming a width of 500 pixels
            height=500,  # Assuming a height of 500 pixels
            center=mock_center,
        )

        # Define hands and angles
        hands_and_angles = [
            ("hour", 100, 90),  # Hour hand at 90 degrees (right)
            ("minute", 120, 180),  # Minute hand at 180 degrees (down)
            ("second", 150, 270),  # Second hand at 270 degrees (left)
        ]
        tag_prefix = "clock"

        # Call the function under test
        draw_clock_hands(canvas_config, hands_and_angles, tag_prefix)

        # Check that delete was called with the correct tag
        mock_canvas.delete.assert_called_with(f"{tag_prefix}_hands")

        # Check that draw_hand was called with the correct configurations for each hand
        for name, length, angle in hands_and_angles:
            if name == "second":
                hand_config = HandConfig(
                    length, angle, 3, styles["hand_colors"][name], f"{tag_prefix}_hands"
                )
            else:
                base_width = 15 if (name == "hour") else 10
                hand_config = HandConfig(
                    length, angle, base_width, styles["hand_colors"][name], f"{tag_prefix}_hands"
                )
            # Assert that draw_hand was called with the correct parameters for each hand
            mock_draw_hand.assert_any_call(canvas_config, hand_config)

        # Check if the center circle is drawn with the correct arguments
        mock_canvas.create_oval.assert_called_with(
            243,
            243,
            257,
            257,
            fill=styles["center_circle_color"],
            outline="",
            tags=f"{tag_prefix}_hands",
        )

    @patch("utms.clock.draw_hand")
    def test_draw_clock_hands_empty(self, mock_draw_hand):
        # Setup a mock canvas object
        mock_canvas = MagicMock()

        # Setup the CanvasConfig with the mock canvas and other attributes
        mock_center = (250, 250)
        canvas_config = CanvasConfig(
            canvas=mock_canvas,
            width=500,  # Assuming a width of 500 pixels
            height=500,  # Assuming a height of 500 pixels
            center=mock_center,
        )

        # Test case with no hands (empty list)
        hands_and_angles = []
        tag_prefix = "clock"

        # Call the function under test
        draw_clock_hands(canvas_config, hands_and_angles, tag_prefix)

        # Check that no hands are drawn and no calls to draw_hand are made
        mock_draw_hand.assert_not_called()
        mock_canvas.create_oval.assert_called_once()  # Center circle should be drawn

    @patch("utms.clock.draw_hand")
    def test_draw_clock_hands_single_hand(self, mock_draw_hand):
        # Setup a mock canvas object
        mock_canvas = MagicMock()

        # Setup the CanvasConfig with the mock canvas and other attributes
        mock_center = (250, 250)
        canvas_config = CanvasConfig(
            canvas=mock_canvas,
            width=500,  # Assuming a width of 500 pixels
            height=500,  # Assuming a height of 500 pixels
            center=mock_center,
        )

        # Test case with a single hand
        hands_and_angles = [("second", 150, 270)]  # Second hand at 270 degrees
        tag_prefix = "clock"

        # Call the function under test
        draw_clock_hands(canvas_config, hands_and_angles, tag_prefix)

        # Check that draw_hand was called once for the second hand
        mock_draw_hand.assert_called_once_with(
            canvas_config,
            HandConfig(150, 270, 3, styles["hand_colors"]["second"], f"{tag_prefix}_hands"),
        )

        # Check if the center circle is drawn with the correct arguments
        mock_canvas.create_oval.assert_called_with(
            243,
            243,
            257,
            257,
            fill=styles["center_circle_color"],
            outline="",
            tags=f"{tag_prefix}_hands",
        )
