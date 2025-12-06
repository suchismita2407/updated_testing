# dashboard/app.py
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# Try to import EnhancedTestingDashboard
try:
    from dashboard.testing_dashboard import EnhancedTestingDashboard
except ImportError:
    # If that fails, try direct import
    try:
        from testing_dashboard import EnhancedTestingDashboard
    except ImportError as e:
        st.error(f"Failed to import EnhancedTestingDashboard: {e}")
        st.stop()

# Run the enhanced dashboard
if __name__ == "__main__":
    dashboard = EnhancedTestingDashboard()
    dashboard.run()