from fastapi import APIRouter

from . import anchors_routes, clock_routes, config_routes, resolve_routes, units_routes

routers = [
    config_routes.router,
    units_routes.router,
    anchors_routes.router,
    resolve_routes.router,
    clock_routes.router,
]
