#!/usr/bin/env python3
"""
Run the Sales EVA Testing Framework API server
"""

import subprocess
import sys
from pathlib import Path

def run_api():
    """Run the FastAPI server"""
    api_path = Path(__file__).parent / "api" / "server.py"
    
    if not api_path.exists():
        print(f"Error: API server not found at {api_path}")
        sys.exit(1)
    
    print("🚀 Starting Sales EVA Testing Framework API...")
    print(f"📡 API will be available at: http://localhost:8502")
    print("📖 API docs will be available at: http://localhost:8502/docs")
    print("\nPress Ctrl+C to stop the API server")
    
    # Run FastAPI with uvicorn
    try:
        subprocess.run([
            "uvicorn", "api.server:app",
            "--host", "0.0.0.0",
            "--port", "8502",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
    except Exception as e:
        print(f"Error running API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_api()