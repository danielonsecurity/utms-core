from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utms.web.api.routes import (
    anchors_routes,
    clock_routes,
    config_routes,
    resolve_routes,
    units_routes,
    variables_routes,
)
from utms.web.dependencies import get_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_config()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static files
app.mount("/static", StaticFiles(directory="utms/web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="utms/web/templates")

# Include routers
app.include_router(config_routes.router)
app.include_router(variables_routes.router)
app.include_router(anchors_routes.router)
app.include_router(units_routes.router)
app.include_router(clock_routes.router)
app.include_router(resolve_routes.router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
