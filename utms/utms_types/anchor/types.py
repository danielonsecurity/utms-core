from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TypedDict, Union

from ..hy.types import PropertyValue, NamesList

# Complex types
class AnchorKwargs(TypedDict, total=False):
    name: PropertyValue
    value: PropertyValue
    groups: PropertyValue
    precision: PropertyValue
    breakdowns: PropertyValue

