from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import Config
from utms.web.api import templates
from utms.web.dependencies import get_config

router = APIRouter()


@router.get("/api/config", response_class=JSONResponse)
async def get_config_data(config: Config = Depends(get_config)):
    return config.config


@router.put("/api/config/{key}", response_class=JSONResponse)
async def update_config(key: str, value: str = Body(...), config: Config = Depends(get_config)):
    try:
        config.config[key] = value
        config.config.save()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
