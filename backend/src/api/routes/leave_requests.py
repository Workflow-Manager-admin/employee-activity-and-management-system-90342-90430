from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
from ..models import (
    LeaveRequest, LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestApproval,
    Employee, LeaveStatus, ActionType
)
from ..storage import storage
from ..auth import get_current_user, can_approve_leave

router = APIRouter(prefix="/leave-requests", tags=["leave-requests"])


# PUBLIC_INTERFACE
@router.post("/", response_model=LeaveRequest, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    current_user: Employee = Depends(get_current_user)
):
    """
    Create a new leave request for the current user.
    """
    try:
        # Validate dates
        if leave_data.start_date > leave_data.end_date:
            raise HTTPException(
                status_code=400, 
                detail="Start date must be before or equal to end date"
            )
        
        leave_request = storage.create_leave_request(current_user.id, leave_data)
        
        # Log audit trail
        storage.create_audit_entry(
            user_id=current_user.id,
            action=ActionType.CREATE,
            resource_type="leave_request",
            resource_id=leave_request.id,
            details={
                "start_date": leave_request.start_date.isoformat(),
                "end_date": leave_request.end_date.isoformat(),
                "leave_type": leave_request.leave_type
            }
        )
        
        return leave_request
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# PUBLIC_INTERFACE
@router.get("/", response_model=List[LeaveRequest])
async def get_leave_requests(
    status_filter: Optional[LeaveStatus] = None,
    current_user: Employee = Depends(get_current_user)
):
    """
    Get leave requests for the current user.
    """
    leave_requests = storage.get_leave_requests_by_employee(current_user.id)
    
    if status_filter:
        leave_requests = [req for req in leave_requests if req.status == status_filter]
    
    return sorted(leave_requests, key=lambda x: x.created_at, reverse=True)


# PUBLIC_INTERFACE
@router.get("/pending-approvals", response_model=List[LeaveRequest])
async def get_pending_approvals(
    current_user: Employee = Depends(get_current_user)
):
    """
    Get leave requests pending approval for the current manager.
    Only managers and admins can access this endpoint.
    """
    if current_user.role.value not in ["manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can view pending approvals"
        )
    
    if current_user.role.value == "admin":
        # Admin can see all pending requests
        all_requests = storage._read_json_file(storage.files["leave_requests"])
        pending_requests = [
            LeaveRequest(**req_data) for req_data in all_requests
            if req_data.get("status") == LeaveStatus.PENDING
        ]
    else:
        # Manager sees only their direct reports' requests
        pending_requests = storage.get_leave_requests_by_manager(current_user.id)
        pending_requests = [req for req in pending_requests if req.status == LeaveStatus.PENDING]
    
    return sorted(pending_requests, key=lambda x: x.created_at)


# PUBLIC_INTERFACE
@router.get("/{request_id}", response_model=LeaveRequest)
async def get_leave_request(
    request_id: str,
    current_user: Employee = Depends(get_current_user)
):
    """
    Get a specific leave request by ID.
    """
    leave_request = storage.get_leave_request(request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions - user can see their own, manager can see their reports', admin sees all
    if (leave_request.employee_id != current_user.id and
        leave_request.manager_id != current_user.id and
        current_user.role.value != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this leave request"
        )
    
    return leave_request


# PUBLIC_INTERFACE
@router.put("/{request_id}", response_model=LeaveRequest)
async def update_leave_request(
    request_id: str,
    leave_update: LeaveRequestUpdate,
    current_user: Employee = Depends(get_current_user)
):
    """
    Update a leave request.
    Only the owner can update, and only if status is still pending.
    """
    leave_request = storage.get_leave_request(request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if leave_request.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own leave requests"
        )
    
    # Check if still pending
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Cannot update leave request that has already been processed"
        )
    
    # Validate dates if provided
    updates = leave_update.model_dump(exclude_unset=True)
    if "start_date" in updates or "end_date" in updates:
        start_date = updates.get("start_date", leave_request.start_date)
        end_date = updates.get("end_date", leave_request.end_date)
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before or equal to end date"
            )
    
    # Perform update
    updated_request = storage.update_leave_request(request_id, updates)
    if not updated_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.UPDATE,
        resource_type="leave_request",
        resource_id=request_id,
        details=updates
    )
    
    return updated_request


# PUBLIC_INTERFACE
@router.post("/{request_id}/approve", response_model=LeaveRequest)
async def approve_or_reject_leave_request(
    request_id: str,
    approval_data: LeaveRequestApproval,
    current_user: Employee = Depends(get_current_user)
):
    """
    Approve or reject a leave request.
    Only managers can approve their direct reports' requests, admins can approve any.
    """
    leave_request = storage.get_leave_request(request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if not can_approve_leave(current_user, leave_request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to approve this leave request"
        )
    
    # Check if still pending
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Leave request has already been processed"
        )
    
    # Update request with approval decision
    updates = {
        "status": approval_data.status,
        "manager_comments": approval_data.manager_comments,
        "approved_by": current_user.id,
        "approved_at": datetime.now().isoformat()
    }
    
    updated_request = storage.update_leave_request(request_id, updates)
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.APPROVE if approval_data.status == LeaveStatus.APPROVED else ActionType.REJECT,
        resource_type="leave_request",
        resource_id=request_id,
        details={
            "status": approval_data.status,
            "comments": approval_data.manager_comments
        }
    )
    
    return updated_request


# PUBLIC_INTERFACE
@router.delete("/{request_id}")
async def cancel_leave_request(
    request_id: str,
    current_user: Employee = Depends(get_current_user)
):
    """
    Cancel a leave request.
    Only the owner can cancel, and only if status is still pending.
    """
    leave_request = storage.get_leave_request(request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if leave_request.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only cancel your own leave requests"
        )
    
    # Check if still pending
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel leave request that has already been processed"
        )
    
    # Mark as rejected (cancelled)
    updates = {
        "status": LeaveStatus.REJECTED,
        "manager_comments": "Cancelled by employee",
        "approved_by": current_user.id,
        "approved_at": datetime.now().isoformat()
    }
    
    storage.update_leave_request(request_id, updates)
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.DELETE,
        resource_type="leave_request",
        resource_id=request_id,
        details={"action": "cancelled"}
    )
    
    return {"message": "Leave request cancelled successfully"}
