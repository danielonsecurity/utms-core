import hy

from utms.core.logger import get_logger

from ..node import HyNode
from ..utils import is_dynamic_content

logger = get_logger()


def parse_pattern_def(expr: hy.models.Expression, original: str) -> HyNode:
    """Parse a def-pattern expression."""
    if len(expr) < 2:
        return None

    name = str(expr[1])
    properties = []

    for prop in expr[2:]:
        if isinstance(prop, hy.models.Expression):
            prop_name = str(prop[0])

            # Handle properties that should be pairs
            if prop_name in ["between", "except-between"]:
                if len(prop) != 3:  # Should have name and two values
                    logger.warning(f"Expected two values for {prop_name}, got {len(prop)-1}")
                    continue
                # Create a list of the two values
                prop_value = hy.models.List([prop[1], prop[2]])
            else:
                prop_value = prop[1]

            is_dynamic = is_dynamic_content(prop_value)
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
        type="def-pattern",
        value=name,
        children=properties,
        original=original,
    )
