from typing import Any, List, Optional

from pydantic import BaseModel


class DateTimeComponents(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    second: int = 0
    microsecond: int = 0
    tz_offset: Optional[str] = None


class ConfigFieldUpdatePayload(BaseModel):
    value: Any
    type: Optional[str] = None
    is_dynamic: Optional[bool] = False
    original: Optional[str] = None
    enum_choices: Optional[List[Any]] = None
    list_item_type: Optional[str] = None
