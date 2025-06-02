from .auth import router as auth_router
from .report import router as report_router
from .search import router as search_router
from .servers import router as servers_router
from .user import router as user_router
from .webhook import router as webhook_router

__all__ = [
    "auth_router",
    "report_router",
    "search_router",
    "servers_router",
    "user_router",
    "webhook_router",
]
