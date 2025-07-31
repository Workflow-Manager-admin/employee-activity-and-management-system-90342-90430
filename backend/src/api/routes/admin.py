from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from ..models import (
    Employee, SystemSettings, SettingsUpdate, AuditTrail, DashboardStats,
    ActionType
)
from ..storage import storage
from ..auth import get_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


# PUBLIC_INTERFACE
@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: Employee = Depends(get_admin_user)):
    """
    Get dashboard statistics for admin overview.
    Only administrators can access this endpoint.
    """
    all_employees = storage.get_all_employees()
    all_leave_requests = storage._read_json_file(storage.files["leave_requests"])
    all_work_logs = storage._read_json_file(storage.files["work_logs"])
    
    # Calculate stats
    total_employees = len(all_employees)
    active_employees = len([emp for emp in all_employees if emp.is_active])
    
    pending_leave_requests = len([
        req for req in all_leave_requests 
        if req.get("status") == "pending"
    ])
    
    # Recent work logs (last 7 days)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_work_logs = len([
        log for log in all_work_logs
        if datetime.fromisoformat(log.get("created_at", "")) > seven_days_ago
    ])
    
    # Calculate completion rate
    if all_work_logs:
        completed_logs = len([
            log for log in all_work_logs
            if log.get("status") == "completed"
        ])
        completion_rate = completed_logs / len(all_work_logs)
    else:
        completion_rate = 0.0
    
    return DashboardStats(
        total_employees=total_employees,
        active_employees=active_employees,
        pending_leave_requests=pending_leave_requests,
        recent_work_logs=recent_work_logs,
        completion_rate=completion_rate
    )


# PUBLIC_INTERFACE
@router.get("/audit-trails", response_model=List[AuditTrail])
async def get_audit_trails(
    limit: int = Query(100, le=1000),
    user_id: Optional[str] = Query(None),
    action: Optional[ActionType] = Query(None),
    resource_type: Optional[str] = Query(None),
    current_user: Employee = Depends(get_admin_user)
):
    """
    Get audit trail entries with optional filtering.
    Only administrators can access audit trails.
    """
    audit_trails = storage._read_json_file(storage.files["audit_trails"])
    
    # Apply filters
    filtered_trails = audit_trails
    
    if user_id:
        filtered_trails = [t for t in filtered_trails if t.get("user_id") == user_id]
    
    if action:
        filtered_trails = [t for t in filtered_trails if t.get("action") == action]
    
    if resource_type:
        filtered_trails = [t for t in filtered_trails if t.get("resource_type") == resource_type]
    
    # Sort by timestamp (newest first) and limit
    sorted_trails = sorted(
        filtered_trails, 
        key=lambda x: x.get("timestamp", ""), 
        reverse=True
    )[:limit]
    
    return [AuditTrail(**trail_data) for trail_data in sorted_trails]


# PUBLIC_INTERFACE
@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(current_user: Employee = Depends(get_admin_user)):
    """
    Get current system settings.
    Only administrators can access system settings.
    """
    return storage.get_settings()


# PUBLIC_INTERFACE
@router.put("/settings", response_model=SystemSettings)
async def update_system_settings(
    settings_update: SettingsUpdate,
    current_user: Employee = Depends(get_admin_user)
):
    """
    Update system settings.
    Only administrators can modify system settings.
    """
    updates = settings_update.model_dump(exclude_unset=True)
    updated_settings = storage.update_settings(updates)
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.UPDATE,
        resource_type="system_settings",
        resource_id="system_settings",
        details=updates
    )
    
    return updated_settings


# PUBLIC_INTERFACE
@router.post("/bulk-create-employees")
async def bulk_create_employees(
    employees_data: List[dict],
    current_user: Employee = Depends(get_admin_user)
):
    """
    Bulk create employees from CSV/JSON data.
    Only administrators can perform bulk operations.
    """
    created_employees = []
    errors = []
    
    for i, emp_data in enumerate(employees_data):
        try:
            # Validate required fields
            required_fields = ["email", "password", "first_name", "last_name", "hire_date"]
            for field in required_fields:
                if field not in emp_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create employee
            from ..models import EmployeeCreate
            employee_create = EmployeeCreate(**emp_data)
            employee = storage.create_employee(employee_create)
            created_employees.append(employee.id)
            
        except Exception as e:
            errors.append({
                "row": i + 1,
                "email": emp_data.get("email", "unknown"),
                "error": str(e)
            })
    
    # Log bulk operation
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.CREATE,
        resource_type="bulk_employees",
        resource_id="bulk_operation",
        details={
            "total_processed": len(employees_data),
            "successful": len(created_employees),
            "errors": len(errors)
        }
    )
    
    return {
        "message": "Bulk operation completed",
        "successful": len(created_employees),
        "errors": len(errors),
        "created_employee_ids": created_employees,
        "error_details": errors
    }


# PUBLIC_INTERFACE
@router.get("/reports/productivity")
async def get_productivity_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    current_user: Employee = Depends(get_admin_user)
):
    """
    Generate productivity report for all employees.
    Only administrators can access organization-wide reports.
    """
    from datetime import datetime
    
    # Parse dates
    start_dt = datetime.fromisoformat(start_date).date() if start_date else None
    end_dt = datetime.fromisoformat(end_date).date() if end_date else None
    
    all_employees = storage.get_all_employees()
    
    # Filter by department if specified
    if department:
        all_employees = [emp for emp in all_employees if emp.department == department]
    
    report_data = []
    
    for employee in all_employees:
        if not employee.is_active:
            continue
            
        work_logs = storage.get_work_logs_by_employee(employee.id, start_dt, end_dt)
        
        total_hours = sum(log.time_spent for log in work_logs)
        completed_tasks = len([log for log in work_logs if log.status.value == "completed"])
        in_progress_tasks = len([log for log in work_logs if log.status.value == "in_progress"])
        blocked_tasks = len([log for log in work_logs if log.status.value == "blocked"])
        
        report_data.append({
            "employee_id": employee.id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "department": employee.department,
            "total_hours": total_hours,
            "total_logs": len(work_logs),
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "blocked_tasks": blocked_tasks,
            "completion_rate": completed_tasks / len(work_logs) if work_logs else 0
        })
    
    return {
        "report_period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "filters": {
            "department": department
        },
        "employees": report_data,
        "summary": {
            "total_employees": len(report_data),
            "total_hours": sum(emp["total_hours"] for emp in report_data),
            "average_completion_rate": sum(emp["completion_rate"] for emp in report_data) / len(report_data) if report_data else 0
        }
    }
