from fastapi import APIRouter, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from utms.web.api.models import config
from utms.web.api import templates

router = APIRouter()

@router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    return templates.TemplateResponse(
        "config.html", 
        {"request": request, "config": config.data, "active_page": "config"}
    )


@router.get("/api/config")
async def get_config():
    return config.data

@router.put("/{key}")
async def update_config(key: str, value: str=Body(...)):
    try:
        config.set_value(key, value)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
