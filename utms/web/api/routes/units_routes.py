from decimal import Decimal

import hy
from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core import Config
from utms.web.api import templates
from utms.web.api.utils import format_scientific

config = Config()
unit_component = config.units

router = APIRouter()


@router.get("/units", response_class=HTMLResponse)
async def units_page(request: Request):
    units_data = {}
    for label, unit in unit_component.get_all_units().items():
        units_data[label] = {"name": unit.name, "value": str(unit.value), "groups": unit.groups}
    active_filters = request.query_params.get("filters", "").split(",")
    active_filters = [f for f in active_filters if f]
    return templates.TemplateResponse(
        "units.html",
        {
            "request": request,
            "active_page": "units",
            "units": units_data,
            "active_filters": active_filters,
            "format_scientific": format_scientific,
        },
    )


@router.get("/api/units", response_class=JSONResponse)
async def get_units():
    units_data = {}
    for label, unit in unit_component.get_all_units().items():
        units_data[unit.label] = {
            "name": unit.name,
            "value": str(unit.value),
            "groups": unit.groups,
        }
    return units_data


@router.put("/api/units/{label}", response_class=JSONResponse)
async def update_unit_bulk(label: str, updates: dict = Body(...)):
    try:
        unit = unit_component.get_unit(label)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        current_label = label

        # Process updates in specific order: label first, then others
        if "label" in updates:
            new_label = updates["label"]
            if new_label != current_label:
                if config.units.get_unit(new_label):
                    raise HTTPException(status_code=400, detail="Label already exists")
                unit_component.remove_unit(current_label)
                unit_component.add_unit(unit)
                unit._label = new_label
                current_label = new_label

        # Process other fields
        for field, value in updates.items():
            if field == "label":
                continue  # Already handled

            if field not in unit._properties:
                raise HTTPException(status_code=400, detail=f"Invalid field: {field}")

            if unit._properties[field].original:
                raise HTTPException(status_code=400, detail=f"Cannot edit dynamic field: {field}")

            if field == "name":
                unit._properties[field].value = hy.models.String(value)
            elif field == "value":
                try:
                    unit._properties[field].value = Decimal(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid numeric value")
            elif field == "groups":
                if not isinstance(value, list):
                    raise HTTPException(status_code=400, detail="Groups must be a list")
                unit._properties[field].value = [hy.models.String(g) for g in value]

        unit_component.save()
        unit_component.load()

        return {"status": "success", "new_label": current_label}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/units/{label}/{field}", response_class=JSONResponse)
async def update_unit(label: str, field: str, value: dict):
    try:
        unit = unit_component.get_unit(label)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        if field == "label":
            new_label = value["value"]
            if new_label != label:
                if unit_component.get_unit(new_label):
                    raise HTTPException(status_code=400, detail="Label already exists")
                unit_component.remove_unit(label)
                unit_component.add_unit(unit)
                unit._label = new_label
        else:
            if field not in unit._properties:
                raise HTTPException(status_code=400, detail="Invalid field")

            if unit._properties[field].original:
                raise HTTPException(status_code=400, detail="Cannot edit dynamic field")

            if field == "name":
                unit._properties[field].value = hy.models.String(value["value"])
            elif field == "value":
                try:
                    unit._properties[field].value = Decimal(value["value"])
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid numeric value")
            elif field == "groups":
                if not isinstance(value["value"], list):
                    raise HTTPException(status_code=400, detail="Groups must be a list")
                unit._properties[field].value = [hy.models.String(g) for g in value["value"]]

        unit_component.save()
        unit_component.load()

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/units", response_class=JSONResponse)
async def create_unit(unit: dict):
    try:
        if not all(key in unit for key in ["label", "name", "value"]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        try:
            unit["value"] = Decimal(unit["value"])
        except:
            raise HTTPException(status_code=400, detail="Invalid value format")

        unit_component.create_unit(
            label=unit["label"],
            name=unit["name"],
            value=unit["value"],
            groups=unit["groups"],
        )
        success = True

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create unit")

        unit_component.save()
        unit_component.load()

        return {"message": "Unit created successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/units/{label}", response_class=JSONResponse)
async def delete_unit(label: str):
    try:
        unit = unit_component.get_unit(label)
        if not unit:
            raise HTTPException(status_code=404, detail=f"Unit '{label}' not found")

        unit_component.remove_unit(label)
        unit_component.save()
        unit_component.load()

        return {"message": f"Unit '{label}' deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
