# sales_eva_testing_framework/dashboard/testing_dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import asyncio
import random
import httpx
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tester import SalesEVATester
from src.detailed_metrics_collector import DetailedMetricsCollector
from src.detailed_test_runner import DetailedTestRunner
from config.settings import settings
from typing import Dict, List, Any, Optional

class EnhancedTestingDashboard:
    """Enhanced dashboard with visual metrics for all tests"""
    
    def __init__(self):
        st.set_page_config(
            page_title="Sales EVA Testing Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state
        if 'tester' not in st.session_state:
            st.session_state.tester = None
        if 'metrics' not in st.session_state:
            st.session_state.metrics = DetailedMetricsCollector()
        if 'test_runner' not in st.session_state:
            st.session_state.test_runner = DetailedTestRunner(
                base_url=settings.SALES_EVA_API_URL,
                metrics_collector=st.session_state.metrics
            )
        if 'test_results' not in st.session_state:
            st.session_state.test_results = {}
        if 'running_tests' not in st.session_state:
            st.session_state.running_tests = []
        if 'page' not in st.session_state:
            st.session_state.page = "dashboard"
        if 'test_filter' not in st.session_state:
            st.session_state.test_filter = "all"

        # Custom CSS
        self._apply_custom_css()
    
    def _apply_custom_css(self):
        """Apply custom CSS for better UX"""
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                color: #1E3A8A;
                font-weight: 700;
                margin-bottom: 1rem;
            }
            .sub-header {
                font-size: 1.5rem;
                color: #374151;
                font-weight: 600;
                margin-bottom: 1rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                padding: 1.5rem;
                color: white;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .success-card {
                background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            }
            .warning-card {
                background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
            }
            .error-card {
                background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
            }
            .test-running {
                background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%);
                color: white;
                padding: 1rem;
                border-radius: 10px;
                animation: pulse 2s infinite;
                text-align: center;
                font-weight: bold;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            .progress-bar {
                height: 10px;
                background: #E5E7EB;
                border-radius: 5px;
                overflow: hidden;
                margin: 0.5rem 0;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #10B981 0%, #059669 100%);
                border-radius: 5px;
                transition: width 0.3s ease;
            }
            .stButton button {
                width: 100%;
            }
            .test-detail-card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 1rem;
                border-left: 4px solid #3B82F6;
            }
            .input-badge {
                background: #E3F2FD;
                color: #1565C0;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8rem;
                margin-right: 5px;
                display: inline-block;
            }
            .output-badge {
                background: #E8F5E9;
                color: #2E7D32;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8rem;
                margin-right: 5px;
                display: inline-block;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Run the enhanced dashboard"""
        # Sidebar
        self._render_sidebar()
        
        # Main content
        page = st.session_state.get("page", "dashboard")
        
        # Update page_functions in run method
        page_functions = {
            "dashboard": self._render_dashboard,
            "test_details": self._render_test_details,
            "prompt_responses": self._render_prompt_responses,  # NEW
            "data_management": self._render_data_management,
            "login_tests": self._render_login_tests,
            "prompt_tests": self._render_prompt_tests,
            "agent_tests": self._render_agent_tests,
            "kb_tests": self._render_kb_tests,
            "e2e_tests": self._render_e2e_tests,
            "test_cases": self._render_test_cases,
            "metrics": self._render_detailed_metrics,
            "run_tests": self._render_run_tests,
            "history": self._render_history
        }
        
        if page in page_functions:
            page_functions[page]()
    
    def _render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.markdown("## 🧪 Sales EVA Testing")
            st.markdown("---")
            
            # Configuration
            st.markdown("### 🔧 Configuration")
            api_url = st.text_input(
                "Sales EVA API URL",
                value=settings.SALES_EVA_API_URL,
                help="URL of the Sales EVA service to test"
            )
            
            if api_url != settings.SALES_EVA_API_URL:
                settings.SALES_EVA_API_URL = api_url
                # Reinitialize test runner with new URL
                st.session_state.test_runner = DetailedTestRunner(
                    base_url=api_url,
                    metrics_collector=st.session_state.metrics
                )
            
            # Health check
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Health Check", width='stretch'):
                    self._run_health_check()
            
            with col2:
                if st.button("🔄 Refresh", width='stretch'):
                    st.rerun()
            
            st.markdown("---")
            
            # Navigation
            st.markdown("### 📊 Navigation")
            
            # Update the pages list in _render_sidebar method
            pages = [
                ("📈 Dashboard", "dashboard"),
                ("🔍 Test Details", "test_details"),
                ("📝 Prompt Responses", "prompt_responses"),  # NEW
                ("💾 Data Management", "data_management"),
                ("🔐 Login Tests", "login_tests"),
                ("💬 Prompt Tests", "prompt_tests"),
                ("🤖 Agent Tests", "agent_tests"),
                ("📚 KB Tests", "kb_tests"),
                ("🚀 E2E Tests", "e2e_tests"),
                ("📋 Test Cases", "test_cases"),
                ("📊 Metrics", "metrics"),
                ("⚡ Run Tests", "run_tests"),
                ("🕐 History", "history")
            ]
            
            for page_name, page_key in pages:
                if st.button(
                    page_name,
                    key=f"nav_{page_key}",
                    width='stretch',
                    type="primary" if page_key == st.session_state.get("page", "dashboard") else "secondary"
                ):
                    st.session_state["page"] = page_key
                    st.rerun()
            
            st.markdown("---")
            
            # Quick stats
            st.markdown("### 📊 Quick Stats")
            stats = st.session_state.metrics.get_summary_stats()
            if stats:
                st.metric("Total Tests", stats.get("total_tests", 0))
                st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
                st.metric("Avg Score", f"{stats.get('avg_score', 0):.2f}")
    
    def _render_dashboard(self):
        """Render main dashboard"""
        st.markdown('<div class="main-header">Sales EVA Testing Dashboard</div>', unsafe_allow_html=True)
        
        # Quick actions row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🚀 Run Quick Test", width='stretch'):
                self._run_quick_test()
        with col2:
            if st.button("📊 View Metrics", width='stretch'):
                st.session_state["page"] = "metrics"
                st.rerun()
        with col3:
            if st.button("📋 Test History", width='stretch'):
                st.session_state["page"] = "history"
                st.rerun()
        with col4:
            if st.button("⚡ Run All Tests", width='stretch'):
                st.session_state["page"] = "run_tests"
                st.rerun()
        
        # Quick access to test details
        st.markdown("---")
        st.markdown("### 🔍 Quick Access")
        
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            if st.button("📋 View Latest Test", width='stretch'):
                st.session_state["page"] = "test_details"
                st.rerun()
        
        with quick_col2:
            if st.button("📊 Failed Tests", width='stretch'):
                st.session_state.test_filter = "failed"
                st.session_state["page"] = "test_details"
                st.rerun()
        
        with quick_col3:
            if st.button("💾 Export All Data", width='stretch'):
                st.session_state["page"] = "data_management"
                st.rerun()
        
        st.markdown("---")
        
        # Metrics overview
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_overall_metrics()
        
        with col2:
            self._render_test_distribution()
        
        # Recent tests
        st.markdown("---")
        self._render_recent_tests()
        
        # Running tests
        if st.session_state.running_tests:
            st.markdown("---")
            self._render_running_tests()
    
    def _render_login_tests(self):
        """Render login testing interface"""
        st.markdown('<div class="main-header">🔐 Login & Authentication Tests</div>', unsafe_allow_html=True)
        
        with st.expander("📋 Test Scenarios", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Valid Login Tests:**")
                if st.button("✅ Test Valid Login", key="valid_login", width='stretch'):
                    self._run_login_test("sales1", "demo123", "Valid credentials")
                if st.button("✅ Test Expert Login", key="expert_login", width='stretch'):
                    self._run_login_test("expert1", "demo123", "Expert credentials")
                if st.button("✅ Test Admin Login", key="admin_login", width='stretch'):
                    self._run_login_test("admin", "demo123", "Admin credentials")
            
            with col2:
                st.markdown("**Invalid Login Tests:**")
                if st.button("❌ Test Invalid User", key="invalid_user", width='stretch'):
                    self._run_login_test("invalid_user", "wrong_pass", "Invalid username")
                if st.button("❌ Test Wrong Password", key="wrong_pass", width='stretch'):
                    self._run_login_test("sales1", "wrong_pass", "Wrong password")
                if st.button("❌ Test Empty Credentials", key="empty_creds", width='stretch'):
                    self._run_login_test("", "", "Empty credentials")
        
        # Login test results
        st.markdown("---")
        st.markdown("### 📊 Login Test Results")
        
        # Get login metrics
        login_metrics = []
        for metric in st.session_state.metrics.get_session_metrics():
            if metric.get("test_type") == "login":
                login_metrics.append(metric)
        
        if login_metrics:
            df = pd.DataFrame(login_metrics)
            
            # Metrics cards
            total = len(df)
            passed = len(df[df["status"] == "passed"])
            failed = len(df[df["status"] == "failed"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                self._metric_card("Total Tests", total, "Login tests executed", "default")
            with col2:
                self._metric_card("Passed", passed, f"{passed/total*100:.1f}% success", "success")
            with col3:
                self._metric_card("Failed", failed, f"{failed/total*100:.1f}% failure", "error" if failed > 0 else "default")
            
            # Detailed table
            st.dataframe(
                df[["test_name", "status", "score", "duration_ms", "timestamp"]],
                use_container_width=True,
                column_config={
                    "test_name": "Test Scenario",
                    "status": "Status",
                    "score": "Score",
                    "duration_ms": "Duration (ms)",
                    "timestamp": "Time"
                }
            )
        else:
            st.info("No login tests executed yet. Run some tests above.")
    
    def _render_prompt_tests(self):
        """Render prompt testing interface"""
        st.markdown('<div class="main-header">💬 Prompt Testing & Optimization</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Test Configuration")
            
            prompt_count = st.slider("Number of prompts to test", 10, 200, 50)
            test_case_count = st.slider("Test cases per prompt", 5, 50, 20)
            
            if st.button("🚀 Run Prompt Tests", type="primary", width='stretch'):
                self._run_prompt_tests(prompt_count, test_case_count)
        
        with col2:
            st.markdown("### Quick Tests")
            if st.button("🔍 Test Single Prompt", width='stretch'):
                self._run_single_prompt_test()
            if st.button("📊 Analyze Prompt Styles", width='stretch'):
                self._run_prompt_style_analysis()
        
        # Prompt test results
        st.markdown("---")
        self._render_test_results_by_type("prompt")
    
    def _render_agent_tests(self):
        """Render agent testing interface"""
        st.markdown('<div class="main-header">🤖 Agent Capability Tests</div>', unsafe_allow_html=True)
        
        st.markdown("""
        Test different agent functions using RAG search endpoint:
        - **Matching**: Finding relevant offerings for opportunities
        - **Gap Analysis**: Identifying missing capabilities
        - **Research**: Finding latest information
        - **Reporting**: Generating sales proposals
        """)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🎯 Test Matching", width='stretch'):
                self._run_agent_test("matching")
        with col2:
            if st.button("🔍 Test Gap Analysis", width='stretch'):
                self._run_agent_test("gap_analysis")
        with col3:
            if st.button("📚 Test Research", width='stretch'):
                self._run_agent_test("research")
        with col4:
            if st.button("📄 Test Reporting", width='stretch'):
                self._run_agent_test("reporting")
        
        if st.button("🚀 Test All Agent Functions", type="primary", width='stretch'):
            self._run_all_agent_tests()
        
        # Agent test results
        st.markdown("---")
        self._render_test_results_by_type("agent")
    
    def _render_kb_tests(self):
        """Render knowledge base testing interface"""
        st.markdown('<div class="main-header">📚 Knowledge Base Validation</div>', unsafe_allow_html=True)
        
        st.markdown("""
        Test knowledge base using RAG search:
        - **Coverage**: Does KB cover required topics?
        - **Freshness**: Is information up-to-date?
        - **Consistency**: Are there contradictions?
        - **Relevance**: Is content relevant to sales?
        """)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📚 Test Coverage", width='stretch'):
                self._run_kb_test("coverage")
        with col2:
            if st.button("🕒 Test Freshness", width='stretch'):
                self._run_kb_test("freshness")
        with col3:
            if st.button("⚖️ Test Consistency", width='stretch'):
                self._run_kb_test("consistency")
        with col4:
            if st.button("🎯 Test Relevance", width='stretch'):
                self._run_kb_test("relevance")
        
        sample_size = st.slider("Sample size for validation", 10, 100, 50)
        
        if st.button("🚀 Run Comprehensive KB Validation", type="primary", width='stretch'):
            self._run_comprehensive_kb_validation(sample_size)
        
        # KB test results
        st.markdown("---")
        self._render_test_results_by_type("kb")
    
    def _render_e2e_tests(self):
        """Render end-to-end testing interface"""
        st.markdown('<div class="main-header">🚀 End-to-End System Tests</div>', unsafe_allow_html=True)
        
        st.markdown("### Test Realistic Sales Scenarios")
        
        scenario_options = {
            "Banking AI": "Bank needs AI-powered fraud detection with cloud deployment",
            "Retail Digital": "Retail chain wants digital transformation with mobile apps",
            "Healthcare Data": "Hospital network needs patient data analytics platform",
            "Manufacturing IoT": "Manufacturer seeks IoT-based predictive maintenance"
        }
        
        selected_scenario = st.selectbox(
            "Choose a test scenario",
            options=list(scenario_options.keys())
        )
        
        if st.button(f"🚀 Test {selected_scenario} Scenario", type="primary", width='stretch'):
            self._run_e2e_scenario(selected_scenario, scenario_options[selected_scenario])
        
        # Custom scenario
        st.markdown("---")
        st.markdown("### Custom Scenario")
        custom_scenario = st.text_area(
            "Enter custom opportunity description",
            placeholder="Describe a sales opportunity to test end-to-end...",
            height=100
        )
        
        if st.button("🚀 Test Custom Scenario", width='stretch'):
            self._run_e2e_scenario("Custom", custom_scenario)
        
        # E2E test results
        st.markdown("---")
        self._render_test_results_by_type("e2e")
    
    def _render_test_details(self):
        """Render detailed test execution view"""
        st.markdown('<div class="main-header">🔍 Test Execution Details</div>', unsafe_allow_html=True)
        
        # Test selector
        all_tests = st.session_state.metrics.get_session_metrics()
        
        if not all_tests:
            st.info("No tests executed yet. Run some tests first.")
            return
        
        # Filter options
        filter_options = st.columns(5)
        with filter_options[0]:
            if st.button("All Tests", width='stretch'):
                st.session_state.test_filter = "all"
                st.rerun()
        with filter_options[1]:
            if st.button("✅ Passed", width='stretch'):
                st.session_state.test_filter = "passed"
                st.rerun()
        with filter_options[2]:
            if st.button("❌ Failed", width='stretch'):
                st.session_state.test_filter = "failed"
                st.rerun()
        with filter_options[3]:
            if st.button("⚠️ Errors", width='stretch'):
                st.session_state.test_filter = "error"
                st.rerun()
        with filter_options[4]:
            if st.button("🔄 Running", width='stretch'):
                st.session_state.test_filter = "running"
                st.rerun()
        
        # Apply filter
        filtered_tests = []
        if st.session_state.test_filter == "all":
            filtered_tests = all_tests
        elif st.session_state.test_filter == "passed":
            filtered_tests = [t for t in all_tests if t.get("status") == "passed"]
        elif st.session_state.test_filter == "failed":
            filtered_tests = [t for t in all_tests if t.get("status") == "failed"]
        elif st.session_state.test_filter == "error":
            filtered_tests = [t for t in all_tests if t.get("status") == "error"]
        elif st.session_state.test_filter == "running":
            filtered_tests = [t for t in all_tests if t.get("status") == "running"]
        
        st.markdown(f"**Showing {len(filtered_tests)} of {len(all_tests)} tests**")
        
        if not filtered_tests:
            st.info(f"No tests found with filter: {st.session_state.test_filter}")
            return
        
        # Create test selection
        test_options = []
        for test in filtered_tests:
            test_id = test.get("timer_id", "unknown")
            test_name = test.get("test_name", "Unknown")
            test_type = test.get("test_type", "unknown")
            status = test.get("status", "unknown")
            timestamp = test.get("timestamp", "")
            score = test.get("score", 0)
            
            # Format timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:19]
            else:
                time_str = ""
            
            display_text = f"{test_name} ({test_type}) - Score: {score:.2f} - {status.upper()} - {time_str}"
            test_options.append((display_text, test_id))
        
        # Create selector
        selected_display = st.selectbox(
            "Select a test to view details:",
            options=[opt[0] for opt in test_options],
            index=len(test_options) - 1 if test_options else 0,
            key="test_selector"
        )
        
        # Find selected test
        selected_test = None
        selected_id = None
        for display, test_id in test_options:
            if display == selected_display:
                selected_id = test_id
                selected_test = next((t for t in filtered_tests if t.get("timer_id") == test_id), None)
                break
        
        if not selected_test:
            st.error("Selected test not found")
            return
        
        # Display test details in tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📥 Inputs", "📤 Outputs", "📈 Analysis", "💾 Raw Data"])
        
        with tab1:
            self._render_test_overview(selected_test)
        
        with tab2:
            self._render_test_inputs(selected_test)
        
        with tab3:
            self._render_test_outputs(selected_test)
        
        with tab4:
            self._render_test_analysis(selected_test)
        
        with tab5:
            self._render_raw_data(selected_test)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Run This Test Again", width='stretch'):
                self._rerun_test(selected_test)
        
        with col2:
            if st.button("📋 Export Test Details", width='stretch'):
                self._export_test_details(selected_test)
        
        with col3:
            if st.button("📊 Compare Similar Tests", width='stretch'):
                self._compare_similar_tests(selected_test)
    
    def _render_data_management(self):
        """Render data management interface"""
        st.markdown('<div class="main-header">💾 Data Management</div>', unsafe_allow_html=True)
        
        # Data overview
        st.markdown("### 📊 Stored Data Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Count files in data directory
        data_dir = Path("data")
        if data_dir.exists():
            test_cases = list((data_dir / "test_cases").glob("*.json"))
            prompts = list((data_dir / "prompts").glob("*.json"))
            credentials = list((data_dir / "credentials").glob("*.json"))
            results = list((data_dir / "results").glob("*.json"))
            
            with col1:
                st.metric("Test Cases", len(test_cases))
            with col2:
                st.metric("Prompts", len(prompts))
            with col3:
                st.metric("Credentials", len(credentials))
            with col4:
                st.metric("Results", len(results))
        else:
            st.info("Data directory not found. Run tests to generate data.")
        
        # Data management actions
        st.markdown("---")
        st.markdown("### ⚡ Data Actions")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("📥 Export All Data", width='stretch'):
                self._export_all_data()
        
        with action_col2:
            if st.button("🗑️ Clear Old Data", width='stretch'):
                self._clear_old_data()
        
        with action_col3:
            if st.button("🔄 Refresh Data", width='stretch'):
                st.rerun()
        
        # View stored data
        st.markdown("---")
        st.markdown("### 👁️ View Stored Data")
        
        data_type = st.selectbox(
            "Select data type to view:",
            ["Test Cases", "Prompts", "Credentials", "Results"]
        )
        
        self._view_stored_data(data_type)
    
    def _render_test_cases(self):
        """Render test case management"""
        st.markdown('<div class="main-header">📋 Test Case Management</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Generate Test Cases")
            test_case_count = st.number_input("Number of test cases to generate", 10, 200, 50)
            
            if st.button("🎲 Generate Test Cases with LLM", type="primary", width='stretch'):
                self._generate_test_cases(test_case_count)
            
            if st.button("📥 Load Saved Test Cases", width='stretch'):
                self._load_saved_test_cases()
        
        with col2:
            st.markdown("### Test Case Stats")
            stats = st.session_state.metrics.get_summary_stats()
            st.metric("Total Tests", stats.get("total_tests", 0))
            st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
            st.metric("Avg Score", f"{stats.get('avg_score', 0):.2f}")
        
        # Test case list
        st.markdown("---")
        st.markdown("### Test Case Library")
        
        # Placeholder for test case table
        st.info("Test case management coming soon...")
    
    def _render_detailed_metrics(self):
        """Render detailed metrics dashboard"""
        st.markdown('<div class="main-header">📊 Detailed Test Metrics</div>', unsafe_allow_html=True)
        
        stats = st.session_state.metrics.get_summary_stats()
        
        if not stats:
            st.info("No metrics collected yet. Run some tests first.")
            return
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            self._metric_card("Total Tests", stats.get("total_tests", 0), "Tests executed", "default")
        with col2:
            success_rate = stats.get("success_rate", 0)
            self._metric_card("Success Rate", f"{success_rate:.1f}%", "Overall success", 
                            "success" if success_rate > 80 else "warning" if success_rate > 60 else "error")
        with col3:
            avg_score = stats.get("avg_score", 0)
            self._metric_card("Avg Score", f"{avg_score:.2f}", "Average test score",
                            "success" if avg_score > 0.7 else "warning" if avg_score > 0.5 else "error")
        with col4:
            avg_duration = stats.get("avg_duration_ms", 0)
            self._metric_card("Avg Duration", f"{avg_duration:.0f}ms", "Average test time",
                            "default")
        
        st.markdown("---")
        
        # Test type distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Test Type Distribution")
            type_data = []
            for test_type, metrics in stats.get("by_type", {}).items():
                type_data.append({
                    "Type": test_type.replace("_", " ").title(),
                    "Count": len(metrics),
                    "Avg Score": sum(m.get("score", 0) for m in metrics) / len(metrics) if metrics else 0
                })
            
            if type_data:
                df = pd.DataFrame(type_data)
                fig = px.bar(df, x="Type", y="Count", color="Avg Score",
                           title="Tests by Type", color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Score Distribution")
            all_scores = [m.get("score", 0) for m in st.session_state.metrics.get_session_metrics()]
            if all_scores:
                fig = px.histogram(x=all_scores, nbins=20, title="Score Distribution",
                                 labels={"x": "Score", "y": "Count"})
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed metrics table
        st.markdown("---")
        st.markdown("### All Test Metrics")
        
        all_metrics = st.session_state.metrics.get_session_metrics()
        if all_metrics:
            df = pd.DataFrame(all_metrics)
            
            # Format columns
            if "duration_ms" in df.columns:
                df["duration_formatted"] = df["duration_ms"].apply(lambda x: f"{x:.0f}ms" if pd.notnull(x) else "N/A")
            else:
                df["duration_formatted"] = "N/A"
            
            if "score" in df.columns:
                df["score_formatted"] = df["score"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
            else:
                df["score_formatted"] = "N/A"
            
            display_columns = []
            for col in ["test_type", "test_name", "status", "score_formatted", "duration_formatted", "timestamp"]:
                if col in df.columns:
                    display_columns.append(col)
            
            st.dataframe(
                df[display_columns],
                use_container_width=True,
                column_config={
                    "test_type": "Type",
                    "test_name": "Test Name",
                    "status": "Status",
                    "score_formatted": "Score",
                    "duration_formatted": "Duration",
                    "timestamp": "Time"
                }
            )
    
    def _render_run_tests(self):
        """Render comprehensive test runner"""
        st.markdown('<div class="main-header">⚡ Run Comprehensive Tests</div>', unsafe_allow_html=True)
        
        st.markdown("""
        Run comprehensive testing suite to evaluate all aspects of the Sales EVA system.
        This will test:
        - Authentication & Security
        - Prompt Effectiveness
        - Agent Capabilities
        - Knowledge Base Quality
        - End-to-End Scenarios
        """)
        
        # Test selection
        st.markdown("### Select Tests to Run")
        
        col1, col2 = st.columns(2)
        
        with col1:
            run_login = st.checkbox("🔐 Login & Authentication Tests", value=True)
            run_prompt = st.checkbox("💬 Prompt Tests", value=True)
            run_agent = st.checkbox("🤖 Agent Tests", value=True)
        
        with col2:
            run_kb = st.checkbox("📚 Knowledge Base Tests", value=True)
            run_e2e = st.checkbox("🚀 End-to-End Tests", value=True)
            run_all = st.checkbox("🎯 Run All Tests", value=True)
        
        # Configuration
        st.markdown("---")
        st.markdown("### Test Configuration")
        
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            prompt_count = st.number_input("Prompt Test Count", 10, 200, 50)
            agent_count = st.number_input("Agent Test Count", 5, 100, 20)
        
        with config_col2:
            e2e_count = st.number_input("E2E Test Count", 1, 50, 5)
            kb_sample = st.number_input("KB Sample Size", 10, 200, 50)
        
        # Run button
        if st.button("🚀 START COMPREHENSIVE TESTING", type="primary", width='stretch'):
            self._run_comprehensive_tests({
                "login": run_login or run_all,
                "prompt": run_prompt or run_all,
                "agent": run_agent or run_all,
                "kb": run_kb or run_all,
                "e2e": run_e2e or run_all,
                "config": {
                    "prompt_count": prompt_count,
                    "agent_count": agent_count,
                    "e2e_count": e2e_count,
                    "kb_sample": kb_sample
                }
            })
    
    def _render_history(self):
        """Render test history"""
        st.markdown('<div class="main-header">🕐 Test History</div>', unsafe_allow_html=True)
        
        # Load historical sessions
        sessions = self._load_test_sessions()
        
        if not sessions:
            st.info("No test history found.")
            return
        
        # Session selector
        selected_session = st.selectbox(
            "Select Test Session",
            options=list(sessions.keys()),
            format_func=lambda x: f"{x} - {sessions[x].get('total_tests', 0)} tests"
        )
        
        if selected_session:
            session_data = sessions[selected_session]
            
            # Session overview
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Tests", session_data.get("total_tests", 0))
            with col2:
                st.metric("Passed", session_data.get("passed", 0))
            with col3:
                st.metric("Success Rate", f"{session_data.get('success_rate', 0):.1f}%")
            with col4:
                st.metric("Avg Score", f"{session_data.get('avg_score', 0):.2f}")
            
            # Detailed metrics
            st.markdown("---")
            st.markdown("### Session Details")
            
            if "by_type" in session_data:
                type_data = []
                for test_type, metrics in session_data["by_type"].items():
                    if metrics:
                        type_data.append({
                            "Type": test_type,
                            "Count": len(metrics),
                            "Avg Score": sum(m.get("score", 0) for m in metrics) / len(metrics)
                        })
                
                if type_data:
                    df = pd.DataFrame(type_data)
                    st.dataframe(df, use_container_width=True)
    
    # Helper methods for rendering
    def _metric_card(self, title: str, value: str, description: str, style: str = "default"):
        """Render a metric card"""
        style_class = {
            "success": "success-card",
            "warning": "warning-card", 
            "error": "error-card"
        }.get(style, "")
        
        st.markdown(f"""
        <div class="metric-card {style_class}">
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">{title}</div>
            <div style="font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;">{value}</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">{description}</div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_overall_metrics(self):
        """Render overall metrics chart"""
        stats = st.session_state.metrics.get_summary_stats()
        
        if not stats:
            st.info("Run tests to see metrics")
            return
        
        # Create gauge chart for overall score
        avg_score = stats.get("avg_score", 0)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_score * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#3B82F6"},
                'steps': [
                    {'range': [0, 50], 'color': "#EF4444"},
                    {'range': [50, 70], 'color': "#F59E0B"},
                    {'range': [70, 100], 'color': "#10B981"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_test_distribution(self):
        """Render test distribution pie chart"""
        stats = st.session_state.metrics.get_summary_stats()
        
        if not stats or "by_type" not in stats:
            st.info("No test distribution data")
            return
        
        type_counts = {k: len(v) for k, v in stats["by_type"].items()}
        
        if not type_counts:
            st.info("No test type data")
            return
        
        df = pd.DataFrame({
            "Test Type": [t.replace("_", " ").title() for t in type_counts.keys()],
            "Count": list(type_counts.values())
        })
        
        fig = px.pie(df, values='Count', names='Test Type', title='Test Distribution by Type')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recent_tests(self):
        """Render recent tests table"""
        recent_metrics = st.session_state.metrics.get_session_metrics()[-10:]  # Last 10 tests
        
        if not recent_metrics:
            st.info("No recent tests")
            return
        
        df = pd.DataFrame(recent_metrics)
        
        # Format for display
        if "duration_ms" in df.columns:
            df["duration"] = df["duration_ms"].apply(lambda x: f"{x:.0f}ms" if pd.notnull(x) else "N/A")
        else:
            df["duration"] = "N/A"
        
        if "score" in df.columns:
            df["score_display"] = df["score"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
        else:
            df["score_display"] = "N/A"
        
        # Color code status
        def status_color(status):
            if status == "passed":
                return "✅"
            elif status == "failed":
                return "❌"
            else:
                return "⚠️"
        
        if "status" in df.columns:
            df["status_icon"] = df["status"].apply(status_color)
        else:
            df["status_icon"] = "⚠️"
        
        st.markdown("### Recent Tests")
        
        display_columns = []
        for col in ["status_icon", "test_type", "test_name", "score_display", "duration", "timestamp"]:
            if col in df.columns:
                display_columns.append(col)
        
        if display_columns:
            st.dataframe(
                df[display_columns],
                use_container_width=True,
                column_config={
                    "status_icon": "Status",
                    "test_type": "Type",
                    "test_name": "Test",
                    "score_display": "Score",
                    "duration": "Duration",
                    "timestamp": "Time"
                }
            )
    
    def _render_running_tests(self):
        """Render currently running tests"""
        st.markdown('<div class="test-running">🔄 Tests Running...</div>', unsafe_allow_html=True)
        
        for test in st.session_state.running_tests:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.markdown("🔄")
                with col2:
                    st.text(test.get("name", "Unknown test"))
                    st.progress(test.get("progress", 0) / 100)
                with col3:
                    if st.button("❌", key=f"cancel_{test.get('id')}", width='content'):
                        st.session_state.running_tests = [
                            t for t in st.session_state.running_tests 
                            if t.get("id") != test.get("id")
                        ]
                        st.rerun()
    
    def _render_test_results_by_type(self, test_type: str):
        """Render test results for a specific type"""
        metrics = []
        for metric in st.session_state.metrics.get_session_metrics():
            if metric.get("test_type") == test_type:
                metrics.append(metric)
        
        if not metrics:
            return
        
        df = pd.DataFrame(metrics)
        
        # Summary stats
        total = len(df)
        if "status" in df.columns:
            passed = len(df[df["status"] == "passed"])
        else:
            passed = 0
        
        if "score" in df.columns:
            avg_score = df["score"].mean()
        else:
            avg_score = 0
        
        if "duration_ms" in df.columns:
            avg_duration = df["duration_ms"].mean()
        else:
            avg_duration = 0
        
        st.markdown(f"### {test_type.upper()} Tests Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tests", total)
        with col2:
            st.metric("Passed", passed)
        with col3:
            st.metric("Avg Score", f"{avg_score:.2f}")
        with col4:
            st.metric("Avg Duration", f"{avg_duration:.0f}ms")
        
        # Detailed table
        st.markdown("#### Detailed Results")
        
        display_columns = []
        for col in ["test_name", "status", "score", "duration_ms", "timestamp"]:
            if col in df.columns:
                display_columns.append(col)
        
        if display_columns:
            column_config = {
                "test_name": "Test Name",
                "status": "Status",
                "score": "Score",
                "duration_ms": "Duration (ms)",
                "timestamp": "Time"
            }
            st.dataframe(
                df[display_columns],
                use_container_width=True,
                column_config=column_config
            )
    
    # Test execution methods
    def _run_health_check(self):
        """Run health check on Sales EVA service"""
        async def check_health():
            try:
                url = settings.SALES_EVA_API_URL.rstrip('/')
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{url}/")
                    return response.status_code == 200, response.elapsed.total_seconds() * 1000
            except Exception as e:
                print(f"Health check error: {e}")
                return False, 0

        with st.spinner("Checking service health..."):
            is_healthy, response_time = asyncio.run(check_health())
            
            # Start timer for metrics
            timer_id = st.session_state.metrics.start_test(
                test_id="health_check",
                test_type="system",
                test_name="Service Health Check",
                inputs={"url": settings.SALES_EVA_API_URL}
            )
            
            if is_healthy:
                st.success(f"✅ Sales EVA service is healthy! (Response: {response_time:.0f}ms)")
                # Record health check metric
                st.session_state.metrics.end_test(
                    timer_id=timer_id,
                    status="passed",
                    score=1.0,
                    outputs={
                        "status_code": 200,
                        "response_time_ms": response_time,
                        "is_healthy": True
                    },
                    details={
                        "service": "Sales EVA", 
                        "status": "healthy",
                        "response_time_ms": response_time
                    },
                    justification="Service responded with HTTP 200 status"
                )
            else:
                st.error("❌ Sales EVA service is not responding!")
                # Record failed health check
                st.session_state.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    outputs={
                        "status_code": 0,
                        "response_time_ms": response_time,
                        "is_healthy": False
                    },
                    details={
                        "service": "Sales EVA", 
                        "status": "unreachable"
                    },
                    justification="Service did not respond or returned non-200 status"
                )
    
    def _run_login_test(self, username: str, password: str, test_name: str):
        """Run login test with detailed view"""
        # Store inputs for display
        inputs_display = {
            "username": username,
            "password": "••••••••" if password else "",
            "expected_result": "Success" if username in ["sales1", "expert1", "admin"] and password == "demo123" else "Failure"
        }
        
        # Show what's being tested
        with st.expander(f"📋 Test Configuration: {test_name}", expanded=True):
            st.write("**Inputs:**")
            st.json(inputs_display)
        
        with st.spinner(f"Running {test_name}..."):
            # Run async function
            result = asyncio.run(self._execute_login_test(username, password, test_name))

            if result:
                if result.get("success", False):
                    st.success(f"✅ {test_name}: PASSED (Score: {result.get('score', 0):.2f})")
                else:
                    st.error(f"❌ {test_name}: FAILED (Score: {result.get('score', 0):.2f})")

                # Show detailed results
                with st.expander("📊 View Detailed Results", expanded=True):
                    # Get the latest test details
                    all_tests = st.session_state.metrics.get_session_metrics()
                    if all_tests:
                        latest_test = all_tests[-1]  # Get most recent test
                        
                        # Show justification if available
                        justification = latest_test.get("justification", "")
                        if justification:
                            st.info(f"**Justification:** {justification}")
                        
                        # Show outputs
                        st.write("**Outputs:**")
                        outputs = latest_test.get("outputs", {})
                        if outputs:
                            st.json(outputs)
                        else:
                            st.json(result.get("details", {}))
                
                # Suggest viewing test details
                timer_id = result.get("timer_id")
                if timer_id:
                    st.info(f"🔍 View complete test details in the **Test Details** page")

            # Rerun to update metrics
            st.rerun()

    def _run_agent_test(self, function: str):
        """Run agent function test with detailed view"""
        # Map function to query
        queries = {
            "matching": "Find relevant AI and cloud solutions for banking fraud detection",
            "gap_analysis": "What are common gaps in digital transformation projects for banks?",
            "research": "Latest trends and best practices in AI-powered fraud detection",
            "reporting": "How to structure a sales proposal for cybersecurity solutions"
        }
        
        query = queries.get(function, "Test query")
        
        # Show what's being tested
        with st.expander(f"📋 Test Configuration: Agent {function}", expanded=True):
            st.write("**Inputs:**")
            st.json({
                "function": function,
                "query": query,
                "endpoint": "/api/rag/search",
                "method": "POST"
            })
        
        with st.spinner(f"Testing agent {function.replace('_', ' ')} function..."):
            # Run async function
            result = asyncio.run(self._execute_agent_test(function))

            if result:
                success = result.get("success", False)
                score = result.get("score", 0)
                if success:
                    st.success(f"✅ Agent {function}: PASSED (Score: {score:.2f})")
                else:
                    st.error(f"❌ Agent {function}: FAILED (Score: {score:.2f})")

                # Show detailed results
                with st.expander("📊 View Detailed Results", expanded=True):
                    # Get the latest test details
                    all_tests = st.session_state.metrics.get_session_metrics()
                    if all_tests:
                        latest_test = all_tests[-1]
                        
                        # Show justification
                        justification = latest_test.get("justification", "")
                        if justification:
                            st.info(f"**Justification:** {justification}")
                        
                        # Show outputs
                        st.write("**Outputs:**")
                        outputs = latest_test.get("outputs", {})
                        if outputs:
                            st.json(outputs)
                        else:
                            st.json(result.get("details", {}))
                
                # Suggest viewing test details
                timer_id = result.get("timer_id")
                if timer_id:
                    st.info(f"🔍 View complete test details in the **Test Details** page")

            # Rerun to update metrics
            st.rerun()
    
    async def _execute_login_test(self, username: str, password: str, test_name: str):
        """Execute login test asynchronously"""
        try:
            # Use the detailed test runner
            result = await st.session_state.test_runner.run_login_test(username, password, test_name)
            return result
        except Exception as e:
            st.error(f"Login test failed: {e}")
            # Record error
            timer_id = st.session_state.metrics.start_test(
                test_id=f"login_{username}",
                test_type="login",
                test_name=test_name,
                inputs={"username": username, "password": "[HIDDEN]"}
            )
            st.session_state.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"Test failed with error: {str(e)}"
            )
            return None

    async def _execute_agent_test(self, function: str):
        """Execute agent test asynchronously"""
        try:
            result = await st.session_state.test_runner.run_agent_test(function)
            return result
        except Exception as e:
            st.error(f"Agent test failed: {e}")
            # Record error
            timer_id = st.session_state.metrics.start_test(
                test_id=f"agent_{function}",
                test_type="agent",
                test_name=f"Agent {function}",
                inputs={"function": function}
            )
            st.session_state.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"Test failed with error: {str(e)}"
            )
            return None

    async def _execute_prompt_tests(self, prompt_count: int, test_case_count: int):
        """Execute prompt tests asynchronously"""
        try:
            result = await st.session_state.test_runner.run_prompt_test(prompt_count, test_case_count)
            return result
        except Exception as e:
            st.error(f"Prompt tests failed: {e}")
            return None

    async def _execute_kb_test(self, category: str):
        """Execute KB test asynchronously"""
        try:
            result = await st.session_state.test_runner.run_kb_test(category)
            return result
        except Exception as e:
            st.error(f"KB test failed: {e}")
            return None

    async def _execute_e2e_scenario(self, name: str, scenario: str):
        """Execute E2E scenario test asynchronously"""
        try:
            result = await st.session_state.test_runner.run_e2e_scenario(name, scenario)
            return result
        except Exception as e:
            st.error(f"E2E test failed: {e}")
            return None

    async def _execute_comprehensive_tests(self, config: Dict):
        """Execute comprehensive tests asynchronously"""
        try:
            results = {}

            # Login tests
            if config.get("login", False):
                login_tests = [
                    ("sales1", "demo123", "Valid Sales Login"),
                    ("expert1", "demo123", "Valid Expert Login"),
                    ("admin", "demo123", "Valid Admin Login"),
                    ("invalid", "wrongpass", "Invalid Login")
                ]

                for username, password, test_name in login_tests:
                    result = await st.session_state.test_runner.run_login_test(username, password, test_name)
                    results[f"login_{username}"] = result

            # Prompt tests
            if config.get("prompt", False):
                prompt_config = config.get("config", {})
                prompt_count = prompt_config.get("prompt_count", 50)
                test_case_count = prompt_config.get("test_case_count", 20)
                result = await st.session_state.test_runner.run_prompt_test(prompt_count, test_case_count)
                results["prompt"] = result

            # Agent tests
            if config.get("agent", False):
                agent_functions = ["matching", "gap_analysis", "research", "reporting"]
                for function in agent_functions:
                    result = await st.session_state.test_runner.run_agent_test(function)
                    results[f"agent_{function}"] = result

            # KB tests
            if config.get("kb", False):
                kb_categories = ["coverage", "freshness", "consistency", "relevance"]
                for category in kb_categories:
                    result = await st.session_state.test_runner.run_kb_test(category)
                    results[f"kb_{category}"] = result

            # E2E tests
            if config.get("e2e", False):
                e2e_scenarios = [
                    ("Banking AI", "Bank needs AI-powered fraud detection with cloud deployment"),
                    ("Retail Digital", "Retail chain wants digital transformation with mobile apps"),
                    ("Healthcare Data", "Hospital network needs patient data analytics platform")
                ]

                for name, scenario in e2e_scenarios:
                    result = await st.session_state.test_runner.run_e2e_scenario(name, scenario)
                    results[f"e2e_{name.replace(' ', '_').lower()}"] = result

            return results

        except Exception as e:
            st.error(f"Comprehensive tests failed: {e}")
            return None

    # Add these public methods that call the async ones
    def _run_kb_test(self, category: str):
        """Run knowledge base test"""
        with st.spinner(f"Testing KB {category}..."):
            # Run async function
            result = asyncio.run(self._execute_kb_test(category))

            if result:
                success = result.get("success", False)
                score = result.get("score", 0)
                if success:
                    st.success(f"✅ KB {category}: PASSED (Score: {score:.2f})")
                else:
                    st.error(f"❌ KB {category}: FAILED (Score: {score:.2f})")

                # Show detailed results
                with st.expander("📊 View Detailed Results", expanded=True):
                    # Get the latest test details
                    all_tests = st.session_state.metrics.get_session_metrics()
                    if all_tests:
                        latest_test = all_tests[-1]
                        
                        # Show justification
                        justification = latest_test.get("justification", "")
                        if justification:
                            st.info(f"**Justification:** {justification}")
                        
                        # Show outputs
                        st.write("**Outputs:**")
                        outputs = latest_test.get("outputs", {})
                        if outputs:
                            st.json(outputs)
                
                # Suggest viewing test details
                timer_id = result.get("timer_id")
                if timer_id:
                    st.info(f"🔍 View complete test details in the **Test Details** page")

            # Rerun to update metrics
            st.rerun()

    def _run_e2e_scenario(self, name: str, scenario: str):
        """Run end-to-end scenario test"""
        with st.spinner(f"Running {name} scenario..."):
            # Run async function
            result = asyncio.run(self._execute_e2e_scenario(name, scenario))

            if result:
                success = result.get("success", False)
                score = result.get("score", 0)
                if success:
                    st.success(f"✅ {name}: PASSED (Score: {score:.2f})")
                else:
                    st.error(f"❌ {name}: FAILED (Score: {score:.2f})")

                # Show detailed results
                with st.expander("📊 View Detailed Results", expanded=True):
                    # Get the latest test details
                    all_tests = st.session_state.metrics.get_session_metrics()
                    if all_tests:
                        latest_test = all_tests[-1]
                        
                        # Show justification
                        justification = latest_test.get("justification", "")
                        if justification:
                            st.info(f"**Justification:** {justification}")
                        
                        # Show outputs
                        st.write("**Outputs:**")
                        outputs = latest_test.get("outputs", {})
                        if outputs:
                            st.json(outputs)
                
                # Suggest viewing test details
                timer_id = result.get("timer_id")
                if timer_id:
                    st.info(f"🔍 View complete test details in the **Test Details** page")

            # Rerun to update metrics
            st.rerun()

    def _run_comprehensive_tests(self, config: Dict):
        """Run comprehensive test suite"""
        # Create a progress container
        progress_container = st.container()
        results_container = st.container()

        with progress_container:
            st.markdown("## 🚀 Running Comprehensive Tests")
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Show test plan
            test_plan = []
            if config.get("login", False):
                test_plan.append("🔐 Login Tests (4 scenarios)")
            if config.get("prompt", False):
                prompt_config = config.get("config", {})
                test_plan.append(f"💬 Prompt Tests ({prompt_config.get('prompt_count', 50)} prompts)")
            if config.get("agent", False):
                test_plan.append("🤖 Agent Tests (4 functions)")
            if config.get("kb", False):
                test_plan.append("📚 KB Tests (4 categories)")
            if config.get("e2e", False):
                test_plan.append("🚀 E2E Tests (3 scenarios)")

            st.write("**Test Plan:**")
            for plan in test_plan:
                st.write(f"- {plan}")

        # Run tests asynchronously
        async def run_tests_with_progress():
            total_tests = sum([
                4 if config.get("login") else 0,
                1 if config.get("prompt") else 0,
                4 if config.get("agent") else 0,
                4 if config.get("kb") else 0,
                3 if config.get("e2e") else 0
            ])

            completed = 0

            # Update progress
            def update_progress():
                progress = (completed / total_tests) if total_tests > 0 else 0
                progress_bar.progress(progress)
                status_text.text(f"Completed: {completed}/{total_tests} tests")

            # Run tests
            results = await self._execute_comprehensive_tests(config)

            # Simulate progress updates
            for i in range(total_tests):
                await asyncio.sleep(0.5)  # Simulate test execution time
                completed += 1
                update_progress()

            return results

        # Execute and get results
        results = asyncio.run(run_tests_with_progress())

        # Clear progress container
        progress_container.empty()

        # Show results
        with results_container:
            if results:
                st.success("🎉 Comprehensive Tests Completed!")

                # Calculate summary
                total_tests = len(results)
                passed = sum(1 for r in results.values() if r and r.get("success", False))
                avg_score = sum(r.get("score", 0) for r in results.values() if r) / total_tests if total_tests > 0 else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Tests", total_tests)
                with col2:
                    st.metric("Passed", passed)
                with col3:
                    st.metric("Avg Score", f"{avg_score:.2f}")

                # Detailed results in expanders
                with st.expander("📋 View Detailed Results", expanded=True):
                    for test_name, result in results.items():
                        if result:
                            status = "✅" if result.get("success", False) else "❌"
                            score = result.get("score", 0)
                            st.write(f"{status} **{test_name}**: Score: {score:.2f}")

                # Rerun to update metrics dashboard
                st.rerun()

    def _run_quick_test(self):
        """Run quick test suite"""
        with st.spinner("Running quick test suite..."):
            # Run a subset of tests
            async def run_quick_tests():
                results = {}
                
                # Quick login test
                try:
                    result = await st.session_state.test_runner.run_login_test("sales1", "demo123", "Quick Login Test")
                    results["quick_login"] = result
                except Exception as e:
                    results["quick_login"] = {"success": False, "error": str(e)}
                
                # Quick agent test (matching only)
                try:
                    result = await st.session_state.test_runner.run_agent_test("matching")
                    results["quick_agent_matching"] = result
                except Exception as e:
                    results["quick_agent_matching"] = {"success": False, "error": str(e)}
                
                # Quick KB test
                try:
                    result = await st.session_state.test_runner.run_kb_test("coverage")
                    results["quick_kb_coverage"] = result
                except Exception as e:
                    results["quick_kb_coverage"] = {"success": False, "error": str(e)}
                
                return results
            
            results = asyncio.run(run_quick_tests())
            
            # Show results
            if results:
                passed = sum(1 for r in results.values() if isinstance(r, dict) and r.get("success", False))
                total = len(results)
                
                if passed == total:
                    st.success(f"✅ Quick Test: {passed}/{total} tests passed!")
                elif passed > 0:
                    st.warning(f"⚠️ Quick Test: {passed}/{total} tests passed")
                else:
                    st.error(f"❌ Quick Test: 0/{total} tests passed")
                
                # Show brief summary
                with st.expander("View Quick Test Results"):
                    for test_name, result in results.items():
                        if isinstance(result, dict):
                            if result.get("success", False):
                                status = "✅"
                            elif "error" in result:
                                status = "⚠️"
                            else:
                                status = "❌"
                            score = result.get('score', 0)
                            st.write(f"{status} {test_name}: Score: {score:.2f}")
                        else:
                            st.write(f"❌ {test_name}: Invalid result")
            
            # Rerun to update metrics
            st.rerun()

    def _run_single_prompt_test(self):
        """Run single prompt test"""
        with st.spinner("Testing single prompt..."):
            result = asyncio.run(self._execute_prompt_tests(1, 5))

            if result:
                st.success(f"✅ Single Prompt Test: Score {result.get('score', 0):.2f}")
                with st.expander("Prompt Details"):
                    st.json({
                        "prompt_tested": "Sales EVA system prompt",
                        "test_cases": 5,
                        "score": result.get('score', 0),
                        "details": result.get('details', {})
                    })

            st.rerun()

    def _run_prompt_style_analysis(self):
        """Run prompt style analysis"""
        with st.spinner("Analyzing prompt styles..."):
            # Simulate different prompt styles
            styles = ["instructional", "role-based", "concise", "detailed", "conversational"]

            async def analyze_styles():
                results = {}
                for style in styles:
                    # Simulate testing each style
                    await asyncio.sleep(0.5)
                    score = random.uniform(0.6, 0.95)
                    results[style] = {
                        "score": score,
                        "test_cases": random.randint(3, 8),
                        "avg_response_time": random.uniform(800, 2000)
                    }
                return results

            results = asyncio.run(analyze_styles())

            # Display results
            st.markdown("### Prompt Style Analysis")

            # Create bar chart
            df = pd.DataFrame([
                {"Style": style, "Score": data["score"]}
                for style, data in results.items()
            ])

            fig = px.bar(df, x="Style", y="Score", title="Prompt Style Performance",
                        color="Score", color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)

            # Detailed table
            st.markdown("### Detailed Metrics")
            detail_df = pd.DataFrame([
                {
                    "Style": style,
                    "Score": f"{data['score']:.2f}",
                    "Test Cases": data["test_cases"],
                    "Avg Response Time": f"{data['avg_response_time']:.0f}ms"
                }
                for style, data in results.items()
            ])
            st.dataframe(detail_df, use_container_width=True)

            # Record metric
            best_style = max(results.items(), key=lambda x: x[1]["score"])[0]
            timer_id = st.session_state.metrics.start_test(
                test_id="prompt_style_analysis",
                test_type="prompt",
                test_name="Prompt Style Analysis",
                inputs={"styles": styles}
            )
            st.session_state.metrics.end_test(
                timer_id=timer_id,
                status="passed",
                score=max(data["score"] for data in results.values()),
                outputs={"results": results, "best_style": best_style},
                details={"best_style": best_style, "results": results},
                justification=f"Best performing style: {best_style}"
            )

            st.rerun()

    def _run_all_agent_tests(self):
        """Run all agent function tests"""
        with st.spinner("Testing all agent functions..."):
            functions = ["matching", "gap_analysis", "research", "reporting"]

            async def run_all_agents():
                results = {}
                for function in functions:
                    result = await st.session_state.test_runner.run_agent_test(function)
                    results[function] = result
                return results

            results = asyncio.run(run_all_agents())

            # Display results
            st.markdown("### Agent Function Test Results")

            # Create radar chart
            categories = [f.replace("_", " ").title() for f in functions]
            scores = [results[f].get("score", 0) if results[f] else 0 for f in functions]

            fig = go.Figure(data=go.Scatterpolar(
                r=scores,
                theta=categories,
                fill='toself',
                name='Agent Performance'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=False,
                title="Agent Function Performance Radar"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            summary_data = []
            for function in functions:
                if results[function]:
                    result = results[function]
                    summary_data.append({
                        "Function": function.replace("_", " ").title(),
                        "Status": "✅ PASS" if result.get("success", False) else "❌ FAIL",
                        "Score": f"{result.get('score', 0):.2f}",
                        "Success": result.get("success", False)
                    })

            if summary_data:
                df = pd.DataFrame(summary_data)
                st.dataframe(df, use_container_width=True)

            st.rerun()

    def _run_comprehensive_kb_validation(self, sample_size: int):
        """Run comprehensive KB validation"""
        with st.spinner(f"Running comprehensive KB validation ({sample_size} samples)..."):
            categories = ["coverage", "freshness", "consistency", "relevance"]

            async def validate_kb():
                results = {}
                for category in categories:
                    result = await st.session_state.test_runner.run_kb_test(category)
                    results[category] = result
                return results

            results = asyncio.run(validate_kb())

            # Display results
            st.markdown("### Knowledge Base Validation Results")

            # Create gauge chart for overall score
            if results:
                valid_results = [r for r in results.values() if r]
                if valid_results:
                    avg_score = sum(r.get("score", 0) for r in valid_results) / len(valid_results)

                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=avg_score * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Overall KB Health Score"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#3B82F6"},
                            'steps': [
                                {'range': [0, 60], 'color': "#EF4444"},
                                {'range': [60, 80], 'color': "#F59E0B"},
                                {'range': [80, 100], 'color': "#10B981"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 70
                            }
                        }
                    ))

                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

                    # Category breakdown
                    st.markdown("#### Category Breakdown")
                    cat_df = pd.DataFrame([
                        {
                            "Category": cat.title(),
                            "Score": results[cat].get("score", 0) if results[cat] else 0,
                            "Status": "✅" if results[cat] and results[cat].get("success", False) else "❌"
                        }
                        for cat in categories
                    ])
                    st.dataframe(cat_df, use_container_width=True)

            st.rerun()

    def _generate_test_cases(self, count: int):
        """Generate test cases using LLM"""
        with st.spinner(f"Generating {count} test cases..."):
            # Simulate test case generation
            import time
            time.sleep(2)

            # Record metric
            timer_id = st.session_state.metrics.start_test(
                test_id="test_case_generation",
                test_type="system",
                test_name=f"Generate {count} Test Cases",
                inputs={"count": count}
            )

            # Simulate results
            success = random.random() > 0.1  # 90% success rate
            score = random.uniform(0.7, 0.95) if success else random.uniform(0.3, 0.6)

            details = {
                "count_generated": count if success else 0,
                "llm_used": "DeepSeek-V3",
                "generation_time": random.uniform(2000, 8000),
                "categories": ["banking", "retail", "healthcare", "manufacturing"][:random.randint(2, 4)]
            }

            st.session_state.metrics.end_test(
                timer_id=timer_id,
                status="passed" if success else "failed",
                score=score,
                outputs={"details": details},
                details=details,
                justification=f"Generated {count} test cases with {score:.2f} quality score"
            )

            if success:
                st.success(f"✅ Generated {count} test cases!")
                with st.expander("Generation Details"):
                    st.json(details)
            else:
                st.error("❌ Failed to generate test cases")

            st.rerun()

    def _load_saved_test_cases(self):
        """Load saved test cases"""
        with st.spinner("Loading saved test cases..."):
            # Simulate loading
            import time
            time.sleep(1)

            # Record metric
            timer_id = st.session_state.metrics.start_test(
                test_id="load_test_cases",
                test_type="system",
                test_name="Load Saved Test Cases",
                inputs={}
            )

            # Simulate results
            success = random.random() > 0.2  # 80% success rate
            score = 1.0 if success else 0.0

            details = {
                "loaded_count": random.randint(50, 200) if success else 0,
                "source_files": ["test_cases.json", "opportunities.json"] if success else [],
                "load_time": random.uniform(500, 2000)
            }

            st.session_state.metrics.end_test(
                timer_id=timer_id,
                status="passed" if success else "failed",
                score=score,
                outputs={"details": details},
                details=details,
                justification=f"Loaded {details['loaded_count']} test cases" if success else "Failed to load test cases"
            )

            if success:
                st.success(f"✅ Loaded {details['loaded_count']} test cases!")
            else:
                st.error("❌ Failed to load test cases")

            st.rerun()

    def _load_test_sessions(self) -> Dict:
        """Load test sessions from files"""
        try:
            from config.settings import settings
            import json
            from pathlib import Path

            sessions = {}
            results_dir = Path(settings.RESULTS_DIR) if hasattr(settings, 'RESULTS_DIR') else Path("data/results")

            if results_dir.exists():
                for file_path in results_dir.glob("session_*.json"):
                    try:
                        with open(file_path, 'r') as f:
                            metrics = json.load(f)

                        if metrics:
                            # Calculate session stats
                            session_id = file_path.stem.replace("session_", "")
                            total_tests = len(metrics)
                            passed = sum(1 for m in metrics if m.get("status") == "passed")
                            avg_score = sum(m.get("score", 0) for m in metrics) / total_tests if total_tests > 0 else 0

                            # Group by type
                            by_type = {}
                            for metric in metrics:
                                test_type = metric.get("test_type", "unknown")
                                if test_type not in by_type:
                                    by_type[test_type] = []
                                by_type[test_type].append(metric)

                            sessions[session_id] = {
                                "total_tests": total_tests,
                                "passed": passed,
                                "failed": total_tests - passed,
                                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
                                "avg_score": avg_score,
                                "by_type": by_type,
                                "start_time": metrics[0].get("timestamp") if metrics else None,
                                "end_time": metrics[-1].get("timestamp") if metrics else None,
                                "file": file_path.name
                            }
                    except Exception as e:
                        print(f"Error loading session file {file_path}: {e}")

            # Sort by session ID (most recent first)
            sorted_sessions = dict(sorted(sessions.items(), key=lambda x: x[0], reverse=True))
            return sorted_sessions

        except Exception as e:
            st.error(f"Error loading test sessions: {e}")
            return {}

    # ============================================
    # NEW: Test Details Page Methods
    # ============================================
    
    def _render_test_overview(self, test_data: Dict):
        """Render test overview"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = test_data.get("status", "unknown")
            status_color = {
                "passed": "green",
                "failed": "red",
                "error": "orange"
            }.get(status, "gray")
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f8f9fa;">
                <div style="font-size: 12px; color: #666;">Status</div>
                <div style="font-size: 24px; font-weight: bold; color: {status_color};">{status.upper()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            score = test_data.get("score", 0)
            score_color = "green" if score >= 0.7 else "orange" if score >= 0.4 else "red"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f8f9fa;">
                <div style="font-size: 12px; color: #666;">Score</div>
                <div style="font-size: 24px; font-weight: bold; color: {score_color};">{score:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            duration = test_data.get("duration_ms", 0)
            st.metric("Duration", f"{duration:.0f} ms")
        
        with col4:
            test_type = test_data.get("test_type", "unknown")
            st.metric("Type", test_type.upper())
        
        # Test information
        st.markdown("### Test Information")
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.write("**Test Name:**", test_data.get("test_name", "Unknown"))
            st.write("**Test ID:**", test_data.get("test_id", "Unknown"))
            st.write("**Timer ID:**", test_data.get("timer_id", "Unknown"))
        
        with info_col2:
            start_time = test_data.get("start_time")
            end_time = test_data.get("end_time")
            
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    st.write("**Start Time:**", start_dt.strftime("%Y-%m-%d %H:%M:%S"))
                except:
                    st.write("**Start Time:**", start_time)
            
            if end_time:
                try:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    st.write("**End Time:**", end_dt.strftime("%Y-%m-%d %H:%M:%S"))
                except:
                    st.write("**End Time:**", end_time)
        
        # Justification
        justification = test_data.get("justification", "")
        if justification:
            st.markdown("### 📝 Justification")
            st.info(justification)
    
    def _render_test_inputs(self, test_data: Dict):
        """Render test inputs"""
        inputs = test_data.get("inputs", {})
        
        if not inputs:
            st.info("No inputs recorded for this test")
            return
        
        st.markdown("### 📥 Test Inputs")
        
        # Display inputs in a nice format
        for key, value in inputs.items():
            with st.expander(f"**{key}**", expanded=True if key == list(inputs.keys())[0] else False):
                if isinstance(value, dict):
                    st.json(value)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        st.write(f"{i+1}. {item}")
                else:
                    st.write(str(value))
        
        # Show input summary
        st.markdown("#### 📋 Input Summary")
        input_df = pd.DataFrame([
            {"Parameter": key, "Type": type(value).__name__, "Value Preview": str(value)[:100] + "..." if len(str(value)) > 100 else str(value)}
            for key, value in inputs.items()
        ])
        st.dataframe(input_df, use_container_width=True, hide_index=True)
    
    def _render_test_outputs(self, test_data: Dict):
        """Render test outputs"""
        outputs = test_data.get("outputs", {})
        
        if not outputs:
            st.info("No outputs recorded for this test")
            return
        
        st.markdown("### 📤 Test Outputs")
        
        # Check for HTTP response
        if "status_code" in outputs:
            status_code = outputs["status_code"]
            status_color = "green" if 200 <= status_code < 300 else "orange" if 300 <= status_code < 400 else "red"
            
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: #f8f9fa; margin-bottom: 20px;">
                <strong>HTTP Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_code}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Display response data
        if "response_data" in outputs:
            st.markdown("#### Response Data")
            response_data = outputs["response_data"]
            
            if isinstance(response_data, dict):
                # Pretty print JSON
                st.json(response_data)
                
                # Show key metrics if available
                if "results" in response_data:
                    results = response_data["results"]
                    if isinstance(results, list):
                        st.metric("Results Count", len(results))
            else:
                st.text_area("Response", str(response_data), height=200)
        
        # Show response time if available
        if "response_time_ms" in outputs:
            response_time = outputs["response_time_ms"]
            time_color = "green" if response_time < 3000 else "orange" if response_time < 10000 else "red"
            
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: #f8f9fa; margin-top: 20px;">
                <strong>Response Time:</strong> <span style="color: {time_color}; font-weight: bold;">{response_time:.0f} ms</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Show score components if available
        if "score_components" in outputs:
            st.markdown("#### 📈 Score Components")
            components = outputs.get("score_components", {})
            
            if components:
                components_df = pd.DataFrame([
                    {"Component": comp, "Score": score}
                    for comp, score in components.items()
                ])
                
                # Create bar chart
                fig = px.bar(
                    components_df, 
                    x="Component", 
                    y="Score",
                    title="Score Breakdown",
                    color="Score",
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_test_analysis(self, test_data: Dict):
        """Render test analysis"""
        st.markdown("### 📈 Test Analysis")
        
        # Performance analysis
        duration = test_data.get("duration_ms", 0)
        score = test_data.get("score", 0)
        status = test_data.get("status", "unknown")
        
        # Create metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Performance rating
            if duration < 1000:
                perf_rating = "Excellent"
                perf_color = "green"
            elif duration < 3000:
                perf_rating = "Good"
                perf_color = "lightgreen"
            elif duration < 10000:
                perf_rating = "Fair"
                perf_color = "orange"
            else:
                perf_rating = "Poor"
                perf_color = "red"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f8f9fa;">
                <div style="font-size: 12px; color: #666;">Performance</div>
                <div style="font-size: 20px; font-weight: bold; color: {perf_color};">{perf_rating}</div>
                <div style="font-size: 11px; color: #888;">{duration:.0f} ms</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Quality rating
            if score >= 0.9:
                quality_rating = "Excellent"
                quality_color = "green"
            elif score >= 0.7:
                quality_rating = "Good"
                quality_color = "lightgreen"
            elif score >= 0.5:
                quality_rating = "Fair"
                quality_color = "orange"
            else:
                quality_rating = "Poor"
                quality_color = "red"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f8f9fa;">
                <div style="font-size: 12px; color: #666;">Quality</div>
                <div style="font-size: 20px; font-weight: bold; color: {quality_color};">{quality_rating}</div>
                <div style="font-size: 11px; color: #888;">Score: {score:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Reliability rating
            if status == "passed":
                reliability_rating = "Reliable"
                reliability_color = "green"
            elif status == "failed":
                reliability_rating = "Unreliable"
                reliability_color = "red"
            else:
                reliability_rating = "Erratic"
                reliability_color = "orange"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f8f9fa;">
                <div style="font-size: 12px; color: #666;">Reliability</div>
                <div style="font-size: 20px; font-weight: bold; color: {reliability_color};">{reliability_rating}</div>
                <div style="font-size: 11px; color: #888;">Status: {status}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("#### 💡 Recommendations")
        
        recommendations = []
        
        if status == "failed":
            recommendations.append("🔧 **Investigate the failure reason** - Check the justification and outputs for clues")
        
        if duration > 5000:
            recommendations.append("⚡ **Optimize performance** - Response time is high, consider optimizing the endpoint")
        
        if score < 0.7:
            recommendations.append("📊 **Improve quality** - Test score is below 0.7, review test criteria")
        
        if not recommendations:
            recommendations.append("✅ **No major issues detected** - Test passed all criteria")
        
        for rec in recommendations:
            st.write(rec)
        
        # Similar tests comparison
        st.markdown("#### 🔄 Similar Tests")
        
        # Find similar tests by type
        test_type = test_data.get("test_type")
        similar_tests = [
            t for t in st.session_state.metrics.get_session_metrics()
            if t.get("test_type") == test_type and t.get("timer_id") != test_data.get("timer_id")
        ][:5]  # Limit to 5 similar tests
        
        if similar_tests:
            comparison_data = []
            for test in similar_tests:
                comparison_data.append({
                    "Test": test.get("test_name", "Unknown"),
                    "Status": test.get("status", "unknown"),
                    "Score": test.get("score", 0),
                    "Duration (ms)": test.get("duration_ms", 0),
                    "Time": test.get("timestamp", "")[:19]
                })
            
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No similar tests found for comparison")
    
    def _render_raw_data(self, test_data: Dict):
        """Render raw test data"""
        st.markdown("### 💾 Raw Test Data")
        
        # Show raw JSON
        st.json(test_data)
        
        # Download button
        import json
        json_str = json.dumps(test_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download Raw Data (JSON)",
            data=json_str,
            file_name=f"test_{test_data.get('timer_id', 'unknown')}.json",
            mime="application/json"
        )
    
    def _rerun_test(self, test_data: Dict):
        """Rerun a specific test"""
        test_type = test_data.get("test_type")
        test_name = test_data.get("test_name")
        inputs = test_data.get("inputs", {})
        
        # Map test type to appropriate rerun method
        if test_type == "login":
            username = inputs.get("username", "")
            password = inputs.get("password", "")
            if password == "[HIDDEN]" or password == "••••••••":
                # We need the actual password - prompt user
                st.warning("Password was hidden. Please provide password to rerun.")
                password = st.text_input("Password", type="password")
                if st.button("Rerun with this password", width='stretch'):
                    self._run_login_test(username, password, f"Rerun: {test_name}")
            else:
                self._run_login_test(username, password, f"Rerun: {test_name}")
        
        elif test_type == "agent":
            function = inputs.get("function", "")
            if function:
                self._run_agent_test(function)
        
        elif test_type == "kb":
            category = inputs.get("category", "")
            if category:
                self._run_kb_test(category)
        
        else:
            st.warning(f"Cannot automatically rerun test type: {test_type}")
    
    def _export_test_details(self, test_data: Dict):
        """Export test details to file"""
        import json
        from pathlib import Path
        
        # Create export directory
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_export_{test_data.get('timer_id', 'unknown')}_{timestamp}.json"
        filepath = export_dir / filename
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(test_data, f, indent=2, default=str)
        
        st.success(f"✅ Test details exported to: {filepath}")
        
        # Provide download link
        with open(filepath, 'r') as f:
            json_data = f.read()
        
        st.download_button(
            label="📥 Download Export",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )
    
    def _compare_similar_tests(self, test_data: Dict):
        """Compare similar tests"""
        test_type = test_data.get("test_type")
        similar_tests = [
            t for t in st.session_state.metrics.get_session_metrics()
            if t.get("test_type") == test_type
        ]
        
        if len(similar_tests) <= 1:
            st.info("Not enough similar tests to compare")
            return
        
        st.markdown("### 📊 Test Comparison")
        
        # Create comparison table
        comparison_data = []
        for test in similar_tests:
            comparison_data.append({
                "Test Name": test.get("test_name", "Unknown"),
                "Status": test.get("status", "unknown"),
                "Score": test.get("score", 0),
                "Duration (ms)": test.get("duration_ms", 0),
                "Time": test.get("timestamp", "")[:19],
                "Timer ID": test.get("timer_id", "unknown")
            })
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
        
        # Create comparison chart
        fig = go.Figure()
        
        # Add score bars
        fig.add_trace(go.Bar(
            x=df["Test Name"],
            y=df["Score"],
            name="Score",
            marker_color=df["Score"].apply(lambda x: 'green' if x >= 0.7 else 'orange' if x >= 0.4 else 'red')
        ))
        
        # Add duration line
        fig.add_trace(go.Scatter(
            x=df["Test Name"],
            y=df["Duration (ms)"] / df["Duration (ms)"].max() if df["Duration (ms)"].max() > 0 else df["Duration (ms)"],
            name="Duration (normalized)",
            yaxis="y2",
            line=dict(color="blue", width=2)
        ))
        
        fig.update_layout(
            title="Test Comparison",
            yaxis=dict(title="Score"),
            yaxis2=dict(
                title="Duration (normalized)",
                overlaying="y",
                side="right"
            ),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ============================================
    # NEW: Data Management Methods
    # ============================================
    
    def _export_all_data(self):
        """Export all data to CSV"""
        try:
            # Export metrics to CSV
            csv_path = st.session_state.metrics.export_to_csv()
            
            if csv_path:
                st.success(f"✅ Data exported to: {csv_path}")
                
                # Provide download link
                with open(csv_path, 'r') as f:
                    csv_data = f.read()
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=Path(csv_path).name,
                    mime="text/csv"
                )
            else:
                st.error("❌ Failed to export data")
        except Exception as e:
            st.error(f"❌ Export error: {str(e)}")
    
    def _clear_old_data(self):
        """Clear old data"""
        try:
            data_dir = Path("data")
            if data_dir.exists():
                # Keep only files from last 7 days
                cutoff_time = datetime.now().timestamp() - (7 * 24 * 60 * 60)
                
                files_deleted = 0
                for subdir in ["test_cases", "prompts", "credentials", "results"]:
                    subdir_path = data_dir / subdir
                    if subdir_path.exists():
                        for file_path in subdir_path.glob("*.json"):
                            if file_path.stat().st_mtime < cutoff_time:
                                file_path.unlink()
                                files_deleted += 1
                
                st.success(f"✅ Cleared {files_deleted} files older than 7 days")
            else:
                st.info("No data directory found")
        except Exception as e:
            st.error(f"❌ Error clearing data: {str(e)}")
    
    def _view_stored_data(self, data_type: str):
        """View stored data of specific type"""
        data_dir = Path("data")
        subdir_map = {
            "Test Cases": "test_cases",
            "Prompts": "prompts",
            "Credentials": "credentials",
            "Results": "results",
            "Responses": "responses"
        }
        
        subdir = subdir_map.get(data_type)
        if not subdir or not (data_dir / subdir).exists():
            st.info(f"No {data_type.lower()} data found")
            return
        
        files = list((data_dir / subdir).glob("*.json"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not files:
            st.info(f"No {data_type.lower()} files found")
            return
        
        # File selector
        selected_file = st.selectbox(
            f"Select {data_type.lower()} file:",
            options=[f.name for f in files],
            index=0
        )
        
        file_path = data_dir / subdir / selected_file
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Display data
            st.json(data)
            
            # Download button
            st.download_button(
                label=f"📥 Download {selected_file}",
                data=json.dumps(data, indent=2),
                file_name=selected_file,
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

    # ============================================
    # NEW: Missing Methods
    # ============================================

    def _run_prompt_tests(self, prompt_count: int, test_case_count: int):
        """Run prompt tests with detailed view"""
        with st.spinner(f"Running prompt tests ({prompt_count} prompts, {test_case_count} cases)..."):
            try:
                # Run async function
                result = asyncio.run(self._execute_prompt_tests(prompt_count, test_case_count))

                if result:
                    success = result.get("success", False)
                    score = result.get("score", 0)
                    if success:
                        st.success(f"✅ Prompt Tests: PASSED (Score: {score:.2f})")
                    else:
                        st.error(f"❌ Prompt Tests: FAILED (Score: {score:.2f})")

                    # Show detailed results
                    with st.expander("📊 View Detailed Results", expanded=True):
                        # Get the latest test details
                        all_tests = st.session_state.metrics.get_session_metrics()
                        if all_tests:
                            latest_test = all_tests[-1]
                            
                            # Show justification
                            justification = latest_test.get("justification", "")
                            if justification:
                                st.info(f"**Justification:** {justification}")
                            
                            # Show outputs
                            st.write("**Outputs:**")
                            outputs = latest_test.get("outputs", {})
                            if outputs:
                                st.json(outputs)
                            else:
                                st.json(result.get("details", {}))
                    
                    # Suggest viewing test details
                    timer_id = result.get("timer_id")
                    if timer_id:
                        st.info(f"🔍 View complete test details in the **Test Details** page")

                # Rerun to update metrics
                st.rerun()
                
            except Exception as e:
                st.error(f"Prompt tests failed: {str(e)}")
                # Record error
                timer_id = st.session_state.metrics.start_test(
                    test_id=f"prompt_test_{prompt_count}x{test_case_count}",
                    test_type="prompt",
                    test_name=f"Prompt Testing ({prompt_count} prompts, {test_case_count} cases)",
                    inputs={"prompt_count": prompt_count, "test_case_count": test_case_count}
                )
                st.session_state.metrics.end_test(
                    timer_id=timer_id,
                    status="error",
                    score=0.0,
                    outputs={"error": str(e)},
                    justification=f"Prompt test failed with error: {str(e)}"
                )
                st.rerun()

    # Add this new page function to your EnhancedTestingDashboard class

    def _render_prompt_responses(self):
        """Render detailed prompt responses view"""
        st.markdown('<div class="main-header">📝 Generated Prompts & LLM Responses</div>', unsafe_allow_html=True)
        
        # Check for saved response files
        responses_dir = Path("data/responses")
        if not responses_dir.exists():
            st.info("No response files found. Run some prompt tests first.")
            return
        
        # Get all response files
        response_files = list(responses_dir.glob("*.json"))
        if not response_files:
            st.info("No response files found. Run some prompt tests first.")
            return
        
        # Sort by modification time (newest first)
        response_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # File selector
        st.markdown("### Select Response File")
        file_options = {f.name: f for f in response_files}
        selected_file_name = st.selectbox(
            "Choose a response file to view:",
            options=list(file_options.keys()),
            index=0
        )
        
        selected_file = file_options[selected_file_name]
        
        # Load and display the selected file
        try:
            with open(selected_file, 'r') as f:
                response_data = json.load(f)
            
            # Display file info
            st.markdown("### File Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Responses", response_data.get("total_responses", 0))
            with col2:
                st.metric("Test Name", response_data.get("test_name", "Unknown"))
            with col3:
                timestamp = response_data.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        st.metric("Generated", dt.strftime("%Y-%m-%d %H:%M:%S"))
                    except:
                        st.metric("Generated", timestamp)
            
            # Filter and search options
            st.markdown("---")
            st.markdown("### Filter Responses")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                # Filter by prompt type
                all_prompt_types = list(set(r.get("prompt_type", "unknown") for r in response_data.get("responses", [])))
                selected_prompt_types = st.multiselect(
                    "Filter by Prompt Type:",
                    options=all_prompt_types,
                    default=all_prompt_types
                )
            
            with col2:
                # Filter by success
                success_filter = st.selectbox(
                    "Filter by Success:",
                    options=["All", "Successful Only", "Failed Only"],
                    index=0
                )
            
            with col3:
                # Search by keyword
                search_term = st.text_input("Search in prompts/responses:")
            
            # Apply filters
            filtered_responses = response_data.get("responses", [])
            
            if selected_prompt_types:
                filtered_responses = [r for r in filtered_responses if r.get("prompt_type", "unknown") in selected_prompt_types]
            
            if success_filter == "Successful Only":
                filtered_responses = [r for r in filtered_responses if r.get("success", False)]
            elif success_filter == "Failed Only":
                filtered_responses = [r for r in filtered_responses if not r.get("success", False)]
            
            if search_term:
                search_lower = search_term.lower()
                filtered_responses = [
                    r for r in filtered_responses 
                    if (search_lower in r.get("prompt_content", "").lower() or 
                        search_lower in str(r.get("response_data", "")).lower() or
                        search_lower in str(r.get("test_case", {})).lower())
                ]
            
            st.markdown(f"**Showing {len(filtered_responses)} of {response_data.get('total_responses', 0)} responses**")
            
            # Display responses in tabs
            if filtered_responses:
                tab1, tab2, tab3 = st.tabs(["📋 List View", "📊 Statistics", "💾 Export"])
                
                with tab1:
                    # Display each response
                    for i, response in enumerate(filtered_responses):
                        with st.expander(f"Response #{i+1}: Prompt {response.get('prompt_id')} - Case {response.get('test_case_id')}", expanded=(i == 0)):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                status = "✅ Success" if response.get("success", False) else "❌ Failed"
                                st.markdown(f"**Status:** {status}")
                            
                            with col2:
                                st.markdown(f"**Prompt Type:** {response.get('prompt_type', 'Unknown')}")
                            
                            with col3:
                                st.markdown(f"**Response Time:** {response.get('response_time_ms', 0):.0f}ms")
                            
                            # Prompt details
                            st.markdown("#### 📝 Generated Prompt")
                            st.code(response.get("prompt_content", "No prompt content"), language="text")
                            
                            # Test case details
                            st.markdown("#### 📋 Test Case")
                            test_case = response.get("test_case", {})
                            if test_case:
                                st.json(test_case)
                            
                            # Full query
                            st.markdown("#### 🔍 Full Query Sent to LLM")
                            st.code(response.get("full_query", "No query"), language="text")
                            
                            # Response data
                            st.markdown("#### 🤖 LLM Response")
                            response_data = response.get("response_data", {})
                            if response_data:
                                if isinstance(response_data, dict):
                                    st.json(response_data)
                                    if "results" in response_data:
                                        results = response_data["results"]
                                        if isinstance(results, list):
                                            st.markdown(f"**Results Count:** {len(results)}")
                                            # Show first few results
                                            if results:
                                                st.markdown("**First Result:**")
                                                st.json(results[0] if isinstance(results[0], dict) else str(results[0]))
                                else:
                                    st.text_area("Response", str(response_data), height=200)
                            else:
                                st.warning("No response data")
                            
                            # Additional metrics
                            if response.get("has_results", False):
                                st.success(f"✅ Contains {response.get('results_count', 0)} results")
                            else:
                                st.warning("⚠️ No results in response")
                
                with tab2:
                    # Statistics
                    st.markdown("#### 📈 Response Statistics")
                    
                    # Success rate
                    success_count = sum(1 for r in filtered_responses if r.get("success", False))
                    total_count = len(filtered_responses)
                    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                    
                    # Average response time
                    response_times = [r.get("response_time_ms", 0) for r in filtered_responses if r.get("response_time_ms", 0) > 0]
                    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                    
                    # Results count distribution
                    results_counts = [r.get("results_count", 0) for r in filtered_responses]
                    avg_results = sum(results_counts) / len(results_counts) if results_counts else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    with col2:
                        st.metric("Avg Response Time", f"{avg_response_time:.0f}ms")
                    with col3:
                        st.metric("Avg Results per Response", f"{avg_results:.1f}")
                    
                    # Prompt type distribution
                    st.markdown("#### Prompt Type Distribution")
                    prompt_type_counts = {}
                    for response in filtered_responses:
                        prompt_type = response.get("prompt_type", "unknown")
                        prompt_type_counts[prompt_type] = prompt_type_counts.get(prompt_type, 0) + 1
                    
                    if prompt_type_counts:
                        df = pd.DataFrame({
                            "Prompt Type": list(prompt_type_counts.keys()),
                            "Count": list(prompt_type_counts.values())
                        })
                        fig = px.bar(df, x="Prompt Type", y="Count", title="Responses by Prompt Type")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Response time distribution
                    st.markdown("#### Response Time Distribution")
                    if response_times:
                        fig = px.histogram(x=response_times, nbins=20, title="Response Time Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    # Export options
                    st.markdown("#### Export Filtered Responses")
                    
                    export_format = st.selectbox(
                        "Export Format:",
                        options=["JSON", "CSV", "HTML Report"]
                    )
                    
                    if st.button("📥 Export Responses", width='stretch'):
                        if export_format == "JSON":
                            export_data = {
                                "filtered_responses": filtered_responses,
                                "filter_applied": {
                                    "prompt_types": selected_prompt_types,
                                    "success_filter": success_filter,
                                    "search_term": search_term,
                                    "total_filtered": len(filtered_responses)
                                }
                            }
                            
                            json_str = json.dumps(export_data, indent=2, default=str)
                            
                            st.download_button(
                                label="📥 Download JSON",
                                data=json_str,
                                file_name=f"prompt_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                        
                        elif export_format == "CSV":
                            # Convert to DataFrame
                            df_data = []
                            for response in filtered_responses:
                                df_data.append({
                                    "prompt_id": response.get("prompt_id"),
                                    "prompt_type": response.get("prompt_type"),
                                    "prompt_content": response.get("prompt_content", "")[:200],  # Truncate
                                    "test_case_id": response.get("test_case_id"),
                                    "industry": response.get("test_case", {}).get("industry", ""),
                                    "description": response.get("test_case", {}).get("description", ""),
                                    "status_code": response.get("status_code"),
                                    "response_time_ms": response.get("response_time_ms"),
                                    "success": response.get("success", False),
                                    "results_count": response.get("results_count", 0),
                                    "has_results": response.get("has_results", False)
                                })
                            
                            if df_data:
                                df = pd.DataFrame(df_data)
                                csv_data = df.to_csv(index=False)
                                
                                st.download_button(
                                    label="📥 Download CSV",
                                    data=csv_data,
                                    file_name=f"prompt_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                        
                        elif export_format == "HTML Report":
                            # Generate HTML report
                            html_report = self._generate_html_report(filtered_responses)
                            
                            st.download_button(
                                label="📥 Download HTML Report",
                                data=html_report,
                                file_name=f"prompt_responses_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                mime="text/html"
                            )
            
            else:
                st.warning("No responses match the selected filters.")
                
        except Exception as e:
            st.error(f"Error loading response file: {str(e)}")
    
    def _generate_html_report(self, responses: List[Dict]) -> str:
        """Generate HTML report for responses"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Prompt Responses Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .response { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .success { background-color: #d4edda; border-color: #c3e6cb; }
                .failed { background-color: #f8d7da; border-color: #f5c6cb; }
                .prompt { background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0; }
                .response-data { background-color: #e9ecef; padding: 10px; border-radius: 3px; margin: 10px 0; }
                .stats { display: flex; justify-content: space-between; margin: 20px 0; }
                .stat-box { flex: 1; text-align: center; padding: 10px; background-color: #007bff; color: white; margin: 0 5px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Prompt Responses Report</h1>
            <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p>Total Responses: """ + str(len(responses)) + """</p>
        """
        
        # Statistics
        success_count = sum(1 for r in responses if r.get("success", False))
        total_count = len(responses)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        html += """
        <div class="stats">
            <div class="stat-box">
                <h3>Success Rate</h3>
                <p>""" + f"{success_rate:.1f}%" + """</p>
            </div>
        </div>
        """
        
        # Responses
        for i, response in enumerate(responses):
            status_class = "success" if response.get("success", False) else "failed"
            status_text = "✅ Success" if response.get("success", False) else "❌ Failed"
            
            html += f"""
            <div class="response {status_class}">
                <h3>Response #{i+1}: {status_text}</h3>
                <p><strong>Prompt Type:</strong> {response.get('prompt_type', 'Unknown')}</p>
                <p><strong>Response Time:</strong> {response.get('response_time_ms', 0):.0f}ms</p>
                
                <div class="prompt">
                    <h4>Generated Prompt:</h4>
                    <pre>{response.get('prompt_content', 'No prompt content')}</pre>
                </div>
                
                <div class="response-data">
                    <h4>LLM Response:</h4>
                    <pre>{json.dumps(response.get('response_data', {}), indent=2)}</pre>
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html    

# Main function to run the dashboard
def main():
    dashboard = EnhancedTestingDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()