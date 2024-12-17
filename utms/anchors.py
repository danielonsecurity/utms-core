"""
Module: Anchor Management for Time Anchors

This module provides utilities for creating and managing time anchors.
Time anchors are representations of specific points in time or numerical values
associated with a precision, which can be accessed and organized efficiently.

The module includes two main classes:

1. **Anchor**:
   - Represents a single time anchor with a name, value, and precision.
   - Designed for simplicity, allowing direct access to attributes such as `full_name`,
     `value`, and `precision`.

2. **AnchorManager**:
   - Manages multiple time anchors, enabling functionalities such as adding anchors,
     iterating over them, and accessing anchors by index or label.
   - Supports anchors defined by both `datetime` and `Decimal` values, with customizable precision.

**Features**:
- Add datetime or decimal-based anchors with specific labels and precision.
- Retrieve anchors by label or numerical index.
- Iterate over all anchors managed by the class.
- Handle edge cases for ancient dates (adjusting for negative timestamps).
- Ensure type safety and robust exception handling for invalid access.

**Dependencies**:
- `datetime` and `timezone`: For working with time-based anchors.
- `decimal.Decimal`: To ensure precise numerical representation for anchor values.
- `utms.constants`: Provides constants used for calculations, such as `SECONDS_IN_YEAR`.

**Example Usage**:

```python
from datetime import datetime, timezone
from decimal import Decimal
from utms.anchor_manager import AnchorManager

# Initialize an AnchorManager
manager = AnchorManager()

# Add a datetime anchor
manager.add_datetime_anchor(
    full_name="Epoch Start",
    label="epoch",
    value=datetime(1970, 1, 1, tzinfo=timezone.utc)
)

# Add a decimal anchor
manager.add_decimal_anchor(
    full_name="Custom Anchor",
    label="custom",
    value=Decimal("12345.6789"),
    precision=Decimal("0.001")
)

# Access anchors by label
epoch_anchor = manager["epoch"]

# Iterate through all anchors
for anchor in manager:
    print(anchor.full_name, anchor.value, anchor.precision)

# Get the number of anchors
print(len(manager))
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Iterator, Union

from utms import constants


class Anchor:  # pylint: disable=too-few-public-methods
    """
    Represents a single time anchor with a full name, value, and precision.
    Allows direct attribute access for `full_name`, `value`, and `precision`.
    """

    def __init__(self, full_name: str, value: Decimal, precision: Decimal) -> None:
        self.full_name = full_name
        self.value = value
        self.precision = precision


class AnchorManager:
    """
    A class to manage time anchors, allowing adding new anchors, sorting
    by value, and accessing them by abbreviation.
    """

    def __init__(self) -> None:
        self._anchors: Dict[str, Anchor] = {}

    def add_datetime_anchor(
        self, full_name: str, label: str, value: datetime, precision: Decimal = Decimal(1e-6)
    ) -> None:
        """
        Adds a datetime anchor to the manager.

        :param full_name: The full name of the anchor.
        :param label: The label for the anchor (key).
        :param value: The datetime value of the anchor.
        :param precision: The precision associated with the anchor value.
        """
        if value >= datetime(1, 1, 2, 0, 0, tzinfo=timezone.utc):
            self._anchors[label] = Anchor(full_name, Decimal(value.timestamp()), precision)
        else:
            self._anchors[label] = Anchor(
                full_name, Decimal(value.timestamp()) - constants.SECONDS_IN_YEAR, precision
            )

    def add_decimal_anchor(
        self, full_name: str, label: str, value: Decimal, precision: Decimal = Decimal(1e-6)
    ) -> None:
        """
        Adds a decimal-based anchor to the manager.

        :param full_name: The full name of the anchor.
        :param label: The label for the anchor (key).
        :param value: The decimal value representing the anchor.
        :param precision: The precision associated with the anchor value. Default is 1e-6.
        :return: None
        :raises ValueError: If the provided value is not of type Decimal.

        **Example**:

        .. code-block:: python

        manager = AnchorManager()
        manager.add_decimal_anchor("Big Bang", "BB", Decimal("13.8e9"))
        """
        self._anchors[label] = Anchor(full_name, value, precision)

    def __iter__(self) -> Iterator[Anchor]:
        """
        Returns an iterator over the anchors.
        :return: An iterator of (label, anchor_data) tuples.
        """
        return iter(self._anchors.values())

    def __getitem__(self, index: Union[int, str]) -> Anchor:
        """
        Makes the class subscriptable by allowing access via index or label.

        :param index: The index or label of the item to retrieve.
        :return: An Anchor object.
        :raises KeyError: If the label is not found.
        :raises IndexError: If the index is out of range.
        """
        if isinstance(index, int):  # Index-based access
            try:
                return list(self._anchors.values())[index]
            except IndexError as exc:
                raise IndexError(f"Index {index} is out of range.") from exc

        else:  # Label-based access
            if index in self._anchors:
                return self._anchors[index]
            raise KeyError(f"Label '{index}' not found.")

    def __len__(self) -> int:
        """
        Returns the number of anchors in the manager.
        :return: The number of anchors.
        """
        return len(self._anchors)
