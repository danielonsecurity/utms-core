from decimal import Decimal

import hy
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import Config
from utms.core.formats import TimeUncertainty
from utms.core.models.anchor import FormatSpec
from utms.utils import hy_to_python
from utms.web.api import templates
from utms.web.dependencies import get_config

router = APIRouter()


@router.get("/api/anchors", response_class=JSONResponse)
async def get_anchors(config: Config = Depends(get_config)):
    anchors_data = {}
    for label, anchor in config.anchors.items():
        uncertainty_data = None
        if isinstance(anchor.uncertainty, TimeUncertainty):
            uncertainty_data = {
                "absolute": str(anchor.uncertainty.absolute),
                "relative": str(anchor.uncertainty.relative),
                "confidence_95": anchor.uncertainty.confidence_95,
            }

        anchors_data[label] = {
            "name": hy_to_python(anchor.name),
            "name_original": anchor.name_original,
            "value": str(hy_to_python(anchor.value)),
            "value_original": anchor.value_original,
            "formats": [
                {k: hy_to_python(v) for k, v in format_spec.__dict__.items()}
                for format_spec in anchor.formats
            ],
            "groups": hy_to_python(anchor.groups),
            "uncertainty": uncertainty_data,
        }
    return anchors_data


@router.put("/api/anchors/{label}/{field}", response_class=JSONResponse)
async def update_anchor(label: str, field: str, value: dict, config: Config = Depends(get_config)):
    try:
        anchor = config.anchors.get_anchor(label)
        if not anchor:
            raise HTTPException(status_code=404, detail="Anchor not found")

        # Update the field based on type
        if field == "name":
            anchor.name = str(value["value"])
        elif field == "value":
            try:
                anchor.value = Decimal(value["value"])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid numeric value")
        elif field == "groups":
            if not isinstance(value["value"], list):
                raise HTTPException(status_code=400, detail="Groups must be a list")
            anchor.groups = [str(g) for g in value["value"]]
        elif field == "formats":
            if not isinstance(value["value"], list):
                raise HTTPException(status_code=400, detail="Formats must be a list")
            anchor.formats = [
                FormatSpec(
                    format=str(fmt) if isinstance(fmt, str) else None,
                    units=[str(u) for u in fmt] if isinstance(fmt, list) else None,
                )
                for fmt in value["value"]
            ]
        else:
            raise HTTPException(status_code=400, detail=f"Invalid field: {field}")

        # Save changes
        config.anchors.save()

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
