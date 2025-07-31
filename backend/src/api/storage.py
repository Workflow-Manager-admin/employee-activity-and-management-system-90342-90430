import json
import fcntl
import uuid
from datetime import datetime, date
from typing import List, Dict, Any, Optional, TypeVar
from pathlib import Path
import hashlib
from contextlib import contextmanager

T = TypeVar('T')

class JSONStorage:
    """
    Thread-safe JSON storage manager for persistent data operations.
    Provides ACID-like guarantees using file locks and atomic writes.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize data files with empty structures if they don't exist
        self.files = {
            "employees": self.data_dir / "employees.json",
            "work_logs": self.data_dir / "work_logs.json", 
            "leave_requests": self.data_dir / "leave_requests.json",
            "feedback": self.data_dir / "feedback.json",
            "audit_trails": self.data_dir / "audit_trails.json",
            "settings": self.data_dir / "settings.json"
        }
        
        # Initialize empty files
        for file_path in self.files.values():
            if not file_path.exists():
                self._write_json_file(file_path, [])
    
    @contextmanager
    def _file_lock(self, file_path: Path):
        """Context manager for file locking to ensure atomic operations."""
        with open(file_path, 'r+') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                yield f
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _read_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Safely read JSON file with error handling."""
        try:
            if not file_path.exists():
                return []
            
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            # Backup corrupted file and return empty list
            backup_path = file_path.with_suffix(f".backup_{datetime.now().isoformat()}")
            file_path.rename(backup_path)
            return []
        except Exception:
            return []
    
    def _write_json_file(self, file_path: Path, data: List[Dict[str, Any]]):
        """Atomically write JSON file."""
        temp_path = file_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, default=self._json_serializer)
            temp_path.replace(file_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _generate_id(self) -> str:
        """Generate unique ID for entities."""
        return str(uuid.uuid4())
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return hashlib.sha256(password.encode()).hexdigest() == hashed

    # Employee operations
    def create_employee(self, employee_data) -> dict:
        """Create a new employee record."""
        with self._file_lock(self.files["employees"]):
            employees = self._read_json_file(self.files["employees"])
            
            # Check if email already exists
            if any(emp.get("email") == employee_data.email for emp in employees):
                raise ValueError("Employee with this email already exists")
            
            employee = {
                "id": self._generate_id(),
                "email": employee_data.email,
                "password_hash": self._hash_password(employee_data.password),
                "first_name": employee_data.first_name,
                "last_name": employee_data.last_name,
                "role": employee_data.role.value if hasattr(employee_data.role, 'value') else employee_data.role,
                "manager_id": employee_data.manager_id,
                "department": employee_data.department,
                "position": employee_data.position,
                "hire_date": employee_data.hire_date.isoformat() if hasattr(employee_data.hire_date, 'isoformat') else employee_data.hire_date,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            employees.append(employee)
            self._write_json_file(self.files["employees"], employees)
            
            # Return object that can be used like Employee model
            from .models import Employee
            return Employee(**employee)
    
    def get_employee(self, employee_id: str):
        """Get employee by ID."""
        employees = self._read_json_file(self.files["employees"])
        for emp_data in employees:
            if emp_data.get("id") == employee_id:
                from .models import Employee
                return Employee(**emp_data)
        return None
    
    def get_employee_by_email(self, email: str):
        """Get employee by email."""
        employees = self._read_json_file(self.files["employees"])
        for emp_data in employees:
            if emp_data.get("email") == email:
                from .models import Employee
                return Employee(**emp_data)
        return None
    
    def get_all_employees(self) -> List:
        """Get all employees."""
        employees = self._read_json_file(self.files["employees"])
        from .models import Employee
        return [Employee(**emp_data) for emp_data in employees]
    
    def update_employee(self, employee_id: str, updates: dict):
        """Update employee record."""
        with self._file_lock(self.files["employees"]):
            employees = self._read_json_file(self.files["employees"])
            
            for i, emp_data in enumerate(employees):
                if emp_data.get("id") == employee_id:
                    # Update fields
                    for key, value in updates.items():
                        if value is not None:
                            if hasattr(value, 'value'):  # Enum handling
                                emp_data[key] = value.value
                            elif hasattr(value, 'isoformat'):  # Date handling
                                emp_data[key] = value.isoformat()
                            else:
                                emp_data[key] = value
                    emp_data["updated_at"] = datetime.now().isoformat()
                    
                    employees[i] = emp_data
                    self._write_json_file(self.files["employees"], employees)
                    from .models import Employee
                    return Employee(**emp_data)
            return None
    
    def delete_employee(self, employee_id: str) -> bool:
        """Soft delete employee (set inactive)."""
        return self.update_employee(employee_id, {"is_active": False}) is not None

    # Work Log operations
    def create_work_log(self, employee_id: str, log_data) -> dict:
        """Create a new work log entry."""
        with self._file_lock(self.files["work_logs"]):
            work_logs = self._read_json_file(self.files["work_logs"])
            
            work_log = {
                "id": self._generate_id(),
                "employee_id": employee_id,
                "date": log_data.date.isoformat() if hasattr(log_data.date, 'isoformat') else log_data.date,
                "task_description": log_data.task_description,
                "time_spent": log_data.time_spent,
                "status": log_data.status.value if hasattr(log_data.status, 'value') else log_data.status,
                "project": log_data.project,
                "category": log_data.category,
                "attachments": [],
                "notes": log_data.notes,
                "manager_feedback": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "can_edit": True
            }
            
            work_logs.append(work_log)
            self._write_json_file(self.files["work_logs"], work_logs)
            
            from .models import WorkLog
            return WorkLog(**work_log)
    
    def get_work_log(self, log_id: str):
        """Get work log by ID."""
        work_logs = self._read_json_file(self.files["work_logs"])
        for log_data in work_logs:
            if log_data.get("id") == log_id:
                from .models import WorkLog
                return WorkLog(**log_data)
        return None
    
    def get_work_logs_by_employee(self, employee_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List:
        """Get work logs for an employee with optional date filtering."""
        work_logs = self._read_json_file(self.files["work_logs"])
        filtered_logs = []
        
        for log_data in work_logs:
            if log_data.get("employee_id") == employee_id:
                log_date_str = log_data.get("date")
                if log_date_str:
                    try:
                        log_date = datetime.fromisoformat(log_date_str).date()
                    except:
                        continue
                    
                    if start_date and log_date < start_date:
                        continue
                    if end_date and log_date > end_date:
                        continue
                        
                    from .models import WorkLog
                    filtered_logs.append(WorkLog(**log_data))
        
        return sorted(filtered_logs, key=lambda x: x.date, reverse=True)
    
    def update_work_log(self, log_id: str, updates: dict):
        """Update work log entry."""
        with self._file_lock(self.files["work_logs"]):
            work_logs = self._read_json_file(self.files["work_logs"])
            
            for i, log_data in enumerate(work_logs):
                if log_data.get("id") == log_id:
                    for key, value in updates.items():
                        if value is not None:
                            if hasattr(value, 'value'):  # Enum handling
                                log_data[key] = value.value
                            elif hasattr(value, 'isoformat'):  # Date handling
                                log_data[key] = value.isoformat()
                            else:
                                log_data[key] = value
                    log_data["updated_at"] = datetime.now().isoformat()
                    
                    work_logs[i] = log_data
                    self._write_json_file(self.files["work_logs"], work_logs)
                    from .models import WorkLog
                    return WorkLog(**log_data)
            return None

    # Leave Request operations
    def create_leave_request(self, employee_id: str, leave_data) -> dict:
        """Create a new leave request."""
        with self._file_lock(self.files["leave_requests"]):
            leave_requests = self._read_json_file(self.files["leave_requests"])
            
            # Get employee to find manager
            employee = self.get_employee(employee_id)
            
            leave_request = {
                "id": self._generate_id(),
                "employee_id": employee_id,
                "start_date": leave_data.start_date.isoformat() if hasattr(leave_data.start_date, 'isoformat') else leave_data.start_date,
                "end_date": leave_data.end_date.isoformat() if hasattr(leave_data.end_date, 'isoformat') else leave_data.end_date,
                "leave_type": leave_data.leave_type,
                "reason": leave_data.reason,
                "status": "pending",
                "manager_id": employee.manager_id if employee else None,
                "manager_comments": None,
                "approved_by": None,
                "approved_at": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            leave_requests.append(leave_request)
            self._write_json_file(self.files["leave_requests"], leave_requests)
            
            from .models import LeaveRequest
            return LeaveRequest(**leave_request)
    
    def get_leave_request(self, request_id: str):
        """Get leave request by ID."""
        leave_requests = self._read_json_file(self.files["leave_requests"])
        for req_data in leave_requests:
            if req_data.get("id") == request_id:
                from .models import LeaveRequest
                return LeaveRequest(**req_data)
        return None
    
    def get_leave_requests_by_employee(self, employee_id: str) -> List:
        """Get leave requests for an employee."""
        leave_requests = self._read_json_file(self.files["leave_requests"])
        from .models import LeaveRequest
        return [LeaveRequest(**req_data) for req_data in leave_requests 
                if req_data.get("employee_id") == employee_id]
    
    def get_leave_requests_by_manager(self, manager_id: str) -> List:
        """Get leave requests that need approval from a manager."""
        leave_requests = self._read_json_file(self.files["leave_requests"])
        from .models import LeaveRequest
        return [LeaveRequest(**req_data) for req_data in leave_requests 
                if req_data.get("manager_id") == manager_id]
    
    def update_leave_request(self, request_id: str, updates: dict):
        """Update leave request."""
        with self._file_lock(self.files["leave_requests"]):
            leave_requests = self._read_json_file(self.files["leave_requests"])
            
            for i, req_data in enumerate(leave_requests):
                if req_data.get("id") == request_id:
                    for key, value in updates.items():
                        if value is not None:
                            if hasattr(value, 'value'):  # Enum handling
                                req_data[key] = value.value
                            elif hasattr(value, 'isoformat'):  # Date handling
                                req_data[key] = value.isoformat()
                            else:
                                req_data[key] = value
                    req_data["updated_at"] = datetime.now().isoformat()
                    
                    leave_requests[i] = req_data
                    self._write_json_file(self.files["leave_requests"], leave_requests)
                    from .models import LeaveRequest
                    return LeaveRequest(**req_data)
            return None

    # Feedback operations
    def create_feedback(self, manager_id: str, feedback_data) -> dict:
        """Create feedback for a work log."""
        with self._file_lock(self.files["feedback"]):
            feedbacks = self._read_json_file(self.files["feedback"])
            
            # Get work log to find employee
            work_log = self.get_work_log(feedback_data.work_log_id)
            if not work_log:
                raise ValueError("Work log not found")
            
            feedback = {
                "id": self._generate_id(),
                "work_log_id": feedback_data.work_log_id,
                "employee_id": work_log.employee_id,
                "manager_id": manager_id,
                "feedback_text": feedback_data.feedback_text,
                "rating": feedback_data.rating,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            feedbacks.append(feedback)
            self._write_json_file(self.files["feedback"], feedbacks)
            
            from .models import Feedback
            return Feedback(**feedback)

    # Audit Trail operations
    def create_audit_entry(self, user_id: str, action: str, resource_type: str, 
                          resource_id: str, details: dict, ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None) -> dict:
        """Create an audit trail entry."""
        with self._file_lock(self.files["audit_trails"]):
            audit_trails = self._read_json_file(self.files["audit_trails"])
            
            audit_entry = {
                "id": self._generate_id(),
                "user_id": user_id,
                "action": action.value if hasattr(action, 'value') else action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.now().isoformat()
            }
            
            audit_trails.append(audit_entry)
            self._write_json_file(self.files["audit_trails"], audit_trails)
            
            from .models import AuditTrail
            return AuditTrail(**audit_entry)
    
    def get_audit_trails(self, limit: int = 100) -> List:
        """Get recent audit trail entries."""
        audit_trails = self._read_json_file(self.files["audit_trails"])
        sorted_trails = sorted(audit_trails, key=lambda x: x.get("timestamp", ""), reverse=True)
        from .models import AuditTrail
        return [AuditTrail(**trail_data) for trail_data in sorted_trails[:limit]]

    # Settings operations
    def get_settings(self):
        """Get system settings."""
        settings_data = self._read_json_file(self.files["settings"])
        if settings_data:
            from .models import SystemSettings
            return SystemSettings(**settings_data[0])
        else:
            # Create default settings
            from .models import SystemSettings
            default_settings = SystemSettings()
            self._write_json_file(self.files["settings"], [default_settings.model_dump()])
            return default_settings
    
    def update_settings(self, updates: dict):
        """Update system settings."""
        with self._file_lock(self.files["settings"]):
            settings_data = self._read_json_file(self.files["settings"])
            
            if settings_data:
                settings = settings_data[0]
            else:
                from .models import SystemSettings
                settings = SystemSettings().model_dump()
            
            for key, value in updates.items():
                if value is not None:
                    settings[key] = value
            settings["updated_at"] = datetime.now().isoformat()
            
            self._write_json_file(self.files["settings"], [settings])
            from .models import SystemSettings
            return SystemSettings(**settings)

    # Authentication helper
    def authenticate_user(self, email: str, password: str):
        """Authenticate user login."""
        employee = self.get_employee_by_email(email)
        if employee and self._verify_password(password, employee.password_hash):
            return employee
        return None


# Global storage instance
storage = JSONStorage()
