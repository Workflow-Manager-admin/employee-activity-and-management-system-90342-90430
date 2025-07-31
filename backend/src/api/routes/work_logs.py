from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import date, datetime, timedelta
from ..models import (
    WorkLog, WorkLogCreate, WorkLogUpdate, Employee, ActionType
)
from ..storage import storage
from ..auth import get_current_user, can_access_employee_data

router = APIRouter(prefix="/work-logs", tags=["work-logs"])


def can_edit_work_log(work_log: WorkLog, current_user: Employee) -> bool:
    """Check if user can edit a work log based on time limits and permissions."""
    # Admin can edit any log
    if current_user.role.value == "admin":
        return True
    
    # Owner check
    if work_log.employee_id != current_user.id:
        return False
    
    # Check time limit
    settings = storage.get_settings()
    time_limit = timedelta(hours=settings.log_edit_time_limit_hours)
    
    if datetime.now() - work_log.created_at > time_limit:
        return False
    
    return True


# PUBLIC_INTERFACE
@router.post("/", response_model=WorkLog, status_code=status.HTTP_201_CREATED)
async def create_work_log(
    log_data: WorkLogCreate,
    current_user: Employee = Depends(get_current_user)
):
    """
    Create a new work log entry for the current user.
    """
    try:
        work_log = storage.create_work_log(current_user.id, log_data)
        
        # Log audit trail
        storage.create_audit_entry(
            user_id=current_user.id,
            action=ActionType.CREATE,
            resource_type="work_log",
            resource_id=work_log.id,
            details={
                "date": work_log.date.isoformat(),
                "task_description": work_log.task_description,
                "time_spent": work_log.time_spent
            }
        )
        
        return work_log
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# PUBLIC_INTERFACE
@router.get("/", response_model=List[WorkLog])
async def get_work_logs(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: Employee = Depends(get_current_user)
):
    """
    Get work logs with optional filtering.
    Users can see their own logs, managers can see their reports' logs, admins see all.
    """
    # Determine target employee
    target_employee_id = employee_id if employee_id else current_user.id
    
    # Check permissions
    if not can_access_employee_data(current_user, target_employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these work logs"
        )
    
    work_logs = storage.get_work_logs_by_employee(
        target_employee_id, start_date, end_date
    )
    
    # Update can_edit flag based on current user and time limits
    for log in work_logs:
        log.can_edit = can_edit_work_log(log, current_user)
    
    return work_logs


# PUBLIC_INTERFACE
@router.get("/{log_id}", response_model=WorkLog)
async def get_work_log(
    log_id: str,
    current_user: Employee = Depends(get_current_user)
):
    """
    Get a specific work log by ID.
    """
    work_log = storage.get_work_log(log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Check permissions
    if not can_access_employee_data(current_user, work_log.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this work log"
        )
    
    # Set can_edit flag
    work_log.can_edit = can_edit_work_log(work_log, current_user)
    
    return work_log


# PUBLIC_INTERFACE
@router.put("/{log_id}", response_model=WorkLog)
async def update_work_log(
    log_id: str,
    log_update: WorkLogUpdate,
    current_user: Employee = Depends(get_current_user)
):
    """
    Update a work log entry.
    Only the owner can edit within the time limit, unless user is admin.
    """
    work_log = storage.get_work_log(log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Check edit permissions
    if not can_edit_work_log(work_log, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit this work log (time limit exceeded or insufficient permissions)"
        )
    
    # Perform update
    updates = log_update.model_dump(exclude_unset=True)
    updated_log = storage.update_work_log(log_id, updates)
    
    if not updated_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.UPDATE,
        resource_type="work_log",
        resource_id=log_id,
        details=updates
    )
    
    updated_log.can_edit = can_edit_work_log(updated_log, current_user)
    return updated_log


# PUBLIC_INTERFACE
@router.post("/{log_id}/feedback")
async def add_feedback_to_log(
    log_id: str,
    feedback_text: str,
    rating: Optional[int] = None,
    current_user: Employee = Depends(get_current_user)
):
    """
    Add manager feedback to a work log.
    Only managers can provide feedback to their direct reports' logs.
    """
    work_log = storage.get_work_log(log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Check if current user is manager of the log owner
    log_owner = storage.get_employee(work_log.employee_id)
    if not log_owner:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if (current_user.role.value != "admin" and 
        (current_user.role.value != "manager" or log_owner.manager_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to provide feedback on this work log"
        )
    
    # Update work log with feedback
    updates = {"manager_feedback": feedback_text}
    storage.update_work_log(log_id, updates)
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.UPDATE,
        resource_type="work_log",
        resource_id=log_id,
        details={"action": "add_feedback", "feedback": feedback_text}
    )
    
    return {"message": "Feedback added successfully"}


# PUBLIC_INTERFACE
@router.get("/reports/summary")
async def get_work_summary(
    employee_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: Employee = Depends(get_current_user)
):
    """
    Get work summary statistics for an employee.
    """
    target_employee_id = employee_id if employee_id else current_user.id
    
    # Check permissions
    if not can_access_employee_data(current_user, target_employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this employee's data"
        )
    
    work_logs = storage.get_work_logs_by_employee(
        target_employee_id, start_date, end_date
    )
    
    # Calculate summary statistics
    total_hours = sum(log.time_spent for log in work_logs)
    completed_tasks = len([log for log in work_logs if log.status.value == "completed"])
    in_progress_tasks = len([log for log in work_logs if log.status.value == "in_progress"])
    blocked_tasks = len([log for log in work_logs if log.status.value == "blocked"])
    
    return {
        "employee_id": target_employee_id,
        "total_hours": total_hours,
        "total_logs": len(work_logs),
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "blocked_tasks": blocked_tasks,
        "period_start": start_date,
        "period_end": end_date
    }
