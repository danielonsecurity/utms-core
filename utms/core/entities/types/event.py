from typing import Dict, ClassVar
from utms.utms_types.entity.types import AttributeDefinition
from utms.utms_types.entity.attributes import CORE_ATTRIBUTES, EXTENDED_ATTRIBUTES
from ..base import TimeEntity

class Event(TimeEntity):
    """An event entity with time specifications"""
    
    attributes: ClassVar[Dict[str, AttributeDefinition]] = {
        **CORE_ATTRIBUTES,
        'ranges': EXTENDED_ATTRIBUTES['ranges'],
        'location': EXTENDED_ATTRIBUTES['location'],
        'description': EXTENDED_ATTRIBUTES['description'],
    }

    def __init__(self, name: str):
        super().__init__(name)
