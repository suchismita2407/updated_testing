import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.tester import SalesEVATester
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sales EVA Testing Framework API",
    description="API for comprehensive testing of Sales Virtual Advisor systems",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
test_runners = {}  # Store active test runners
test_results = {}  # Store test results

class TestManager:
    """Manage test execution and results"""
    
    @staticmethod
    def generate_test_id() -> str:
        """Generate unique test ID"""
        return f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(datetime.now())}"
    
    @staticmethod
    async def run_test_background(
        test_id: str,
        api_url: str,
        test_types: List[str]
    ):
        """Run test in background and store results"""
        try:
            logger.info(f"Starting background test {test_id} for {api_url}")
            
            # Create tester
            tester = SalesEVATester(api_url=api_url)
            
            # Run tests
            results = await tester.run_all_tests(
                test_types=test_types,
                save_results=True
            )
            
            # Store results
            test_results[test_id] = {
                "status": "completed",
                "results": results,
                "completed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Background test {test_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Background test {test_id} failed: {e}")
            test_results[test_id] = {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
        
        finally:
            # Cleanup
            if test_id in test_runners:
                del test_runners[test_id]

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sales EVA Testing Framework API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "run_test": "/test/run",
            "test_status": "/test/status/{test_id}",
            "test_results": "/test/results/{test_id}",
            "quick_test": "/test/quick",
            "test_history": "/test/history",
            "metrics": "/metrics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "sales_eva_testing_framework"
    }

@app.post("/test/run")
async def run_comprehensive_test(
    background_tasks: BackgroundTasks,
    api_url: str = Query(..., description="Sales EVA API URL to test"),
    test_types: str = Query("prompt,agent,kb,e2e", description="Comma-separated test types to run"),
    run_in_background: bool = Query(True, description="Run test in background")
):
    """
    Run comprehensive testing suite
    
    Test types: prompt, agent, kb, e2e
    """
    # Parse test types
    types_list = [t.strip() for t in test_types.split(",") if t.strip()]
    valid_types = ["prompt", "agent", "kb", "e2e"]
    
    for test_type in types_list:
        if test_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid test type: {test_type}. Valid types: {valid_types}"
            )
    
    if not types_list:
        types_list = valid_types
    
    # Generate test ID
    test_id = TestManager.generate_test_id()
    
    if run_in_background:
        # Store test runner
        test_runners[test_id] = {
            "status": "running",
            "api_url": api_url,
            "test_types": types_list,
            "started_at": datetime.now().isoformat()
        }
        
        # Initialize results entry
        test_results[test_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat()
        }
        
        # Run in background
        background_tasks.add_task(
            TestManager.run_test_background,
            test_id,
            api_url,
            types_list
        )
        
        return {
            "test_id": test_id,
            "status": "started",
            "message": f"Test running in background. Check status at /test/status/{test_id}",
            "test_types": types_list,
            "api_url": api_url,
            "started_at": datetime.now().isoformat()
        }
    
    else:
        # Run synchronously
        try:
            tester = SalesEVATester(api_url=api_url)
            results = await tester.run_all_tests(
                test_types=types_list,
                save_results=True
            )
            
            # Store results
            test_results[test_id] = {
                "status": "completed",
                "results": results,
                "completed_at": datetime.now().isoformat()
            }
            
            return {
                "test_id": test_id,
                "status": "completed",
                "results_summary": {
                    "overall_score": results.get("summary", {}).get("overall_score", 0),
                    "health_assessment": results.get("summary", {}).get("health_assessment", {})
                },
                "test_types": types_list,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Test execution failed: {str(e)}"
            )

@app.get("/test/status/{test_id}")
async def get_test_status(test_id: str):
    """Get test execution status"""
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test ID not found")
    
    result = test_results[test_id]
    
    if result["status"] == "running":
        # Check if still in runners (active)
        if test_id in test_runners:
            return {
                "test_id": test_id,
                "status": "running",
                "started_at": result.get("started_at"),
                "message": "Test is currently running"
            }
        else:
            # Runner finished but results not yet stored
            result["status"] = "processing"
            return {
                "test_id": test_id,
                "status": "processing",
                "message": "Test completed, processing results"
            }
    
    return {
        "test_id": test_id,
        "status": result["status"],
        "completed_at": result.get("completed_at"),
        "failed_at": result.get("failed_at"),
        "error": result.get("error") if result["status"] == "failed" else None
    }

