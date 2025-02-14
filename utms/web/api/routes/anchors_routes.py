from fastapi import APIRouter, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from decimal import Decimal
import hy
from utms.web.api.models import config
from utms.web.api import templates

router = APIRouter()

@router.get("/anchors", response_class=HTMLResponse)
async def anchors_page(request: Request):
    anchors_data = {}
    for anchor in config.anchors._anchors.values():
        name_prop = anchor._properties["name"]
        value_prop = anchor._properties["value"]
        formats_prop = anchor._properties["formats"]
        groups_prop = anchor._properties["groups"]
        anchors_data[anchor.label] = {
            "name": anchor.name,
            "name_original": name_prop.original,
            "value": str(anchor.value),
            "value_original": value_prop.original,
            "formats": [format_spec.__dict__ for format_spec in anchor.formats],
            "formats_original": formats_prop.original,
            "groups": anchor.groups,
            "groups_original": groups_prop.original,
            "uncertainty": {
                "absolute": str(anchor.uncertainty.absolute),
                "relative": str(anchor.uncertainty.relative),
                "confidence_95": anchor.uncertainty.confidence_95
            } if anchor.uncertainty else None
        }
    
    active_filters = request.query_params.get('filters', '').split(',')
    active_filters = [f for f in active_filters if f]
    
    return templates.TemplateResponse(
        "anchors.html",
        {
            "request": request, 
            "active_page": "anchors", 
            "anchors": anchors_data,
            "active_filters": active_filters
        }
    )

@router.get("/")
async def get_anchors():
    anchors_data = {}
    for anchor in config.anchors._anchors.values():
        anchors_data[anchor.label] = {
            "name": anchor.name,
            "value": str(anchor.value),
            "formats": [format_spec.__dict__ for format_spec in anchor.formats],
            "groups": anchor.groups,
            "uncertainty": {
                "absolute": str(anchor.uncertainty.absolute),
                "relative": str(anchor.uncertainty.relative),
                "confidence_95": anchor.uncertainty.confidence_95
            } if anchor.uncertainty else None
        }
    return anchors_data

@router.put("/{label}/{field}")
async def update_anchor(label: str, field: str, value: dict):
    try:
        anchor = config.anchors.get(label)
        if not anchor:
            raise HTTPException(status_code=404, detail="Anchor not found")
            
        if field not in anchor._properties:
            raise HTTPException(status_code=400, detail="Invalid field")
            
        # Only allow editing if field is not dynamic
        if anchor._properties[field].original:
            raise HTTPException(status_code=400, detail="Cannot edit dynamic field")
            
        # Update the property
        if field == "name":
            anchor._properties[field].value = hy.models.String(value["value"])
        elif field == "value":
            try:
                anchor._properties[field].value = hy.models.Integer(value["value"])
            except ValueError:
                anchor._properties[field].value = hy.models.Float(value["value"])
        elif field == "groups":
            if not isinstance(value["value"], list):
                raise HTTPException(status_code=400, detail="Group must be a list")
            anchor._properties[field].value = [hy.models.String(g) for g in value["value"]]
        else:
            anchor._properties[field].value = value["value"]

        config.save_anchors()
        config._load_anchors()
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
