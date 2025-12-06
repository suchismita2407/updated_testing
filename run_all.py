#!/usr/bin/env python3
"""
Run both API server and Dashboard
"""

import subprocess
import sys
from pathlib import Path
import time
import webbrowser

def run_all():
    """Run both API server and dashboard"""
    print("🚀 Starting Sales EVA Testing Framework...")
    print("\n📊 Services:")
    print("  Dashboard: http://localhost:8501")
    print("  API Server: http://localhost:8502")
    print("  API Docs: http://localhost:8502/docs")
    
    # Open dashboard in browser after delay
    def open_browser():
        time.sleep(3)
        webbrowser.open("http://localhost:8501")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Use subprocess to run both services
    # Note: This is a simple approach. For production, use process managers like pm2 or supervisor
    try:
        # Start API server
        api_process = subprocess.Popen([
            sys.executable, "run_api.py"
        ])
        
        # Start dashboard
        dashboard_process = subprocess.Popen([
            sys.executable, "run_dashboard.py"
        ])
        
        print("\n✅ Both services started!")
        print("📝 Logs will appear in separate windows/terminals")
        print("\n🛑 Press Ctrl+C to stop all services")
        
        # Wait for both processes
        api_process.wait()
        dashboard_process.wait()
        
    except KeyboardInterrupt:
        print("\n👋 Stopping all services...")
        api_process.terminate()
        dashboard_process.terminate()
        api_process.wait()
        dashboard_process.wait()
        print("✅ All services stopped")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_all()