# Employee Activity and Management System - Full Stack Application

## Overview

This is a comprehensive Employee Activity and Management System built with a FastAPI backend and React frontend. The system provides role-based access control for employees, managers, and administrators to track daily work logs, manage leave requests, provide feedback, and maintain organizational hierarchies.

## 🚀 Quick Start Guide

### Prerequisites

- **Backend**: Python 3.8+ and pip
- **Frontend**: Node.js 16+ and npm
- **System**: Git for version control

### 1. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd employee-activity-and-management-system-90342-90430/backend

# Install Python dependencies
pip install -r requirements.txt

# Initialize default data and start server
python start.py
```

The backend will be available at: **http://localhost:8000**

### 2. Frontend Setup (React)

```bash
# Navigate to frontend directory
cd ../employee-activity-and-management-system-90342-90431/frontend_web_app

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at: **http://localhost:3000**

## 🔐 Default Admin Credentials

**Important**: Use these credentials for initial setup only!

- **Email**: `admin@company.com`
- **Password**: `admin123`

⚠️ **Security Notice**: Change these credentials immediately after first login through the Admin Panel.

## 🗄️ JSON Data Storage System

The application uses a file-based JSON storage system located in the backend's `data/` directory:

### Storage Files
- `employees.json` - Employee records and authentication data
- `work_logs.json` - Daily work log entries
- `leave_requests.json` - Leave request records
- `feedback.json` - Manager feedback on work logs
- `audit_trails.json` - System activity audit log
- `settings.json` - System configuration settings

### Storage Features
- **ACID-like Guarantees**: File locking ensures data consistency
- **Automatic Backup**: Corrupted files are automatically recovered
- **Thread Safety**: Concurrent access protection
- **JSON Structure**: Human-readable and easily maintainable

### Data Location
```
employee-activity-and-management-system-90342-90430/backend/data/
├── employees.json      # User accounts and profiles
├── work_logs.json      # Daily activity logs
├── leave_requests.json # Leave applications
├── feedback.json       # Performance feedback
├── audit_trails.json   # System audit log
└── settings.json       # Application settings
```

## 🔗 Frontend-Backend Integration

### API Communication Configuration

The frontend communicates with the backend via REST APIs. Configure the connection:

1. **Environment Variables** (Frontend):
   ```bash
   # In frontend_web_app/.env (create if needed)
   REACT_APP_API_BASE_URL=http://localhost:8000
   REACT_APP_API_TIMEOUT=10000
   ```

2. **CORS Configuration** (Backend):
   - The backend is configured to accept requests from all origins during development
   - For production, update the CORS settings in `backend/src/api/main.py`

3. **Authentication Flow**:
   - Frontend stores JWT tokens in localStorage
   - All API requests include the token in Authorization headers
   - Automatic token refresh and logout on expiration

## 📚 Complete API Reference

### Authentication Endpoints
- `POST /auth/login` - User login with email/password
- `POST /auth/logout` - User logout and token invalidation
- `GET /auth/me` - Get current user profile
- `POST /auth/verify-token` - Verify JWT token validity

### Employee Management
- `GET /employees/` - List all employees (Admin only)
- `POST /employees/` - Create new employee (Admin only)
- `GET /employees/me` - Get current user profile
- `GET /employees/{id}` - Get employee by ID
- `PUT /employees/{id}` - Update employee information
- `DELETE /employees/{id}` - Deactivate employee (Admin only)
- `GET /employees/{manager_id}/direct-reports` - Get team members

### Work Log Management
- `POST /work-logs/` - Submit daily work log entry
- `GET /work-logs/` - Get work logs with filtering options
- `GET /work-logs/{id}` - Get specific work log details
- `PUT /work-logs/{id}` - Update work log (time-limited)
- `POST /work-logs/{id}/feedback` - Add manager feedback
- `GET /work-logs/reports/summary` - Generate work statistics

