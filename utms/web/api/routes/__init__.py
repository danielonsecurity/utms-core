from fastapi import APIRouter
from . import config_routes, units_routes, anchors_routes

routers = [
    config_routes.router,
    units_routes.router,
    anchors_routes.router
]
