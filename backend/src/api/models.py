from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Role(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class ActionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"


# Employee Models
class Employee(BaseModel):
    id: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    role: Role
    manager_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: date
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EmployeeCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: Role = Role.EMPLOYEE
    manager_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: date


class EmployeeUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[Role] = None
    manager_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: Role
    manager_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Work Log Models
class WorkLogAttachment(BaseModel):
    filename: str
    url: str
    uploaded_at: datetime = Field(default_factory=datetime.now)


class WorkLog(BaseModel):
    id: str
    employee_id: str
    date: date
    task_description: str
    time_spent: float  # hours
    status: TaskStatus
    project: Optional[str] = None
    category: Optional[str] = None
    attachments: List[WorkLogAttachment] = []
    notes: Optional[str] = None
    manager_feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    can_edit: bool = True


class WorkLogCreate(BaseModel):
    date: date
    task_description: str
    time_spent: float
    status: TaskStatus
    project: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class WorkLogUpdate(BaseModel):
    task_description: Optional[str] = None
    time_spent: Optional[float] = None
    status: Optional[TaskStatus] = None
    project: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


# Leave Request Models
class LeaveRequest(BaseModel):
    id: str
    employee_id: str
    start_date: date
    end_date: date
    leave_type: str
    reason: str
    status: LeaveStatus = LeaveStatus.PENDING
    manager_id: Optional[str] = None
    manager_comments: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    leave_type: str
    reason: str


class LeaveRequestUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    leave_type: Optional[str] = None
    reason: Optional[str] = None


class LeaveRequestApproval(BaseModel):
    status: LeaveStatus
    manager_comments: Optional[str] = None


# Feedback Models
class Feedback(BaseModel):
    id: str
    work_log_id: str
    employee_id: str
    manager_id: str
    feedback_text: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FeedbackCreate(BaseModel):
    work_log_id: str
    feedback_text: str
    rating: Optional[int] = Field(None, ge=1, le=5)


# Audit Trail Models
class AuditTrail(BaseModel):
    id: str
    user_id: str
    action: ActionType
    resource_type: str
    resource_id: str
    details: dict
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Authentication Models
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: EmployeeResponse


class Token(BaseModel):
    access_token: str
    token_type: str


# Settings Models
class SystemSettings(BaseModel):
    id: str = "system_settings"
    log_edit_time_limit_hours: int = 24
    default_leave_types: List[str] = ["Sick Leave", "Vacation", "Personal", "Maternity/Paternity"]
    default_task_categories: List[str] = ["Development", "Testing", "Documentation", "Meetings", "Research"]
    notification_settings: dict = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SettingsUpdate(BaseModel):
    log_edit_time_limit_hours: Optional[int] = None
    default_leave_types: Optional[List[str]] = None
    default_task_categories: Optional[List[str]] = None
    notification_settings: Optional[dict] = None


# Dashboard/Report Models
class DashboardStats(BaseModel):
    total_employees: int
    active_employees: int
    pending_leave_requests: int
    recent_work_logs: int
    completion_rate: float


class ProductivityReport(BaseModel):
    employee_id: str
    employee_name: str
    total_hours: float
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    period_start: date
    period_end: date