@app.get("/test/results/{test_id}")
async def get_test_results(
    test_id: str,
    summary_only: bool = Query(False, description="Return only summary")
):
    """Get test results"""
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test ID not found")
    
    result = test_results[test_id]
    
    if result["status"] == "running":
        raise HTTPException(
            status_code=400, 
            detail="Test is still running. Check /test/status/{test_id}"
        )
    
    if result["status"] == "failed":
        return {
            "test_id": test_id,
            "status": "failed",
            "error": result.get("error"),
            "failed_at": result.get("failed_at")
        }
    
    if summary_only:
        full_results = result.get("results", {})
        return {
            "test_id": test_id,
            "status": "completed",
            "summary": full_results.get("summary", {}),
            "recommendations": full_results.get("recommendations", []),
            "completed_at": result.get("completed_at")
        }
    
    return result

@app.post("/test/quick")
async def run_quick_test(
    api_url: str = Query(..., description="Sales EVA API URL to test")
):
    """Run quick health and functionality test"""
    try:
        tester = SalesEVATester(api_url=api_url)
        results = await tester.run_quick_test()
        
        return {
            "api_url": api_url,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quick test failed: {str(e)}"
        )

@app.get("/test/history")
async def get_test_history(
    limit: int = Query(10, ge=1, le=100, description="Number of recent tests to return")
):
    """Get test execution history"""
    # Get recent test IDs
    recent_tests = list(test_results.keys())[-limit:]
    
    history = []
    for test_id in recent_tests:
        result = test_results[test_id]
        
        entry = {
            "test_id": test_id,
            "status": result["status"],
            "timestamp": result.get("started_at") or result.get("completed_at") or result.get("failed_at")
        }
        
        if result["status"] == "completed":
            entry["overall_score"] = result.get("results", {}).get("summary", {}).get("overall_score", 0)
        
        history.append(entry)
    
    return {
        "total_tests": len(test_results),
        "recent_tests": history
    }

@app.get("/metrics")
async def get_testing_metrics():
    """Get aggregated testing metrics"""
    completed_tests = [
        r for r in test_results.values() 
        if r["status"] == "completed" and "results" in r
    ]
    
    if not completed_tests:
        return {
            "message": "No completed tests found",
            "total_tests": len(test_results)
        }
    
    # Calculate metrics
    scores = []
    for test in completed_tests[-10:]:  # Last 10 tests
        score = test.get("results", {}).get("summary", {}).get("overall_score", 0)
        if score > 0:
            scores.append(score)
    
    if scores:
        avg_score = sum(scores) / len(scores)
        trend = "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
    else:
        avg_score = 0
        trend = "unknown"
    
    # Count by status
    status_counts = {
        "completed": 0,
        "running": 0,
        "failed": 0
    }
    
    for result in test_results.values():
        status = result["status"]
        if status in status_counts:
            status_counts[status] += 1
    
    return {
        "total_tests": len(test_results),
        "status_counts": status_counts,
        "performance_metrics": {
            "average_score": avg_score,
            "trend": trend,
            "recent_scores": scores[-5:] if scores else []
        },
        "recent_tests": list(test_results.keys())[-5:]
    }

@app.get("/test/types")
async def get_test_types():
    """Get available test types"""
    return {
        "test_types": [
            {
                "name": "prompt",
                "description": "Test and optimize system prompts",
                "metrics": ["prompt_score", "coverage", "latency"]
            },
            {
                "name": "agent",
                "description": "Test agent capabilities (matching, gap analysis, etc.)",
                "metrics": ["function_scores", "success_rate", "accuracy"]
            },
            {
                "name": "kb",
                "description": "Validate knowledge base coverage and quality",
                "metrics": ["coverage_score", "freshness_score", "consistency"]
            },
            {
                "name": "e2e",
                "description": "End-to-end system testing with realistic scenarios",
                "metrics": ["overall_score", "business_impact", "success_rate"]
            }
        ],
        "default_test_types": ["prompt", "agent", "kb", "e2e"]
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Sales EVA Testing Framework API starting up...")
    logger.info(f"API URL: {settings.SALES_EVA_API_URL}")
    logger.info(f"Results directory: {settings.RESULTS_DIR}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Sales EVA Testing Framework API shutting down...")
    # Cleanup any running tests
    for test_id in list(test_runners.keys()):
        if test_id in test_runners:
            del test_runners[test_id]

# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        reload=True,
        log_level="info"
    )