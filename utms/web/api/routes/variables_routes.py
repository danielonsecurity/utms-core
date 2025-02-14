from fastapi import APIRouter
from . import config, units, anchors

routers = [
    config.router,
    units.router,
    anchors.router
]
