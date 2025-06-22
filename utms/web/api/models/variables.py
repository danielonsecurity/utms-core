from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SerializedTypedValue(BaseModel):
    """Pydantic model for TypedValue serialization (matching TypedValue.serialize()).
    This is used for API responses where a TypedValue object is returned.
    """

    type: str = Field(
        ..., description="The fundamental data type of the value (e.g., 'string', 'integer')."
    )
    value: Any = Field(
        ..., description="The actual data value, serialized to a JSON-compatible format."
    )
    item_type: Optional[str] = Field(
        None, description="For list/dict types, the type of items/values."
    )
    is_dynamic: Optional[bool] = Field(
        False, description="True if the value is derived from a dynamic expression."
    )
    original: Optional[str] = Field(
        None, description="The original Hy expression string if 'is_dynamic' is true."
    )
    enum_choices: Optional[List[Any]] = Field(
        None, description="For 'enum' type, a list of allowed choices."
    )
    item_schema_type: Optional[str] = Field(
        None, description="For LIST of complex objects, the name of the complex type schema."
    )
    referenced_entity_type: Optional[str] = Field(
        None, description="For ENTITY_REFERENCE, the type of entity referenced."
    )
    referenced_entity_category: Optional[str] = Field(
        None, description="For ENTITY_REFERENCE, an optional category constraint."
    )


class VariableResponse(BaseModel):
    """Pydantic model for a single Variable API response."""

    key: str = Field(..., description="The unique identifier for the variable.")
    value: SerializedTypedValue = Field(
        ..., description="The variable's value, as a serialized TypedValue."
    )


class VariableUpdatePayload(BaseModel):
    """Pydantic model for the payload when creating or updating a variable's value.
    This is used for API requests.
    """

    value: Any = Field(
        ...,
        description="The new raw value for the variable. Can be a string, number, boolean, list, dict, or a Hy expression string.",
    )
    is_dynamic: bool = Field(
        False,
        description="Set to true if the value is a dynamic Hy expression that should be stored as such.",
    )
    original_expression: Optional[str] = Field(
        None,
        description="The original Hy expression string if 'is_dynamic' is true. Should be provided if `value` is a resolved dynamic value but stored dynamically.",
    )
    field_type: Optional[str] = Field(
        None,
        description="Optional explicit type string (e.g., 'integer', 'datetime') if inferring from `value` is not sufficient.",
    )
