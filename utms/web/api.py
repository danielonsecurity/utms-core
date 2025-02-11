from decimal import Decimal
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import uvicorn
import hy

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="utms/web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="utms/web/templates")

# Get reference to Config instance
from utms.core.config import Config
config = Config()

@app.get("/config", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "config.html", 
        {"request": request, "config": config.data, "active_page": "config"}
    )

@app.get("/api/config")
async def get_config():
    return config.data

@app.put("/api/config/{key}")
async def update_config(key: str, value: str=Body(...)):
    try:
        config.set_value(key, value)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/units")
async def get_units():
    units_data = {}
    for unit in config.units._units.values():
        units_data[unit.label] = {
            "name": unit.name,
            "value": str(unit.value),  # Convert Decimal to string for JSON
            "groups": unit.groups
        }
    return units_data

def format_scientific(num, max_digits):
    str_num = str(num)
    if 'E' in str_num:
        mantissa, exponent = str_num.split('E')
        if len(mantissa) > max_digits:
            return mantissa[:max_digits] + '...' + 'E' + exponent
    else:
        if len(str_num) > max_digits:
            return str_num[:max_digits] + '...'
    return str_num

@app.get("/units", response_class=HTMLResponse)
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

@app.put("/api/units/{label}/{field}")
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

            # Only allow editing if field is not dynamic
            if unit._properties[field].original:
                raise HTTPException(status_code=400, detail="Cannot edit dynamic field")

            # Update the property
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


@app.get("/api/anchors")
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



@app.put("/api/anchors/{label}/{field}")
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


@app.get("/anchors", response_class=HTMLResponse)
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
            "active_filters": request.query_params.get("filter", "").split(",")
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)    
