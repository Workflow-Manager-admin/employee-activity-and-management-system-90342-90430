from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import (
    auth_router,
    employees_router,
    work_logs_router,
    leave_requests_router,
    feedback_router,
    admin_router
)

# FastAPI app configuration
app = FastAPI(
    title="Employee Activity and Management System API",
    description="""
    A comprehensive API for employee activity tracking, work log management, 
    leave requests, feedback, and administrative functions.
    
    ## Features
    
    - **Authentication**: Secure JWT-based authentication
    - **Employee Management**: CRUD operations for employee records
    - **Work Logs**: Daily activity tracking with time limits and status management
    - **Leave Requests**: Leave application and approval workflow
    - **Feedback**: Manager feedback on employee work logs
    - **Admin Panel**: System settings, audit trails, and reporting
    - **Role-based Access**: Employee, Manager, and Admin role permissions
    
    ## Authentication
    
    Most endpoints require authentication. Use the `/auth/login` endpoint to obtain
    a JWT token, then include it in the Authorization header as `Bearer <token>`.
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Login, logout, and token verification"
        },
        {
            "name": "employees", 
            "description": "Employee CRUD operations and management"
        },
        {
            "name": "work-logs",
            "description": "Daily work log entry and management"
        },
        {
            "name": "leave-requests",
            "description": "Leave request submission and approval workflow"
        },
        {
            "name": "feedback",
            "description": "Manager feedback on employee work logs"
        },
        {
            "name": "admin",
            "description": "Administrative functions, settings, and reports"
        }
    ]
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(work_logs_router)
app.include_router(leave_requests_router)
app.include_router(feedback_router)
app.include_router(admin_router)


# PUBLIC_INTERFACE
@app.get("/", tags=["health"])
def health_check():
    """
    Health check endpoint to verify API availability.
    Returns basic service status information.
    """
    return {
        "message": "Employee Activity and Management System API",
        "status": "healthy",
        "version": "1.0.0"
    }


# PUBLIC_INTERFACE
@app.get("/health", tags=["health"])
def detailed_health_check():
    """
    Detailed health check with system information.
    Provides comprehensive service status for monitoring.
    """
    from datetime import datetime
    from .storage import storage
    
    try:
        # Test storage connectivity
        storage.get_settings()
        storage_healthy = True
    except Exception:
        storage_healthy = False
    
    return {
        "status": "healthy" if storage_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "healthy",
            "storage": "healthy" if storage_healthy else "unhealthy"
        },
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