### Leave Request Workflow
- `POST /leave-requests/` - Submit new leave request
- `GET /leave-requests/` - Get user's leave requests
- `GET /leave-requests/pending-approvals` - Get pending approvals (Managers)
- `GET /leave-requests/{id}` - Get specific leave request
- `PUT /leave-requests/{id}` - Update leave request
- `POST /leave-requests/{id}/approve` - Approve leave request
- `POST /leave-requests/{id}/reject` - Reject leave request
- `DELETE /leave-requests/{id}` - Cancel leave request

### Feedback System
- `POST /feedback/` - Create feedback (Managers only)
- `GET /feedback/employee/{id}` - Get employee feedback history
- `GET /feedback/work-log/{id}` - Get work log feedback
- `GET /feedback/my-feedback` - Get received feedback
- `GET /feedback/given-feedback` - Get given feedback (Managers)

### Administrative Functions
- `GET /admin/dashboard` - System dashboard statistics
- `GET /admin/audit-trails` - Activity audit trail
- `GET /admin/settings` - System configuration
- `PUT /admin/settings` - Update system settings
- `POST /admin/bulk-create-employees` - Bulk employee import
- `GET /admin/reports/productivity` - Productivity analytics

### Health & Monitoring
- `GET /` - Basic health check
- `GET /health` - Detailed system health status
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## 🧪 Testing the Full Stack Flow

### 1. System Health Check
```bash
# Test backend health
curl http://localhost:8000/health

# Expected response: {"status": "healthy", ...}
```

### 2. Authentication Test
```bash
# Login with default admin credentials
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "admin123"}'

# Expected response: {"token": "...", "user": {...}}
```

### 3. Frontend Integration Test
1. Open http://localhost:3000
2. Login with admin credentials
3. Navigate through different sections:
   - Dashboard - View system overview
   - Work Log - Submit daily activities
   - Leave Requests - Manage time off
   - Admin Panel - System administration

### 4. API Integration Test
```bash
# Get user profile (replace TOKEN with actual JWT)
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer TOKEN"

# Submit a work log
curl -X POST http://localhost:8000/work-logs/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-07-31",
    "task_description": "API integration testing",
    "time_spent": 2.5,
    "status": "completed",
    "project": "System Testing"
  }'
```

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│   React Frontend│ ◄─────────────────► │  FastAPI Backend│
│   (Port 3000)   │                     │   (Port 8000)   │
└─────────────────┘                     └─────────────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │  JSON Storage   │
                                        │     System      │
                                        └─────────────────┘
```

### Technology Stack
- **Frontend**: React 18.2, React Router, Axios, vanilla CSS
- **Backend**: FastAPI, Pydantic, JWT Authentication, Uvicorn
- **Storage**: JSON files with file locking
- **Security**: SHA-256 password hashing, JWT tokens, CORS protection

## 🔧 Development & Deployment

### Development Mode
- **Backend**: Auto-reload enabled with `--reload` flag
- **Frontend**: Hot module replacement via React Scripts
- **CORS**: Permissive settings for local development

### Production Considerations
1. **Security**: Update default passwords and JWT secret
2. **CORS**: Restrict origins to your domain
3. **HTTPS**: Enable SSL/TLS certificates
4. **Storage**: Consider database migration for scale
5. **Environment**: Set production environment variables

### Environment Variables
```bash
# Backend (.env - optional)
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend (.env)
REACT_APP_API_BASE_URL=https://your-api-domain.com
REACT_APP_API_TIMEOUT=10000
```

## 📖 Additional Documentation

- **Backend API**: http://localhost:8000/docs (Swagger UI)
- **Code Documentation**: Inline comments and docstrings
- **Architecture Details**: See `kavia-docs/` folder for detailed analysis

## 🐛 Troubleshooting

### Common Issues
1. **Port Conflicts**: Change ports in startup commands if occupied
2. **CORS Errors**: Verify frontend and backend URLs match
3. **Authentication**: Ensure JWT tokens are properly stored
4. **File Permissions**: Check data/ directory write permissions

### Support Resources
- Check browser developer console for frontend errors
- Review backend logs in terminal for API issues
- Verify JSON file integrity in `backend/data/` directory
- Use API documentation at `/docs` for endpoint testing

---

**Version**: 1.0.0  
**Last Updated**: July 31, 2025  
**License**: Proprietary