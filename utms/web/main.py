from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from utms.web.api.routes import config_routes, units_routes, anchors_routes, variables_routes, resolve_routes, clock_routes
import uvicorn

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="utms/web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="utms/web/templates")

# Include routers
app.include_router(config_routes.router)
app.include_router(config_routes.router, prefix="/api/config", tags=["config"])
app.include_router(units_routes.router)
app.include_router(units_routes.router, prefix="/api/units", tags=["units"])
app.include_router(anchors_routes.router)
app.include_router(anchors_routes.router, prefix="/api/anchors", tags=["anchors"])
app.include_router(variables_routes.router)
app.include_router(variables_routes.router, prefix="/api/variables", tags=["variables"])
app.include_router(resolve_routes.router)
app.include_router(resolve_routes.router, prefix="/api/resolve", tags=["resolve"])
app.include_router(clock_routes.router)
app.include_router(clock_routes.router, prefix="/api/clock", tags=["clock"])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
