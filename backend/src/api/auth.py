import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import Employee, Role
from .storage import storage

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Should be in environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Employee:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = storage.get_employee(user_id)
    if user is None:
        raise credentials_exception
    
    return user


def require_role(required_roles: list[Role]):
    """Dependency to require specific roles."""
    def role_checker(current_user: Employee = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Role-specific dependencies
def get_admin_user(current_user: Employee = Depends(require_role([Role.ADMIN]))):
    return current_user


def get_manager_or_admin_user(current_user: Employee = Depends(require_role([Role.MANAGER, Role.ADMIN]))):
    return current_user


def get_any_user(current_user: Employee = Depends(get_current_user)):
    return current_user


def can_access_employee_data(current_user: Employee, target_employee_id: str) -> bool:
    """Check if current user can access target employee's data."""
    # Admin can access any data
    if current_user.role == Role.ADMIN:
        return True
    
    # User can access their own data
    if current_user.id == target_employee_id:
        return True
    
    # Manager can access their direct reports' data
    if current_user.role == Role.MANAGER:
        target_employee = storage.get_employee(target_employee_id)
        if target_employee and target_employee.manager_id == current_user.id:
            return True
    
    return False


def can_approve_leave(current_user: Employee, leave_request) -> bool:
    """Check if current user can approve leave request."""
    # Admin can approve any leave
    if current_user.role == Role.ADMIN:
        return True
    
    # Manager can approve their direct reports' leaves
    if current_user.role == Role.MANAGER and leave_request.manager_id == current_user.id:
        return True
    
    return False
