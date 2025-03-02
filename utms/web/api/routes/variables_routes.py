from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import Config
from utms.web.api import templates

config = Config()
router = APIRouter()


@router.get("/variables", response_class=HTMLResponse)
async def variables_page(request: Request):
    variables_data = {}
    for var_name, var_prop in config.variables.items():
        variables_data[var_name] = {
            "value": str(var_prop.value),
            "value_original": var_prop.original,
            "type": type(var_prop.value).__name__,
        }

    return templates.TemplateResponse(
        "variables.html",
        {"request": request, "active_page": "variables", "variables": variables_data},
    )


@router.get("/api/variables", response_class=JSONResponse)
async def get_variables():
    variables_data = {}
    for var_name, var_prop in config.variables.items():
        variables_data[var_name] = {
            "value": str(var_prop.value),
            "value_original": var_prop.original,
            "type": type(var_prop.value).__name__,
        }
    return variables_data
