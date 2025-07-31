"""
Initialize default data for the Employee Management System.
This script creates the default admin user and sets up initial data.
"""

import os
import sys
from datetime import date

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.storage import storage
from api.models import EmployeeCreate, Role


def init_default_data():
    """Initialize default data including admin user and system settings."""
    
    print("Initializing Employee Management System data...")
    
    # Create default admin user if none exists
    admin_email = "admin@company.com"
    existing_admin = storage.get_employee_by_email(admin_email)
    
    if not existing_admin:
        print("Creating default admin user...")
        admin_data = EmployeeCreate(
            email=admin_email,
            password="admin123",  # Should be changed immediately in production
            first_name="System",
            last_name="Administrator",
            role=Role.ADMIN,
            department="IT",
            position="System Administrator",
            hire_date=date.today()
        )
        
        admin_user = storage.create_employee(admin_data)
        print(f"Created admin user with ID: {admin_user.id}")
        print(f"Default admin credentials: {admin_email} / admin123")
        print("⚠️  IMPORTANT: Change the default password immediately!")
    else:
        print("Admin user already exists.")
    
    # Initialize default system settings if not exists
    try:
        storage.get_settings()
        print("System settings already initialized.")
    except:
        print("Initializing default system settings...")
        # Settings will be auto-created with defaults when first accessed
        storage.get_settings()
        print("Default system settings created.")
    
    print("✅ Data initialization complete!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn src.api.main:app --reload")
    print("2. Access the API documentation at: http://localhost:8000/docs")
    print("3. Login with the admin credentials to set up your organization")


if __name__ == "__main__":
    init_default_data()
