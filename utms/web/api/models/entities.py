# utms.web.api.models.entities.py
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field  # Field might not be needed for these simple payloads


class AttributeSchemaDetail(BaseModel):
    type: str
    label: str
    default_value: Any  # This can remain Any as it's schema definition
    is_dynamic_allowed: Optional[bool] = None
    enum_choices: Optional[List[Any]] = None


class EntityTypeDetailSchema(BaseModel):
    name: str = Field(..., description="The key/identifier for the entity type (e.g., 'task')")
    display_name: str = Field(
        ..., alias="displayName", description="The user-friendly display name (e.g., 'TASK')"
    )
    attributes: Dict[str, AttributeSchemaDetail] = Field(
        ..., description="Schema definition for each attribute"
    )


class AttributeUpdatePayload(BaseModel):
    """
    Payload for updating a single entity attribute.
    Matches what the frontend sends.
    """

    value: Any  # The new primitive/resolved value (e.g., ISO string, number, boolean, or Hy code string)
    is_dynamic: bool = Field(default=False)
    original: Optional[str] = Field(default=None)


class CreateEntityRawAttributesPayload(BaseModel):
    """
    Payload for creating a new entity, defining the structure for attributes_raw.
    This is a dictionary where keys are attribute names and values are the
    raw values (Python natives or Hy code strings) from the client.
    """

    attributes_raw: Dict[str, Any] = Field(default_factory=dict)


class CreateEntityPayload(BaseModel):
    """
    Full payload for creating a new entity.
    This model will be used if you want to receive the entire entity creation data
    as a single Pydantic model in your POST /api/entities route, instead of separate Body fields.
    Using embed=True for individual Body fields achieves a similar nested structure in the request.
    """

    name: str
    entity_type: str
    attributes_raw: Dict[str, Any] = Field(default_factory=dict)
