from typing import Optional
from utms.utms_types.hy.types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type

def node_to_typed_value(node: HyNode, field_type: Optional[FieldType] = None) -> TypedValue:
    """Convert a HyNode to a TypedValue."""
    if isinstance(node.value, TypedValue):
        return node.value
        
    # Determine type
    if field_type is None:
        field_type = infer_type(node.value)
        
    # Create TypedValue
    return TypedValue(
        value=node.value,
        field_type=field_type,
        is_dynamic=node.is_dynamic,
        original=node.original
    )

def typed_value_to_node(typed_value: TypedValue, node_type: str = "value", field_name: Optional[str] = None) -> HyNode:
    """Create a HyNode from a TypedValue."""
    return HyNode(
        type=node_type,
        value=typed_value.value,
        original=typed_value.original,
        is_dynamic=typed_value.is_dynamic,
        field_name=field_name
    )
