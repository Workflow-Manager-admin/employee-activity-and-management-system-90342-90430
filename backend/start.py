"""
Startup script for the Employee Management System backend.
Initializes data and starts the FastAPI server.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Main startup function."""
    print("🚀 Starting Employee Management System Backend...")
    
    # Change to the backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Run data initialization
    print("\n📦 Initializing data...")
    try:
        result = subprocess.run([
            sys.executable, "src/api/init_data.py"
        ], check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Data initialization failed: {e}")
        print(e.stdout)
        print(e.stderr)
        return 1
    
    print("\n🌐 Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    # Start the FastAPI server
    try:
        result = subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "src.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
