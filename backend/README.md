# Employee Activity and Management System - Backend

## Overview

This is a comprehensive FastAPI backend for the Employee Activity and Management System that provides role-based access control, work log management, leave request workflows, feedback systems, and administrative functions. The backend uses structured JSON files for data persistence, ensuring production-ready CRUD operations without requiring a traditional database setup.

## Features

### 🔐 Authentication & Authorization
- JWT token-based authentication
- Role-based access control (Employee, Manager, Admin)
- Secure password hashing
- Token verification and refresh capabilities

### 👥 Employee Management
- Complete CRUD operations for employee records
- Role and hierarchy management
- Manager-employee relationships
- Bulk employee creation via CSV/JSON import

### 📋 Work Log System
- Daily work log entry and management
- Time-based edit restrictions
- Task status tracking (In Progress, Completed, Blocked)
- Manager feedback on work logs
- Project and category organization

### 🏖️ Leave Request Workflow
- Leave request submission and tracking
- Manager approval/rejection workflow
- Status history and comments
- Leave type categorization

### 💬 Feedback System
- Manager feedback on employee work logs
- Rating system (1-5 scale)
- Feedback history and tracking

### 🛠️ Admin Panel
- System settings management
- Audit trail monitoring
- Dashboard with key metrics
- Productivity reporting
- Bulk operations

### 📊 Reporting & Analytics
- Employee productivity reports
- Work log summaries
- Leave request analytics
- Audit trail access

## Technical Architecture

### Data Persistence
- **JSON File Storage**: All data is stored in structured JSON files
- **ACID-like Guarantees**: File locking and atomic writes ensure data consistency
- **Error Recovery**: Automatic backup and recovery for corrupted files
- **Thread Safety**: Concurrent access protection using file locks

### API Design
- **RESTful APIs**: Standard HTTP methods and status codes
- **OpenAPI/Swagger**: Complete API documentation at `/docs`
- **Pydantic Models**: Strong typing and validation
- **Error Handling**: Comprehensive error responses with details

### Security
- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: SHA-256 password encryption
- **Role-based Permissions**: Granular access control
- **Audit Logging**: Complete activity tracking

## Project Structure

```
backend/
├── src/
│   └── api/
│       ├── __init__.py
│       ├── main.py              # FastAPI application entry point
│       ├── models.py            # Pydantic data models
│       ├── storage.py           # JSON storage layer
│       ├── auth.py              # Authentication & authorization
│       ├── init_data.py         # Default data initialization
│       └── routes/              # API route modules
│           ├── __init__.py
│           ├── auth.py          # Authentication endpoints
│           ├── employees.py     # Employee management
│           ├── work_logs.py     # Work log operations
│           ├── leave_requests.py # Leave request workflow
│           ├── feedback.py      # Feedback management
│           └── admin.py         # Administrative functions
├── data/                        # JSON data files (auto-created)
│   ├── employees.json
│   ├── work_logs.json
│   ├── leave_requests.json
│   ├── feedback.json
│   ├── audit_trails.json
│   └── settings.json
├── requirements.txt             # Python dependencies
├── start.py                     # Startup script
└── README.md                    # This file
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation & Setup

1. **Navigate to the backend directory:**
   ```bash
   cd employee-activity-and-management-system-90342-90430/backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize default data:**
   ```bash
   python src/api/init_data.py
   ```

4. **Start the server:**
   ```bash
   python start.py
   ```
   
   Or manually:
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Default Admin Account
- **Email:** `admin@company.com`
- **Password:** `admin123`
- **⚠️ Important:** Change this password immediately after first login!

## API Documentation

Once the server is running, access the interactive API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user info
- `POST /auth/verify-token` - Verify JWT token

