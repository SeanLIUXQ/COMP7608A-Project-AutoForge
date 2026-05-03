from backend.endpoints.dashboard import create_dashboard_router
from backend.endpoints.health import create_health_router
from backend.endpoints.query import create_query_router
from backend.endpoints.tools import create_tools_router

__all__ = [
    "create_dashboard_router",
    "create_health_router",
    "create_query_router",
    "create_tools_router",
]
