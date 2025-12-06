# src/test_runner.py
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

class TestRunner:
    """Runs tests and collects metrics"""
    
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
    
    async def run_login_test(self, username: str, password: str, test_name: str) -> Dict:
        """Run login test"""
        try:
            # Start timer
            timer_id = self.metrics.start_test(
                test_id=f"login_{username}",
                test_type="login",  # Explicitly set test_type
                test_name=test_name
            )
            
            # Simulate API call
            await asyncio.sleep(1)  # Simulate network delay
            
            # Determine if test passes based on username/password
            is_valid = username in ["sales1", "expert1", "admin"] and password == "demo123"
            
            # Record result
            self.metrics.end_test(
                timer_id=timer_id,
                status="passed" if is_valid else "failed",
                score=1.0 if is_valid else 0.0,
                details={
                    "username": username,
                    "is_valid": is_valid,
                    "test_type": "login"
                }
            )
            
            return {
                "success": is_valid,
                "score": 1.0 if is_valid else 0.0,
                "details": {
                    "username": username,
                    "is_valid": is_valid,
                    "message": "Valid login" if is_valid else "Invalid credentials"
                }
            }
        except Exception as e:
            # Record error
            self.metrics.record_test(
                test_id=f"login_{username}",
                test_type="login",  # Explicitly set test_type
                test_name=test_name,
                status="error",
                score=0.0,
                duration_ms=1000,
                details={"error": str(e)}
            )
            raise
    
    async def run_agent_test(self, function: str) -> Dict:
        """Run agent function test"""
        try:
            # Start timer
            timer_id = self.metrics.start_test(
                test_id=f"agent_{function}",
                test_type="agent",  # Explicitly set test_type
                test_name=f"Agent {function}"
            )
            
            # Simulate API call
            await asyncio.sleep(2)  # Simulate processing time
            
            # Simulate test result
            score = 0.85  # Simulated score
            
            # Record result
            self.metrics.end_test(
                timer_id=timer_id,
                status="passed",
                score=score,
                details={
                    "function": function,
                    "test_type": "agent"
                }
            )
            
            return {
                "success": True,
                "score": score,
                "details": {
                    "function": function,
                    "message": f"Agent {function} test completed"
                }
            }
        except Exception as e:
            # Record error
            self.metrics.record_test(
                test_id=f"agent_{function}",
                test_type="agent",  # Explicitly set test_type
                test_name=f"Agent {function}",
                status="error",
                score=0.0,
                duration_ms=2000,
                details={"error": str(e)}
            )
            raise
    
    async def run_prompt_test(self, prompt_count: int, test_case_count: int) -> Dict:
        """Run prompt test"""
        try:
            timer_id = self.metrics.start_test(
                test_id=f"prompt_{prompt_count}_{test_case_count}",
                test_type="prompt",  # Explicitly set test_type
                test_name=f"Prompt Test ({prompt_count} prompts)"
            )
            
            await asyncio.sleep(3)
            
            score = 0.75
            
            self.metrics.end_test(
                timer_id=timer_id,
                status="passed",
                score=score,
                details={
                    "prompt_count": prompt_count,
                    "test_case_count": test_case_count
                }
            )
            
            return {
                "success": True,
                "score": score,
                "details": {
                    "prompt_count": prompt_count,
                    "test_case_count": test_case_count
                }
            }
        except Exception as e:
            self.metrics.record_test(
                test_id=f"prompt_{prompt_count}_{test_case_count}",
                test_type="prompt",
                test_name=f"Prompt Test ({prompt_count} prompts)",
                status="error",
                score=0.0,
                duration_ms=3000,
                details={"error": str(e)}
            )
            raise
    
    async def run_kb_test(self, category: str) -> Dict:
        """Run knowledge base test"""
        try:
            timer_id = self.metrics.start_test(
                test_id=f"kb_{category}",
                test_type="kb",  # Explicitly set test_type
                test_name=f"KB {category}"
            )
            
            await asyncio.sleep(1.5)
            
            score = 0.9
            
            self.metrics.end_test(
                timer_id=timer_id,
                status="passed",
                score=score,
                details={"category": category}
            )
            
            return {
                "success": True,
                "score": score,
                "details": {"category": category}
            }
        except Exception as e:
            self.metrics.record_test(
                test_id=f"kb_{category}",
                test_type="kb",
                test_name=f"KB {category}",
                status="error",
                score=0.0,
                duration_ms=1500,
                details={"error": str(e)}
            )
            raise
    
    async def run_e2e_test(self, name: str, scenario: str) -> Dict:
        """Run end-to-end test"""
        try:
            timer_id = self.metrics.start_test(
                test_id=f"e2e_{name.replace(' ', '_')}",
                test_type="e2e",  # Explicitly set test_type
                test_name=f"E2E {name}"
            )
            
            await asyncio.sleep(4)
            
            score = 0.8
            
            self.metrics.end_test(
                timer_id=timer_id,
                status="passed",
                score=score,
                details={
                    "name": name,
                    "scenario": scenario
                }
            )
            
            return {
                "success": True,
                "score": score,
                "details": {
                    "name": name,
                    "scenario": scenario
                }
            }
        except Exception as e:
            self.metrics.record_test(
                test_id=f"e2e_{name.replace(' ', '_')}",
                test_type="e2e",
                test_name=f"E2E {name}",
                status="error",
                score=0.0,
                duration_ms=4000,
                details={"error": str(e)}
            )
            raise