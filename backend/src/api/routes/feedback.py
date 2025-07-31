from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from ..models import Feedback, FeedbackCreate, Employee, ActionType
from ..storage import storage
from ..auth import get_current_user, get_manager_or_admin_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


# PUBLIC_INTERFACE
@router.post("/", response_model=Feedback, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user: Employee = Depends(get_manager_or_admin_user)
):
    """
    Create feedback for a work log entry.
    Only managers and admins can provide feedback.
    """
    # Verify work log exists and get employee info
    work_log = storage.get_work_log(feedback_data.work_log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Check if current user can provide feedback for this work log
    log_employee = storage.get_employee(work_log.employee_id)
    if not log_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Manager can only provide feedback for their direct reports
    if (current_user.role.value == "manager" and 
        log_employee.manager_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only provide feedback for your direct reports"
        )
    
    try:
        feedback = storage.create_feedback(current_user.id, feedback_data)
        
        # Log audit trail
        storage.create_audit_entry(
            user_id=current_user.id,
            action=ActionType.CREATE,
            resource_type="feedback",
            resource_id=feedback.id,
            details={
                "work_log_id": feedback.work_log_id,
                "employee_id": feedback.employee_id,
                "rating": feedback.rating
            }
        )
        
        return feedback
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# PUBLIC_INTERFACE
@router.get("/employee/{employee_id}", response_model=List[Feedback])
async def get_employee_feedback(
    employee_id: str,
    current_user: Employee = Depends(get_current_user)
):
    """
    Get all feedback for a specific employee.
    Users can see their own feedback, managers can see their reports' feedback, admins see all.
    """
    # Check permissions
    target_employee = storage.get_employee(employee_id)
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Permission check
    if (current_user.id != employee_id and
        current_user.role.value != "admin" and
        (current_user.role.value != "manager" or target_employee.manager_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this employee's feedback"
        )
    
    feedback_data = storage._read_json_file(storage.files["feedback"])
    employee_feedback = [
        Feedback(**fb_data) for fb_data in feedback_data
        if fb_data.get("employee_id") == employee_id
    ]
    
    return sorted(employee_feedback, key=lambda x: x.created_at, reverse=True)


# PUBLIC_INTERFACE
@router.get("/work-log/{work_log_id}", response_model=List[Feedback])
async def get_work_log_feedback(
    work_log_id: str,
    current_user: Employee = Depends(get_current_user)
):
    """
    Get feedback for a specific work log.
    """
    # Verify work log exists and check permissions
    work_log = storage.get_work_log(work_log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Check permissions - user can see feedback on their own logs, managers can see their reports'
    target_employee = storage.get_employee(work_log.employee_id)
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if (current_user.id != work_log.employee_id and
        current_user.role.value != "admin" and
        (current_user.role.value != "manager" or target_employee.manager_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view feedback for this work log"
        )
    
    feedback_data = storage._read_json_file(storage.files["feedback"])
    work_log_feedback = [
        Feedback(**fb_data) for fb_data in feedback_data
        if fb_data.get("work_log_id") == work_log_id
    ]
    
    return sorted(work_log_feedback, key=lambda x: x.created_at, reverse=True)


# PUBLIC_INTERFACE
@router.get("/my-feedback", response_model=List[Feedback])
async def get_my_feedback(current_user: Employee = Depends(get_current_user)):
    """
    Get all feedback received by the current user.
    """
    feedback_data = storage._read_json_file(storage.files["feedback"])
    my_feedback = [
        Feedback(**fb_data) for fb_data in feedback_data
        if fb_data.get("employee_id") == current_user.id
    ]
    
    return sorted(my_feedback, key=lambda x: x.created_at, reverse=True)


# PUBLIC_INTERFACE
@router.get("/given-feedback", response_model=List[Feedback])
async def get_given_feedback(
    current_user: Employee = Depends(get_manager_or_admin_user)
):
    """
    Get all feedback given by the current manager.
    Only managers and admins can access this endpoint.
    """
    feedback_data = storage._read_json_file(storage.files["feedback"])
    given_feedback = [
        Feedback(**fb_data) for fb_data in feedback_data
        if fb_data.get("manager_id") == current_user.id
    ]
    
    return sorted(given_feedback, key=lambda x: x.created_at, reverse=True)
