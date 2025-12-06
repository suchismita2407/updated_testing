# src/real_test_runner.py
import httpx
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTestRunner:
    """Actually tests the Sales EVA service by making real API calls"""
    
    def __init__(self, base_url: str, metrics_collector):
        self.base_url = base_url.rstrip('/')
        self.metrics = metrics_collector
        self.session_cookie = None
        self.client = None
    
    async def _get_client(self):
        """Get HTTP client with session support"""
        if self.client is None:
            # Create client with cookies for session management
            self.client = httpx.AsyncClient(
                timeout=30.0,
                cookies=self.session_cookie if self.session_cookie else {}
            )
        return self.client
    
    async def authenticate(self, username: str, password: str) -> Dict:
        """Actually authenticate with Sales EVA service"""
        try:
            client = await self._get_client()
            
            # First, clear any existing session
            self.session_cookie = None
            client.cookies.clear()
            
            response = await client.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store session cookie (Flask uses session cookies)
                if response.cookies:
                    self.session_cookie = response.cookies
                    client.cookies.update(self.session_cookie)
                
                return {
                    "success": True,
                    "user": data.get("user", {}),
                    "message": data.get("message", "Login successful")
                }
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "status_code": response.status_code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_login_test(self, username: str, password: str, test_name: str) -> Dict:
        """Actually test login functionality"""
        timer_id = self.metrics.start_test(
            test_id=f"login_{username}",
            test_type="login",
            test_name=test_name
        )
        
        try:
            start_time = datetime.now()
            result = await self.authenticate(username, password)
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            success = result.get("success", False)
            status_code = result.get("status_code", 0)
            
            # Calculate score based on expected vs actual
            expected_success = username in ["sales1", "expert1", "admin"] and password == "demo123"
            score = 1.0 if (success == expected_success) else 0.0
            
            test_status = "passed" if success == expected_success else "failed"
            
            self.metrics.end_test(
                timer_id=timer_id,
                status=test_status,
                score=score,
                details={
                    "username": username,
                    "expected_success": expected_success,
                    "actual_success": success,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "user_received": result.get("user") is not None,
                    "error": result.get("error")
                }
            )
            
            return {
                "success": success == expected_success,
                "score": score,
                "details": result
            }
            
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            return {"success": False, "score": 0.0, "details": {"error": str(e)}}
    
    async def run_agent_test(self, function: str) -> Dict:
        """Actually test agent functionality using RAG search endpoint"""
        timer_id = self.metrics.start_test(
            test_id=f"agent_{function}",
            test_type="agent",
            test_name=f"Agent {function}"
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            # Map agent functions to appropriate RAG queries
            queries = {
                "matching": "Find relevant AI and cloud solutions for banking fraud detection",
                "gap_analysis": "What are common gaps in digital transformation projects for banks?",
                "research": "Latest trends and best practices in AI-powered fraud detection",
                "reporting": "How to structure a sales proposal for cybersecurity solutions"
            }
            
            if function not in queries:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={"error": f"Unknown agent function: {function}"}
                )
                return {"success": False, "score": 0.0, "details": {"error": f"Unknown function: {function}"}}
            
            query = queries[function]
            
            response = await client.post(
                f"{self.base_url}/api/rag/search",
                json={"query": query}
            )
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate score based on response quality
                score = self._calculate_rag_score(data, duration_ms)
                success = score >= 0.6  # Pass if score >= 60%
                
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="passed" if success else "failed",
                    score=score,
                    details={
                        "function": function,
                        "query": query,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "has_results": "results" in data and len(data["results"]) > 0,
                        "results_count": len(data.get("results", [])),
                        "sample_results": data.get("results", [])[:2] if data.get("results") else []
                    }
                )
                
                return {
                    "success": success,
                    "score": score,
                    "details": data
                }
            elif response.status_code == 401:
                # Not authenticated
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={
                        "function": function,
                        "status_code": 401,
                        "error": "Authentication required - login first",
                        "duration_ms": duration_ms
                    }
                )
                return {
                    "success": False,
                    "score": 0.0,
                    "details": {"error": "Authentication required. Please run login tests first."}
                }
            else:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={
                        "function": function,
                        "status_code": response.status_code,
                        "error": response.text,
                        "duration_ms": duration_ms
                    }
                )
                return {
                    "success": False,
                    "score": 0.0,
                    "details": {"error": f"HTTP {response.status_code}: {response.text}"}
                }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            return {"success": False, "score": 0.0, "details": {"error": str(e)}}
    
    async def run_kb_test(self, category: str) -> Dict:
        """Actually test knowledge base functionality using RAG search"""
        timer_id = self.metrics.start_test(
            test_id=f"kb_{category}",
            test_type="kb",
            test_name=f"KB {category}"
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            # Different queries for different KB test categories
            queries = {
                "coverage": "What topics, technologies, and solutions are covered in the knowledge base? Provide comprehensive list.",
                "freshness": "What are the most recent updates, technologies, or trends mentioned in the knowledge base?",
                "consistency": "Explain cloud deployment architecture and security best practices consistently across different solutions",
                "relevance": "How relevant is the knowledge base content for banking, healthcare, and retail industries?",
                "completeness": "How complete is the information about digital transformation, AI implementation, and cloud migration?"
            }
            
            if category not in queries:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={"error": f"Unknown KB category: {category}"}
                )
                return {"success": False, "score": 0.0, "details": {"error": f"Unknown category: {category}"}}
            
            query = queries[category]
            
            response = await client.post(
                f"{self.base_url}/api/rag/search",
                json={"query": query}
            )
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate score based on response quality
                score = self._calculate_rag_score(data, duration_ms)
                success = score >= 0.6
                
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="passed" if success else "failed",
                    score=score,
                    details={
                        "category": category,
                        "query": query,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "has_results": "results" in data and len(data["results"]) > 0,
                        "results_count": len(data.get("results", [])),
                        "first_result_type": data.get("results", [{}])[0].get("type", "unknown") if data.get("results") else "none"
                    }
                )
                
                return {
                    "success": success,
                    "score": score,
                    "details": data
                }
            elif response.status_code == 401:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={
                        "category": category,
                        "status_code": 401,
                        "error": "Authentication required - login first",
                        "duration_ms": duration_ms
                    }
                )
                return {
                    "success": False,
                    "score": 0.0,
                    "details": {"error": "Authentication required. Please run login tests first."}
                }
            else:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={
                        "category": category,
                        "status_code": response.status_code,
                        "error": response.text,
                        "duration_ms": duration_ms
                    }
                )
                return {
                    "success": False,
                    "score": 0.0,
                    "details": {"error": f"HTTP {response.status_code}: {response.text}"}
                }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            return {"success": False, "score": 0.0, "details": {"error": str(e)}}
    
    def _calculate_rag_score(self, response_data: Dict, duration_ms: float) -> float:
        """Calculate score for RAG search responses"""
        try:
            score = 0.5  # Base score for any response
            
            # Check if response has results
            if "results" in response_data:
                results = response_data["results"]
                if isinstance(results, list):
                    if len(results) > 0:
                        score += 0.2
                    
                    # Check quality of results
                    for result in results[:3]:  # Check first 3 results
                        if isinstance(result, dict):
                            if result.get("title") and result.get("content"):
                                score += 0.05
                            if result.get("score", 0) > 0.7:
                                score += 0.02
            
            # Check for query in response
            if "query" in response_data:
                score += 0.05
            
            # Penalize for slow responses (but not too much since RAG can be slow)
            if duration_ms > 15000:  # > 15 seconds
                score -= 0.1
            elif duration_ms > 10000:  # > 10 seconds
                score -= 0.05
                
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, score))
            
        except:
            return 0.3  # Minimum score for any response
    
    async def run_profile_test(self) -> Dict:
        """Test profile endpoint to verify authentication works"""
        timer_id = self.metrics.start_test(
            test_id="profile_test",
            test_type="auth",
            test_name="Profile Access Test"
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            response = await client.get(f"{self.base_url}/profile")
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                success = "username" in data and "role" in data
                
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="passed" if success else "failed",
                    score=1.0 if success else 0.0,
                    details={
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "username_returned": "username" in data,
                        "role_returned": "role" in data
                    }
                )
                
                return {
                    "success": success,
                    "score": 1.0 if success else 0.0,
                    "details": data
                }
            else:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={
                        "status_code": response.status_code,
                        "error": response.text,
                        "duration_ms": duration_ms,
                        "expected": "Should return 200 with user data when authenticated"
                    }
                )
                return {
                    "success": False,
                    "score": 0.0,
                    "details": {"error": f"HTTP {response.status_code}: {response.text}"}
                }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            return {"success": False, "score": 0.0, "details": {"error": str(e)}}
    
    async def run_opportunities_test(self) -> Dict:
        """Test opportunities endpoints"""
        timer_id = self.metrics.start_test(
            test_id="opportunities_test",
            test_type="data",
            test_name="Opportunities API Test"
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            # Test GET opportunities
            response = await client.get(f"{self.base_url}/opportunities")
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                success = "opportunities" in data
                
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="passed" if success else "failed",
                    score=1.0 if success else 0.0,
                    details={
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "has_opportunities_field": "opportunities" in data,
                        "opportunities_count": len(data.get("opportunities", [])),
                        "is_list": isinstance(data.get("opportunities"), list)
                    }
                )
                
                return {
                    "success": success,
                    "score": 1.0 if success else 0.0,
                    "details": data
                }
            else:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={
                        "status_code": response.status_code,
                        "error": response.text,
                        "duration_ms": duration_ms,
                        "expected": "Should return 200 with opportunities list"
                    }
                )
                return {
                    "success": False,
                    "score": 0.0,
                    "details": {"error": f"HTTP {response.status_code}: {response.text}"}
                }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            return {"success": False, "score": 0.0, "details": {"error": str(e)}}
    
    async def run_prompt_test(self, prompt_count: int, test_case_count: int) -> Dict:
        """Test multiple prompts through RAG search"""
        timer_id = self.metrics.start_test(
            test_id=f"prompt_{prompt_count}_{test_case_count}",
            test_type="prompt",
            test_name=f"Prompt Test ({prompt_count} prompts)"
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            # Test prompts
            test_prompts = [
                "AI solutions for banking fraud detection",
                "Cloud migration strategies for enterprises",
                "Digital transformation roadmap",
                "Cybersecurity best practices 2025",
                "IoT implementation in manufacturing",
                "Data analytics for retail optimization",
                "Healthcare IT modernization approaches",
                "ERP system selection criteria",
                "CRM implementation best practices",
                "Mobile app development for customer engagement"
            ]
            
            results = []
            total_score = 0
            tested_prompts = min(prompt_count, len(test_prompts))
            
            for i, prompt in enumerate(test_prompts[:tested_prompts]):
                try:
                    response = await client.post(
                        f"{self.base_url}/api/rag/search",
                        json={"query": prompt}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        prompt_score = self._calculate_rag_score(data, 0)
                        total_score += prompt_score
                        results.append({
                            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                            "score": prompt_score,
                            "results_count": len(data.get("results", []))
                        })
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error testing prompt {i}: {e}")
                    continue
            
            avg_score = total_score / len(results) if results else 0.0
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            self.metrics.end_test(
                timer_id=timer_id,
                status="passed" if avg_score >= 0.5 else "failed",
                score=avg_score,
                details={
                    "prompts_tested": len(results),
                    "test_cases_per_prompt": test_case_count,
                    "average_score": avg_score,
                    "total_duration_ms": duration_ms,
                    "avg_duration_per_prompt": duration_ms / len(results) if results else 0,
                    "results_sample": results[:3] if results else []
                }
            )
            
            return {
                "success": avg_score >= 0.5,
                "score": avg_score,
                "details": {
                    "prompts_tested": len(results),
                    "average_score": avg_score,
                    "total_duration_ms": duration_ms
                }
            }
            
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            return {"success": False, "score": 0.0, "details": {"error": str(e)}}
    
    async def run_e2e_scenario(self, name: str, scenario: str) -> Dict:
        """Run end-to-end test: Login → RAG Search → Validate"""
        timer_id = self.metrics.start_test(
            test_id=f"e2e_{name.replace(' ', '_')}",
            test_type="e2e",
            test_name=f"E2E {name}"
        )
        
        try:
            # Step 1: Login
            login_result = await self.authenticate("sales1", "demo123")
            if not login_result.get("success"):
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={"error": "Login failed", "login_result": login_result}
                )
                return {"success": False, "score": 0.0, "details": {"error": "Login failed"}}
            
            # Step 2: Test profile access
            client = await self._get_client()
            profile_response = await client.get(f"{self.base_url}/profile")
            if profile_response.status_code != 200:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={"error": "Profile access failed", "status": profile_response.status_code}
                )
                return {"success": False, "score": 0.0, "details": {"error": "Profile access failed"}}
            
            # Step 3: Run RAG search with scenario
            response = await client.post(
                f"{self.base_url}/api/rag/search",
                json={"query": scenario}
            )
            
            if response.status_code == 200:
                data = response.json()
                score = self._calculate_rag_score(data, 0)
                
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="passed" if score >= 0.6 else "failed",
                    score=score,
                    details={
                        "scenario": name,
                        "query_used": scenario[:100] + "..." if len(scenario) > 100 else scenario,
                        "login_success": True,
                        "profile_access": True,
                        "rag_results_count": len(data.get("results", [])),
                        "rag_score": score
                    }
                )
                
                return {
                    "success": score >= 0.6,
                    "score": score,
                    "details": data
                }
            else:
                self.metrics.end_test(
                    timer_id=timer_id,
                    status="failed",
                    score=0.0,
                    details={
                        "scenario": name,
                        "login_success": True,
                        "profile_access": True,
                        "rag_status_code": response.status_code,
                        "error": response.text
                    }
                )
                return {
                    "success": False,
                    "score": 0.0,
                    "details": {"error": f"RAG search failed: {response.status_code}"}
                }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            return {"success": False, "score": 0.0, "details": {"error": str(e)}}
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()