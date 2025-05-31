from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class AttributeSchemaDetail(BaseModel):
    type: str
    label: str
    default_value: Any
    is_dynamic_allowed: Optional[bool] = None
    enum_choices: Optional[List[Any]] = None


class EntityTypeDetailSchema(BaseModel):
    name: str = Field(..., description="The key/identifier for the entity type (e.g., 'task')")
    display_name: str = Field(..., alias="displayName", description="The user-friendly display name (e.g., 'TASK')")
    attributes: Dict[str, AttributeSchemaDetail] = Field(..., description="Schema definition for each attribute")