### Employees
- `GET /employees/` - List all employees (Admin only)
- `POST /employees/` - Create new employee (Admin only)
- `GET /employees/me` - Get current user profile
- `GET /employees/{id}` - Get employee by ID
- `PUT /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Deactivate employee (Admin only)
- `GET /employees/{manager_id}/direct-reports` - Get direct reports

### Work Logs
- `POST /work-logs/` - Create work log entry
- `GET /work-logs/` - Get work logs (with filters)
- `GET /work-logs/{id}` - Get specific work log
- `PUT /work-logs/{id}` - Update work log (time-limited)
- `POST /work-logs/{id}/feedback` - Add manager feedback
- `GET /work-logs/reports/summary` - Work summary statistics

### Leave Requests
- `POST /leave-requests/` - Submit leave request
- `GET /leave-requests/` - Get user's leave requests
- `GET /leave-requests/pending-approvals` - Get pending approvals (Managers)
- `GET /leave-requests/{id}` - Get specific leave request
- `PUT /leave-requests/{id}` - Update leave request
- `POST /leave-requests/{id}/approve` - Approve/reject leave request
- `DELETE /leave-requests/{id}` - Cancel leave request

### Feedback
- `POST /feedback/` - Create feedback (Managers only)
- `GET /feedback/employee/{id}` - Get employee feedback
- `GET /feedback/work-log/{id}` - Get work log feedback
- `GET /feedback/my-feedback` - Get received feedback
- `GET /feedback/given-feedback` - Get given feedback (Managers)

### Admin
- `GET /admin/dashboard` - Dashboard statistics
- `GET /admin/audit-trails` - Audit trail entries
- `GET /admin/settings` - System settings
- `PUT /admin/settings` - Update system settings
- `POST /admin/bulk-create-employees` - Bulk employee creation
- `GET /admin/reports/productivity` - Productivity reports

## Data Models

### Employee
```json
{
  "id": "uuid",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "employee|manager|admin",
  "manager_id": "uuid|null",
  "department": "string",
  "position": "string",
  "hire_date": "date",
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Work Log
```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "date": "date",
  "task_description": "string",
  "time_spent": 8.5,
  "status": "in_progress|completed|blocked",
  "project": "string",
  "category": "string",
  "notes": "string",
  "manager_feedback": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "can_edit": true
}
```

### Leave Request
```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "start_date": "date",
  "end_date": "date",
  "leave_type": "string",
  "reason": "string",
  "status": "pending|approved|rejected",
  "manager_id": "uuid",
  "manager_comments": "string",
  "approved_by": "uuid",
  "approved_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Configuration

### Environment Variables
The system uses the following environment variables (optional):
- `SECRET_KEY`: JWT secret key (defaults to development key)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)

### System Settings
Configurable via the Admin panel:
- `log_edit_time_limit_hours`: Time limit for editing work logs (default: 24)
- `default_leave_types`: Available leave types
- `default_task_categories`: Available task categories
- `notification_settings`: Notification configuration

## Security Considerations

### Production Deployment
1. **Change Default Password:** Immediately update the admin password
2. **JWT Secret:** Set a strong `SECRET_KEY` environment variable
3. **CORS Configuration:** Restrict `allow_origins` in production
4. **HTTPS:** Use HTTPS in production environments
5. **File Permissions:** Secure the `data/` directory permissions

### Data Protection
- All passwords are hashed using SHA-256
- JWT tokens have configurable expiration times
- File-level locking prevents data corruption
- Comprehensive audit logging tracks all actions

## Development

### Adding New Features
1. **Models:** Add new Pydantic models in `models.py`
2. **Storage:** Extend storage operations in `storage.py`
3. **Routes:** Create new route modules in `routes/`
4. **Documentation:** Update OpenAPI documentation

### Testing
```bash
# Run with auto-reload for development
python -m uvicorn src.api.main:app --reload

# Test endpoints
curl -X GET "http://localhost:8000/health"
```

## Troubleshooting

### Common Issues

1. **Import Errors:** Ensure all dependencies are installed via `pip install -r requirements.txt`
2. **Permission Errors:** Check file permissions on the `data/` directory
3. **Port Conflicts:** Change the port if 8000 is already in use
4. **Data Corruption:** Backup files are automatically created for recovery

### Logs
- Server logs are displayed in the console
- All user actions are logged in `audit_trails.json`
- Application errors include detailed stack traces

## Performance

### Scalability Considerations
- **File Locking:** May become a bottleneck with high concurrency
- **Memory Usage:** JSON files are loaded into memory for operations
- **Future Migration:** Designed for easy migration to database systems

### Optimization Tips
- Regular cleanup of audit trails
- Periodic data archiving for large datasets
- Consider database migration for production scale

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the audit trails for debugging
3. Examine server logs for error details
4. Verify JSON file integrity in the `data/` directory

---

**Version:** 1.0.0  
**Last Updated:** July 31, 2025
