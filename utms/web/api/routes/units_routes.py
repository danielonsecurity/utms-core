from fastapi import APIRouter, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from decimal import Decimal
import hy
from utms.web.api.models import config
from utms.web.api import templates
from utms.web.api.utils import format_scientific

router = APIRouter()

@router.get("/units", response_class=HTMLResponse)
async def units_page(request: Request):
    units_data = {}
    unit_manager = config.units
    for label in unit_manager:
        unit = unit_manager[label]
        units_data[label] = {
            "name": unit.name,
            "value": str(unit.value),
            "groups": unit.groups
        }
    active_filters = request.query_params.get("filters", "").split(",")
    active_filters = [f for f in active_filters if f]
    return templates.TemplateResponse(
        "units.html",
        {"request": request,
         "active_page": "units",
         "units": units_data,
         "active_filters": active_filters,
         "format_scientific": format_scientific}
    )

@router.get("/")
async def get_units():
    units_data = {}
    for unit in config.units._units.values():
        units_data[unit.label] = {
            "name": unit.name,
            "value": str(unit.value),
            "groups": unit.groups
        }
    return units_data

@router.put("/{label}/{field}")
async def update_unit(label: str, field: str, value: dict):
    try:
        unit = config.units.get_unit(label)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        if field == "label":
            new_label = value["value"]
            if new_label != label:
                if config.units.get_unit(new_label):
                    raise HTTPException(status_code=400, detail="Label already exists")
                config.units._units[new_label] = unit
                del config.units._units[label]
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

        config.save_fixed_units()
        config._load_fixed_units()
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_unit(unit: dict):
    try:
        if not all(key in unit for key in ['label', 'name', 'value']):
            raise HTTPException(status_code=400, detail="Missing required fields")

        try:
            unit['value'] = Decimal(unit['value'])
        except:
            raise HTTPException(status_code=400, detail="Invalid value format")

        success = config.units.create_unit(
            label=unit["label"],
            name=unit["name"],
            value=unit["value"],
            groups=unit["groups"],
        ) is not None

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create unit")

        config.save_fixed_units()
        config._load_fixed_units()

        return {"message": "Unit created successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{label}")
async def delete_unit(label: str):
    try:
        unit = config.units.get_unit(label)
        if not unit:
            raise HTTPException(status_code=404, detail=f"Unit '{label}' not found")

        del config.units._units[label]
        
        config.save_fixed_units()
        config._load_fixed_units()

        return {"message": f"Unit '{label}' deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
