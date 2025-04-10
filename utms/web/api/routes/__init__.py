from fastapi import APIRouter

from . import (
    anchors_routes,
    clock_routes,
    config_routes,
    dynamic_routes,
    resolve_routes,
    units_routes,
    variables_routes,
)

routers = [
    dynamic_routes.router,
    config_routes.router,
    variables_routes.router,
    units_routes.router,
    anchors_routes.router,
    clock_routes.router,
    resolve_routes.router,
]
