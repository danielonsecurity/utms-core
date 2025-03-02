from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.web.api import templates
from utms.core.config import Config

router = APIRouter()
config = Config()

@router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    return templates.TemplateResponse(
        "config.html", {"request": request, "config": config.data, "active_page": "config"}
    )


@router.get("/api/config", response_class=JSONResponse)
async def get_config():
    return config.data


@router.put("/api/config/{key}", response_class=JSONResponse)
async def update_config(key: str, value: str = Body(...)):
    try:
        config.set_value(key, value)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
