from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
from ..models import LoginRequest, LoginResponse, EmployeeResponse, ActionType
from ..storage import storage
from ..auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])


# PUBLIC_INTERFACE
@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return access token.
    """
    user = storage.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Log successful login
    storage.create_audit_entry(
        user_id=user.id,
        action=ActionType.LOGIN,
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=EmployeeResponse(**user.model_dump())
    )


# PUBLIC_INTERFACE
@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """
    Logout current user (invalidate token on client side).
    Note: JWT tokens are stateless, so actual invalidation happens on client side.
    """
    # Log logout action
    storage.create_audit_entry(
        user_id=current_user.id,
        action=ActionType.LOGOUT,
        resource_type="user",
        resource_id=current_user.id,
        details={"email": current_user.email}
    )
    
    return {"message": "Successfully logged out"}


# PUBLIC_INTERFACE
@router.get("/me", response_model=EmployeeResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return EmployeeResponse(**current_user.model_dump())


# PUBLIC_INTERFACE
@router.post("/verify-token")
async def verify_token(current_user = Depends(get_current_user)):
    """
    Verify if the provided token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }
