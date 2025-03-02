import hy

from utms.core.logger import get_logger

from ..node import HyNode
from ..utils import is_dynamic_content

logger = get_logger()


def parse_anchor_def(expr: hy.models.Expression, original: str) -> HyNode:
    """Parse a def-anchor expression."""
    if len(expr) < 2:
        return None

    name = str(expr[1])  # The anchor name/label
    properties = []

    # Process each property expression (starting from index 2)
    for prop in expr[2:]:
        if isinstance(prop, hy.models.Expression):
            prop_name = str(prop[0])
            prop_value = prop[1]

            # For dynamic expressions (like function calls or complex expressions)
            is_dynamic = is_dynamic_content(prop_value)

            logger.debug(f"Property: {prop_name}")
            logger.debug(f"Value: {prop_value}")
            logger.debug(f"Is dynamic: {is_dynamic}")
            logger.debug(f"Original: {hy.repr(prop_value) if is_dynamic else None}")

            properties.append(
                HyNode(
                    type="property",
                    value=prop_name,
                    children=[
                        HyNode(
                            type="value",
                            value=prop_value,
                            original=hy.repr(prop_value) if is_dynamic else None,
                            is_dynamic=is_dynamic,
                        )
                    ],
                )
            )

    return HyNode(
        type="def-anchor",
        value=name,
        children=properties,
        original=original,
    )
