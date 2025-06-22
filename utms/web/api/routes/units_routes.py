from decimal import Decimal

import hy
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from utms.core.config import UTMSConfig as Config
from utms.web.api import templates
from utms.web.api.utils import format_scientific
from utms.web.dependencies import get_config

router = APIRouter()


@router.get("/api/units", response_class=JSONResponse)
async def get_units(config: Config = Depends(get_config)):
    units_data = {}
    for label, unit in config.units.items():
        units_data[unit.label] = {
            "name": unit.name,
            "value": str(unit.value),
            "groups": unit.groups or [],
        }
    return units_data


@router.put("/api/units/{label}", response_class=JSONResponse)
async def update_unit(label: str, updates: dict = Body(...), config: Config = Depends(get_config)):
    try:
        unit = config.units.get_unit(label)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        current_label = label

        # Process updates in specific order: label first, then others
        if "label" in updates:
            new_label = updates["label"]
            if new_label != current_label:
                if config.units.get_unit(new_label):
                    raise HTTPException(status_code=400, detail="Label already exists")
                config.units.remove_unit(current_label)
                unit.label = new_label
                config.units.add_unit(unit)
                current_label = new_label

        # Handle other updates
        if "name" in updates:
            unit.name = updates["name"]

        if "value" in updates:
            try:
                unit.value = Decimal(updates["value"])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid numeric value")

        if "groups" in updates:
            if not isinstance(updates["groups"], list):
                raise HTTPException(status_code=400, detail="Groups must be a list")
            unit.groups = updates["groups"]

        config.units.save()

        return {"status": "success", "new_label": current_label}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        if not all(key in unit_data for key in ["label", "name", "value"]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        try:
            value = Decimal(unit_data["value"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid value format")

        if config.units.get_unit(unit_data["label"]):
            raise HTTPException(status_code=400, detail="Unit with this label already exists")

        unit = config.units.create_unit(
            label=unit_data["label"],
            name=unit_data["name"],
            value=value,
            groups=unit_data.get("groups", []),
        )

        config.units.save()

        return {
            "status": "success",
            "unit": {
                "label": unit.label,
                "name": unit.name,
                "value": str(unit.value),
                "groups": unit.groups,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/units/{label}", response_class=JSONResponse)
async def delete_unit(label: str, config: Config = Depends(get_config)):
    try:
        if not config.units.get_unit(label):
            raise HTTPException(status_code=404, detail=f"Unit '{label}' not found")

        config.units.remove_unit(label)
        config.units.save()

        return {"status": "success", "message": f"Unit '{label}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
