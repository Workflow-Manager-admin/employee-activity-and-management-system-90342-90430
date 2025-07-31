from .auth import router as auth_router
from .employees import router as employees_router
from .work_logs import router as work_logs_router
from .leave_requests import router as leave_requests_router
from .feedback import router as feedback_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "employees_router", 
    "work_logs_router",
    "leave_requests_router",
    "feedback_router",
    "admin_router"
]
