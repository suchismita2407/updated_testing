#!/usr/bin/env python3
"""
Run the Sales EVA Testing Dashboard
"""

import subprocess
import sys
from pathlib import Path

def run_dashboard():
    """Run the Streamlit dashboard"""
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    
    if not dashboard_path.exists():
        print(f"Error: Dashboard not found at {dashboard_path}")
        sys.exit(1)
    
    print("🚀 Starting Sales EVA Testing Dashboard...")
    print(f"📊 Dashboard will be available at: http://localhost:8501")
    print("📖 API docs will be available at: http://localhost:8502/docs")
    print("\nPress Ctrl+C to stop the dashboard")
    
    # Run Streamlit
    try:
        subprocess.run([
            "streamlit", "run",
            str(dashboard_path),
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.serverAddress", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"Error running dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_dashboard()