from __future__ import annotations

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from fastapi import FastAPI

from backend.dynamic_api import bind_app, register_all_tools
from backend.endpoints import (
    create_dashboard_router,
    create_health_router,
    create_query_router,
    create_tools_router,
)
from backend.service import AutoForgeBackendService


service = AutoForgeBackendService()


def create_app() -> FastAPI:
    app = FastAPI(title="AutoForge Backend", version="0.1.0")
    bind_app(app)

    @app.on_event("startup")
    def _startup() -> None:
        service.sync()
        register_all_tools(service.registry.all_tools())

    app.include_router(create_dashboard_router(service))
    app.include_router(create_health_router(service))
    app.include_router(create_tools_router(service))
    app.include_router(create_query_router(service))
    return app


app = create_app()
