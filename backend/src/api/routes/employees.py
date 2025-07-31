from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from ..models import (
    Employee, EmployeeCreate, EmployeeUpdate, EmployeeResponse, 
    Role, ActionType
)
from ..storage import storage
from ..auth import get_current_user, get_admin_user, can_access_employee_data

router = APIRouter(prefix="/employees", tags=["employees"])


# PUBLIC_INTERFACE
@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: Employee = Depends(get_admin_user)
):
    """
    Create a new employee record.
    Only administrators can create employee accounts.
    """
    try:
        employee = storage.create_employee(employee_data)
        
        # Log audit trail
        storage.create_audit_entry(
            user_id=current_user.id,
            action=ActionType.CREATE,
            resource_type="employee",
            resource_id=employee.id,
            details={"email": employee.email, "role": employee.role}
        )
        
        return EmployeeResponse(**employee.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# PUBLIC_INTERFACE
@router.get("/", response_model=List[EmployeeResponse])
async def get_all_employees(
    active_only: bool = True,
    current_user: Employee = Depends(get_admin_user)
):
    """
    Get all employees in the system.
    Only administrators can view all employees.
    """
    employees = storage.get_all_employees()
    
    if active_only:
        employees = [emp for emp in employees if emp.is_active]
    
    return [EmployeeResponse(**emp.model_dump()) for emp in employees]


# PUBLIC_INTERFACE  
@router.get("/me", response_model=EmployeeResponse)
async def get_current_employee(current_user: Employee = Depends(get_current_user)):
    """
    Get current user's employee information.
    """
    return EmployeeResponse(**current_user.model_dump())


# PUBLIC_INTERFACE
@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    current_user: Employee = Depends(get_current_user)
):
    """
    Get employee by ID.
    Users can only access their own data unless they are managers/admins.
    """
    if not can_access_employee_data(current_user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this employee's data"
        )
    
    employee = storage.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return EmployeeResponse(**employee.model_dump())


# PUBLIC_INTERFACE
@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_update: EmployeeUpdate,
    current_user: Employee = Depends(get_current_user)
):
    """
    Update employee information.
    Users can update their own basic info, managers can update their reports, admins can update anyone.
    """
    # Check permissions
    target_employee = storage.get_employee(employee_id)
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Role changes only allowed by admins
    if employee_update.role and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can change roles"
        )
    
    # Self-update or admin/manager permissions
    if not (current_user.id == employee_id or 
            current_user.role == Role.ADMIN or
            (current_user.role == Role.MANAGER and target_employee.manager_id == current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this employee"
        )
    
    # Perform update
    updates = employee_update.model_dump(exclude_unset=True)
    updated_employee = storage.update_employee(employee_id, updates)
    
    if not updated_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.UPDATE,
        resource_type="employee",
        resource_id=employee_id,
        details=updates
    )
    
    return EmployeeResponse(**updated_employee.model_dump())


# PUBLIC_INTERFACE
@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user: Employee = Depends(get_admin_user)
):
    """
    Soft delete employee (deactivate).
    Only administrators can delete employees.
    """
    if not storage.delete_employee(employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Log audit trail
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.DELETE,
        resource_type="employee",
        resource_id=employee_id,
        details={"action": "soft_delete"}
    )
    
    return {"message": "Employee deactivated successfully"}


# PUBLIC_INTERFACE
@router.get("/{manager_id}/direct-reports", response_model=List[EmployeeResponse])
async def get_direct_reports(
    manager_id: str,
    current_user: Employee = Depends(get_current_user)
):
    """
    Get direct reports for a manager.
    Managers can only see their own reports, admins can see anyone's reports.
    """
    if current_user.role != Role.ADMIN and current_user.id != manager_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these direct reports"
        )
    
    all_employees = storage.get_all_employees()
    direct_reports = [emp for emp in all_employees 
                     if emp.manager_id == manager_id and emp.is_active]
    
    return [EmployeeResponse(**emp.model_dump()) for emp in direct_reports]
