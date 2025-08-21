from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from utms.web.api.models import config

router = APIRouter()



@router.get("/")
async def get_clock_info():
    return {
        "status": "active",
        "default_settings": {
            "hourRotation": 43200,  # 12 hours in seconds
            "minuteRotation": 3600,  # 1 hour in seconds
            "secondRotation": 60,  # 1 minute in seconds
        },
    }
