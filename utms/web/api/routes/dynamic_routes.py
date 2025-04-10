from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from utms.core.services.dynamic import dynamic_resolution_service
from utms.web.dependencies import get_config
from utms.utms_types import DynamicExpressionInfo

router = APIRouter()

@router.get("/api/dynamic/expressions")
async def get_dynamic_expressions(
    component_type: Optional[str] = None,
    component_label: Optional[str] = None,
    attribute: Optional[str] = None
):
    """
    Get dynamic expression information, optionally filtered by component type,
    label, and attribute.
    """

    try:
        breakpoint()
        result = {}
        
        # Convert registry data to dictionary format
        for type_, label, attr, info in dynamic_resolution_service.registry:
            if component_type and type_ != component_type:
                continue
            if component_label and label != component_label:
                continue
            if attribute and attr != attribute:
                continue
                
            if type_ not in result:
                result[type_] = {}
            if label not in result[type_]:
                result[type_][label] = {}
            
            # Convert DynamicExpressionInfo to dict
            result[type_][label][attr] = {
                "original": info.original,
                "value": info.current_value,
                "is_dynamic": info.is_dynamic,
                "history": [
                    {"timestamp": str(h.timestamp), "value": h.value}
                    for h in info.history
                ]
            }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/dynamic/evaluate")
async def evaluate_expression(
    component_type: str,
    component_label: str,
    attribute: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    Trigger re-evaluation of dynamic expressions
    """
    try:
        results = dynamic_resolution_service.evaluate_all(
            component_type=component_type,
            component_label=component_label,
            context=context
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/dynamic/history")
async def clear_history(
    component_type: Optional[str] = None,
    component_label: Optional[str] = None,
    attribute: Optional[str] = None,
    before: Optional[datetime] = None
):
    """
    Clear evaluation history for dynamic expressions
    """
    try:
        dynamic_resolution_service.clear_history(
            component_type=component_type,
            component_label=component_label,
            attribute=attribute,
            before=before
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
