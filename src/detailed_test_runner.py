# src/detailed_test_runner.py
import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetailedTestRunner:
    """Actually tests the Sales EVA service with detailed metrics"""
    
    def __init__(self, base_url: str, metrics_collector):
        self.base_url = base_url.rstrip('/')
        self.metrics = metrics_collector
        self.session_cookie = None
        self.client = None
    
    async def _get_client(self):
        """Get HTTP client with session support"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                cookies=self.session_cookie if self.session_cookie else {}
            )
        return self.client
    
    async def run_login_test(self, username: str, password: str, test_name: str) -> Dict:
        """Run login test with detailed inputs/outputs"""
        # Start test with inputs
        timer_id = self.metrics.start_test(
            test_id=f"login_{username}",
            test_type="login",
            test_name=test_name,
            inputs={
                "username": username,
                "password": "[HIDDEN]" if password else "",
                "expected_success": username in ["sales1", "expert1", "admin"] and password == "demo123"
            }
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            # Clear any existing session
            self.session_cookie = None
            client.cookies.clear()
            
            # Make request
            response = await client.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password}
            )
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Parse response
            response_data = None
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text}
            else:
                response_data = {"raw_response": response.text}
            
            # Calculate score and status
            expected_success = username in ["sales1", "expert1", "admin"] and password == "demo123"
            actual_success = response.status_code == 200
            
            if expected_success == actual_success:
                score = 1.0
                status = "passed"
                justification = f"Login {'succeeded' if actual_success else 'failed'} as expected"
            else:
                score = 0.0
                status = "failed"
                justification = f"Login {'succeeded unexpectedly' if actual_success else 'failed unexpectedly'}. Expected: {'success' if expected_success else 'failure'}"
            
            # Store session if login successful
            if actual_success and response.cookies:
                self.session_cookie = response.cookies
                client.cookies.update(self.session_cookie)
            
            # End test with outputs and justification
            self.metrics.end_test(
                timer_id=timer_id,
                status=status,
                score=score,
                outputs={
                    "status_code": response.status_code,
                    "response_data": response_data,
                    "session_established": actual_success and bool(response.cookies),
                    "response_time_ms": duration_ms,
                    "actual_success": actual_success
                },
                details={
                    "expected_success": expected_success,
                    "actual_success": actual_success,
                    "match": expected_success == actual_success
                },
                justification=justification
            )
            
            return {
                "success": status == "passed",
                "score": score,
                "timer_id": timer_id,
                "details": response_data
            }
            
        except Exception as e:
            # Record error
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"Test failed with error: {str(e)}"
            )
            raise
    
    async def run_agent_test(self, function: str) -> Dict:
        """Run agent function test with detailed metrics"""
        # Define test queries
        queries = {
            "matching": "Find relevant AI and cloud solutions for banking fraud detection",
            "gap_analysis": "What are common gaps in digital transformation projects for banks?",
            "research": "Latest trends and best practices in AI-powered fraud detection",
            "reporting": "How to structure a sales proposal for cybersecurity solutions"
        }
        
        query = queries.get(function, "Test query for agent function")
        
        # Start test
        timer_id = self.metrics.start_test(
            test_id=f"agent_{function}",
            test_type="agent",
            test_name=f"Agent {function}",
            inputs={
                "function": function,
                "query": query,
                "expected_response": "JSON response with results",
                "required_fields": ["results", "query"],
                "min_results": 1
            }
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            response = await client.post(
                f"{self.base_url}/api/rag/search",
                json={"query": query}
            )
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Parse response
            response_data = None
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text, "parse_error": True}
            else:
                response_data = {"raw_response": response.text}
            
            # Calculate score based on multiple criteria
            score_components = {}
            total_score = 0
            max_score = 0
            
            # Criteria 1: HTTP Status (30% weight)
            max_score += 30
            if response.status_code == 200:
                score_components["http_status"] = 30
                total_score += 30
            elif response.status_code == 401:
                score_components["http_status"] = 0
                total_score += 0
            else:
                score_components["http_status"] = 10  # Partial credit for other 2xx/3xx
                total_score += 10
            
            # Criteria 2: Response format (20% weight)
            max_score += 20
            if isinstance(response_data, dict):
                score_components["response_format"] = 20
                total_score += 20
            else:
                score_components["response_format"] = 5
                total_score += 5
            
            # Criteria 3: Has results (30% weight)
            max_score += 30
            if isinstance(response_data, dict) and "results" in response_data:
                results = response_data.get("results", [])
                if isinstance(results, list) and len(results) > 0:
                    score_components["has_results"] = 30
                    total_score += 30
                elif len(results) == 0:
                    score_components["has_results"] = 15  # Empty results
                    total_score += 15
                else:
                    score_components["has_results"] = 0
                    total_score += 0
            else:
                score_components["has_results"] = 0
                total_score += 0
            
            # Criteria 4: Response time (20% weight)
            max_score += 20
            if duration_ms < 3000:
                score_components["response_time"] = 20
                total_score += 20
            elif duration_ms < 10000:
                score_components["response_time"] = 15
                total_score += 15
            else:
                score_components["response_time"] = 5
                total_score += 5
            
            # Normalize score to 0-1
            normalized_score = total_score / max_score if max_score > 0 else 0
            
            # Determine status
            if response.status_code == 200 and normalized_score >= 0.6:
                status = "passed"
                justification = f"Agent function responded successfully. Score based on: HTTP status ({score_components['http_status']}/30), format ({score_components['response_format']}/20), results ({score_components['has_results']}/30), speed ({score_components['response_time']}/20)"
            else:
                status = "failed"
                justification = f"Agent function failed. HTTP {response.status_code}. Score breakdown: HTTP status ({score_components['http_status']}/30), format ({score_components['response_format']}/20), results ({score_components['has_results']}/30), speed ({score_components['response_time']}/20)"
            
            # End test
            self.metrics.end_test(
                timer_id=timer_id,
                status=status,
                score=normalized_score,
                outputs={
                    "status_code": response.status_code,
                    "response_data": response_data,
                    "response_time_ms": duration_ms,
                    "score_components": score_components,
                    "total_score": total_score,
                    "max_score": max_score
                },
                details={
                    "function": function,
                    "query": query,
                    "response_keys": list(response_data.keys()) if isinstance(response_data, dict) else []
                },
                justification=justification
            )
            
            return {
                "success": status == "passed",
                "score": normalized_score,
                "timer_id": timer_id,
                "details": response_data
            }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"Test failed with error: {str(e)}"
            )
            raise
    
    # Similar methods for KB tests, prompt tests, etc.
    # ... (Add similar detailed implementations for other test types)

    # src/detailed_test_runner.py (continued from your code)

    async def run_kb_test(self, category: str) -> Dict:
        """Run knowledge base test with detailed metrics"""
        # Define test queries based on category
        category_queries = {
            "coverage": [
                "What cloud solutions are available for banking?",
                "How does AI help in fraud detection?",
                "What are the best practices for digital transformation?"
            ],
            "freshness": [
                "Latest trends in cloud computing 2024",
                "Recent advances in AI for cybersecurity",
                "New regulations for data privacy"
            ],
            "consistency": [
                "What is the difference between public and private cloud?",
                "Compare machine learning vs deep learning",
                "Benefits of microservices architecture"
            ],
            "relevance": [
                "Sales strategies for cloud migration",
                "How to pitch AI solutions to banks",
                "ROI calculation for digital transformation"
            ],
            "completeness": [
                "Comprehensive guide to cloud security",
                "Complete AI implementation framework",
                "End-to-end digital transformation methodology"
            ]
        }
        
        queries = category_queries.get(category, ["Test query for knowledge base"])
        
        # Start test
        timer_id = self.metrics.start_test(
            test_id=f"kb_{category}",
            test_type="kb",
            test_name=f"KB {category.title()} Test",
            inputs={
                "category": category,
                "query_count": len(queries),
                "queries": queries,
                "expected_response": "JSON with relevant results",
                "min_relevance_score": 0.5
            }
        )
        
        try:
            client = await self._get_client()
            
            results_summary = {
                "total_queries": len(queries),
                "successful_responses": 0,
                "total_results": 0,
                "avg_relevance": 0,
                "response_times": []
            }
            
            detailed_results = []
            
            for i, query in enumerate(queries):
                query_start = datetime.now()
                
                try:
                    response = await client.post(
                        f"{self.base_url}/api/rag/search",
                        json={"query": query}
                    )
                    
                    query_end = datetime.now()
                    duration_ms = (query_end - query_start).total_seconds() * 1000
                    results_summary["response_times"].append(duration_ms)
                    
                    if response.status_code == 200:
                        response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"raw_response": response.text}
                        
                        results_summary["successful_responses"] += 1
                        
                        if isinstance(response_data, dict) and "results" in response_data:
                            results = response_data.get("results", [])
                            if isinstance(results, list):
                                results_summary["total_results"] += len(results)
                                
                                # Calculate relevance (simplified - could be enhanced)
                                relevance = min(1.0, len(results) / 10) if results else 0.0
                                results_summary["avg_relevance"] += relevance
                        
                        detailed_results.append({
                            "query": query,
                            "status_code": response.status_code,
                            "results_count": len(response_data.get("results", [])) if isinstance(response_data, dict) else 0,
                            "response_time_ms": duration_ms,
                            "success": response.status_code == 200
                        })
                    else:
                        detailed_results.append({
                            "query": query,
                            "status_code": response.status_code,
                            "error": "Non-200 response",
                            "response_time_ms": duration_ms,
                            "success": False
                        })
                        
                except Exception as query_error:
                    detailed_results.append({
                        "query": query,
                        "status_code": 0,
                        "error": str(query_error),
                        "success": False
                    })
            
            # Calculate overall metrics
            if results_summary["total_queries"] > 0:
                success_rate = results_summary["successful_responses"] / results_summary["total_queries"]
                avg_response_time = sum(results_summary["response_times"]) / len(results_summary["response_times"]) if results_summary["response_times"] else 0
                
                if results_summary["successful_responses"] > 0:
                    results_summary["avg_relevance"] /= results_summary["successful_responses"]
            else:
                success_rate = 0
                avg_response_time = 0
            
            # Calculate score based on multiple criteria
            score_components = {}
            total_score = 0
            max_score = 100
            
            # Criteria 1: Success rate (40% weight)
            score_components["success_rate"] = success_rate * 40
            total_score += score_components["success_rate"]
            
            # Criteria 2: Result quality (30% weight)
            avg_results_per_query = results_summary["total_results"] / max(1, results_summary["successful_responses"])
            result_quality = min(1.0, avg_results_per_query / 5)  # Target: 5 results per query
            score_components["result_quality"] = result_quality * 30
            total_score += score_components["result_quality"]
            
            # Criteria 3: Response time (20% weight)
            if avg_response_time < 2000:
                time_score = 20
            elif avg_response_time < 5000:
                time_score = 15
            elif avg_response_time < 10000:
                time_score = 10
            else:
                time_score = 5
            score_components["response_time"] = time_score
            total_score += score_components["response_time"]
            
            # Criteria 4: Consistency (10% weight)
            if results_summary["successful_responses"] == results_summary["total_queries"]:
                consistency_score = 10
            elif success_rate > 0.7:
                consistency_score = 8
            elif success_rate > 0.5:
                consistency_score = 5
            else:
                consistency_score = 2
            score_components["consistency"] = consistency_score
            total_score += score_components["consistency"]
            
            # Normalize score to 0-1
            normalized_score = total_score / max_score
            
            # Determine status
            if normalized_score >= 0.7:
                status = "passed"
                justification = f"KB {category} test passed with {success_rate*100:.1f}% success rate, {results_summary['total_results']} total results, avg response time {avg_response_time:.0f}ms"
            elif normalized_score >= 0.4:
                status = "warning"
                justification = f"KB {category} test partially passed with {success_rate*100:.1f}% success rate. Needs improvement in result quality or response time."
            else:
                status = "failed"
                justification = f"KB {category} test failed with only {success_rate*100:.1f}% success rate"
            
            # End test
            self.metrics.end_test(
                timer_id=timer_id,
                status=status,
                score=normalized_score,
                outputs={
                    "summary": results_summary,
                    "detailed_results": detailed_results,
                    "score_components": score_components,
                    "total_score": total_score,
                    "max_score": max_score
                },
                details={
                    "category": category,
                    "success_rate": success_rate,
                    "avg_response_time_ms": avg_response_time,
                    "total_results": results_summary["total_results"]
                },
                justification=justification
            )
            
            return {
                "success": status == "passed",
                "score": normalized_score,
                "timer_id": timer_id,
                "details": results_summary
            }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"KB test failed with error: {str(e)}"
            )
            raise
    
    async def run_prompt_test(self, prompt_count: int, test_case_count: int) -> Dict:
        """Run prompt testing with multiple variations"""
        # Start test
        timer_id = self.metrics.start_test(
            test_id=f"prompt_test_{prompt_count}x{test_case_count}",
            test_type="prompt",
            test_name=f"Prompt Testing ({prompt_count} prompts, {test_case_count} cases)",
            inputs={
                "prompt_count": prompt_count,
                "test_case_count": test_case_count,
                "prompt_types": ["instructional", "role-based", "concise", "detailed", "conversational"],
                "test_categories": ["banking", "retail", "healthcare", "manufacturing", "technology"]
            }
        )
        
        try:
            client = await self._get_client()
            
            # Generate test prompts
            test_prompts = self._generate_test_prompts(prompt_count)
            test_cases = self._generate_test_cases(test_case_count)
            
            results = {
                "total_tests": 0,
                "successful_tests": 0,
                "total_responses": 0,
                "avg_response_length": 0,
                "avg_response_time": 0,
                "prompt_performance": {},
                "category_performance": {}
            }
            
            detailed_results = []
            response_times = []
            
            # Test each prompt with each test case
            for prompt_idx, prompt in enumerate(test_prompts):
                prompt_results = []
                
                for case_idx, test_case in enumerate(test_cases):
                    test_start = datetime.now()
                    
                    try:
                        # Combine prompt with test case
                        full_query = f"{prompt}\n\nOpportunity: {test_case['description']}\nIndustry: {test_case['industry']}\nRequirements: {test_case['requirements']}"
                        
                        response = await client.post(
                            f"{self.base_url}/api/rag/search",
                            json={"query": full_query}
                        )
                        
                        test_end = datetime.now()
                        duration_ms = (test_end - test_start).total_seconds() * 1000
                        response_times.append(duration_ms)
                        
                        results["total_tests"] += 1
                        
                        if response.status_code == 200:
                            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"raw_response": response.text}
                            
                            results["successful_tests"] += 1
                            
                            if isinstance(response_data, dict):
                                response_text = str(response_data)
                                results["total_responses"] += 1
                                results["avg_response_length"] += len(response_text)
                                
                                # Track performance by prompt type
                                prompt_type = prompt.get("type", "unknown")
                                if prompt_type not in results["prompt_performance"]:
                                    results["prompt_performance"][prompt_type] = {
                                        "count": 0,
                                        "success": 0,
                                        "avg_score": 0
                                    }
                                results["prompt_performance"][prompt_type]["count"] += 1
                                results["prompt_performance"][prompt_type]["success"] += 1
                                
                                # Track performance by category
                                category = test_case.get("industry", "unknown")
                                if category not in results["category_performance"]:
                                    results["category_performance"][category] = {
                                        "count": 0,
                                        "success": 0,
                                        "avg_score": 0
                                    }
                                results["category_performance"][category]["count"] += 1
                                results["category_performance"][category]["success"] += 1
                            
                            prompt_results.append({
                                "test_case": test_case["description"],
                                "status_code": response.status_code,
                                "response_time_ms": duration_ms,
                                "success": True,
                                "has_results": "results" in response_data if isinstance(response_data, dict) else False
                            })
                        else:
                            prompt_results.append({
                                "test_case": test_case["description"],
                                "status_code": response.status_code,
                                "response_time_ms": duration_ms,
                                "success": False,
                                "error": f"HTTP {response.status_code}"
                            })
                            
                    except Exception as test_error:
                        prompt_results.append({
                            "test_case": test_case["description"],
                            "status_code": 0,
                            "error": str(test_error),
                            "success": False
                        })
                
                detailed_results.append({
                    "prompt": prompt["content"][:100] + "...",
                    "prompt_type": prompt["type"],
                    "results": prompt_results,
                    "success_rate": sum(1 for r in prompt_results if r["success"]) / len(prompt_results) if prompt_results else 0
                })
            
            # Calculate overall metrics
            success_rate = results["successful_tests"] / results["total_tests"] if results["total_tests"] > 0 else 0
            
            if results["total_responses"] > 0:
                results["avg_response_length"] /= results["total_responses"]
            
            if response_times:
                results["avg_response_time"] = sum(response_times) / len(response_times)
            
            # Calculate scores for each prompt type
            for prompt_type, perf in results["prompt_performance"].items():
                if perf["count"] > 0:
                    perf["success_rate"] = perf["success"] / perf["count"]
                    # Score based on success rate and average response quality
                    perf["avg_score"] = min(1.0, perf["success_rate"] * 0.7 + 0.3)  # Base score
            
            # Calculate score
            score_components = {}
            total_score = 0
            max_score = 100
            
            # Criteria 1: Overall success rate (40% weight)
            score_components["success_rate"] = success_rate * 40
            total_score += score_components["success_rate"]
            
            # Criteria 2: Response quality (30% weight)
            avg_results_per_test = results["total_responses"] / max(1, results["successful_tests"])
            response_quality = min(1.0, avg_results_per_test / 3)  # Target: 3 results per test
            score_components["response_quality"] = response_quality * 30
            total_score += score_components["response_quality"]
            
            # Criteria 3: Response time (20% weight)
            if results["avg_response_time"] < 3000:
                time_score = 20
            elif results["avg_response_time"] < 7000:
                time_score = 15
            elif results["avg_response_time"] < 15000:
                time_score = 10
            else:
                time_score = 5
            score_components["response_time"] = time_score
            total_score += score_components["response_time"]
            
            # Criteria 4: Coverage (10% weight)
            unique_categories = len(results["category_performance"])
            coverage_score = min(10, unique_categories * 2)  # 2 points per category up to 10
            score_components["coverage"] = coverage_score
            total_score += score_components["coverage"]
            
            # Normalize score to 0-1
            normalized_score = total_score / max_score
            
            # Determine best performing prompt type
            best_prompt_type = None
            best_prompt_score = 0
            for prompt_type, perf in results["prompt_performance"].items():
                if perf.get("avg_score", 0) > best_prompt_score:
                    best_prompt_score = perf["avg_score"]
                    best_prompt_type = prompt_type
            
            # Determine status
            if normalized_score >= 0.7:
                status = "passed"
                justification = f"Prompt testing passed with {success_rate*100:.1f}% success rate. Best prompt type: {best_prompt_type} ({best_prompt_score:.2f})"
            elif normalized_score >= 0.5:
                status = "warning"
                justification = f"Prompt testing partially passed with {success_rate*100:.1f}% success rate. Best prompt type: {best_prompt_type}"
            else:
                status = "failed"
                justification = f"Prompt testing failed with only {success_rate*100:.1f}% success rate"
            
            # End test
            self.metrics.end_test(
                timer_id=timer_id,
                status=status,
                score=normalized_score,
                outputs={
                    "summary": results,
                    "detailed_results": detailed_results[:10],  # Limit detailed output
                    "score_components": score_components,
                    "total_score": total_score,
                    "max_score": max_score,
                    "best_prompt_type": best_prompt_type,
                    "best_prompt_score": best_prompt_score
                },
                details={
                    "prompt_count": prompt_count,
                    "test_case_count": test_case_count,
                    "success_rate": success_rate,
                    "avg_response_time_ms": results["avg_response_time"],
                    "best_performing_prompt": best_prompt_type
                },
                justification=justification
            )
            
            return {
                "success": status == "passed",
                "score": normalized_score,
                "timer_id": timer_id,
                "details": results
            }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"Prompt test failed with error: {str(e)}"
            )
            raise
    
    async def run_e2e_scenario(self, scenario_name: str, scenario_description: str) -> Dict:
        """Run end-to-end scenario test"""
        # Start test
        timer_id = self.metrics.start_test(
            test_id=f"e2e_{scenario_name.lower().replace(' ', '_')}",
            test_type="e2e",
            test_name=f"E2E Scenario: {scenario_name}",
            inputs={
                "scenario_name": scenario_name,
                "scenario_description": scenario_description,
                "steps": [
                    "Login with valid credentials",
                    "Analyze opportunity with agent",
                    "Search knowledge base",
                    "Generate recommendations",
                    "Create proposal outline"
                ]
            }
        )
        
        try:
            client = await self._get_client()
            start_time = datetime.now()
            
            # Step 1: Login (if needed)
            login_success = False
            if not self.session_cookie:
                try:
                    login_response = await client.post(
                        f"{self.base_url}/login",
                        json={"username": "sales1", "password": "demo123"}
                    )
                    login_success = login_response.status_code == 200
                    if login_success and login_response.cookies:
                        self.session_cookie = login_response.cookies
                        client.cookies.update(self.session_cookie)
                except:
                    login_success = False
            
            # Step 2: Analyze opportunity with agent
            agent_response = None
            agent_success = False
            try:
                agent_response = await client.post(
                    f"{self.base_url}/api/rag/search",
                    json={"query": f"Analyze this opportunity: {scenario_description}"}
                )
                agent_success = agent_response.status_code == 200
            except:
                agent_success = False
            
            # Step 3: Search knowledge base for specific solutions
            kb_responses = []
            kb_success = False
            kb_queries = [
                f"Cloud solutions for {scenario_name.split()[0].lower()} industry",
                f"AI applications for {scenario_description.split()[0].lower()}",
                "Best practices for similar implementations"
            ]
            
            for query in kb_queries:
                try:
                    kb_response = await client.post(
                        f"{self.base_url}/api/rag/search",
                        json={"query": query}
                    )
                    kb_responses.append({
                        "query": query,
                        "status_code": kb_response.status_code,
                        "success": kb_response.status_code == 200,
                        "has_results": "results" in (kb_response.json() if kb_response.headers.get('content-type', '').startswith('application/json') else {})
                    })
                except:
                    kb_responses.append({
                        "query": query,
                        "status_code": 0,
                        "success": False,
                        "error": "Request failed"
                    })
            
            kb_success_count = sum(1 for r in kb_responses if r["success"])
            kb_success = kb_success_count >= 2  # At least 2 successful KB queries
            
            # Step 4: Generate recommendations
            recommendations = []
            recommendation_success = False
            try:
                rec_response = await client.post(
                    f"{self.base_url}/api/rag/search",
                    json={"query": f"Generate sales recommendations for: {scenario_description}"}
                )
                if rec_response.status_code == 200:
                    rec_data = rec_response.json() if rec_response.headers.get('content-type', '').startswith('application/json') else {}
                    if isinstance(rec_data, dict) and "results" in rec_data:
                        recommendations = rec_data["results"][:3] if isinstance(rec_data["results"], list) else []
                        recommendation_success = len(recommendations) > 0
            except:
                recommendation_success = False
            
            end_time = datetime.now()
            total_duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Calculate scores for each step
            step_scores = {
                "login": 20 if login_success else 0,
                "agent_analysis": 25 if agent_success else 5,
                "kb_search": (kb_success_count / 3) * 30,  # Up to 30 points
                "recommendations": 15 if recommendation_success else 5,
                "performance": 10 if total_duration_ms < 15000 else 5 if total_duration_ms < 30000 else 0
            }
            
            total_score = sum(step_scores.values())
            max_score = 100
            normalized_score = total_score / max_score
            
            # Determine status
            if normalized_score >= 0.7:
                status = "passed"
                justification = f"E2E scenario '{scenario_name}' completed successfully with {total_score}/100 points"
            elif normalized_score >= 0.5:
                status = "warning"
                justification = f"E2E scenario '{scenario_name}' partially completed with {total_score}/100 points"
            else:
                status = "failed"
                justification = f"E2E scenario '{scenario_name}' failed with only {total_score}/100 points"
            
            # End test
            self.metrics.end_test(
                timer_id=timer_id,
                status=status,
                score=normalized_score,
                outputs={
                    "step_results": {
                        "login": {"success": login_success, "score": step_scores["login"]},
                        "agent_analysis": {"success": agent_success, "score": step_scores["agent_analysis"]},
                        "kb_search": {"success": kb_success, "count": kb_success_count, "score": step_scores["kb_search"]},
                        "recommendations": {"success": recommendation_success, "count": len(recommendations), "score": step_scores["recommendations"]},
                        "performance": {"duration_ms": total_duration_ms, "score": step_scores["performance"]}
                    },
                    "step_scores": step_scores,
                    "total_score": total_score,
                    "max_score": max_score,
                    "recommendations": recommendations[:3] if recommendations else []
                },
                details={
                    "scenario_name": scenario_name,
                    "total_duration_ms": total_duration_ms,
                    "successful_steps": sum([
                        1 if login_success else 0,
                        1 if agent_success else 0,
                        1 if kb_success else 0,
                        1 if recommendation_success else 0
                    ]),
                    "total_steps": 4
                },
                justification=justification
            )
            
            return {
                "success": status == "passed",
                "score": normalized_score,
                "timer_id": timer_id,
                "details": {
                    "scenario": scenario_name,
                    "total_score": total_score,
                    "duration_ms": total_duration_ms
                }
            }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"E2E scenario failed with error: {str(e)}"
            )
            raise
    
    # Add this method to your DetailedTestRunner class in src/detailed_test_runner.py

    async def run_prompt_test(self, prompt_count: int, test_case_count: int) -> Dict:
        """Run prompt testing with multiple variations and save detailed results"""
        # Start test
        timer_id = self.metrics.start_test(
            test_id=f"prompt_test_{prompt_count}x{test_case_count}",
            test_type="prompt",
            test_name=f"Prompt Testing ({prompt_count} prompts, {test_case_count} cases)",
            inputs={
                "prompt_count": prompt_count,
                "test_case_count": test_case_count,
                "prompt_types": ["instructional", "role-based", "concise", "detailed", "conversational"],
                "test_categories": ["banking", "retail", "healthcare", "manufacturing", "technology"]
            }
        )
        
        try:
            client = await self._get_client()
            
            # Generate test prompts
            test_prompts = self._generate_test_prompts(prompt_count)
            test_cases = self._generate_test_cases(test_case_count)
            
            results = {
                "total_tests": 0,
                "successful_tests": 0,
                "total_responses": 0,
                "avg_response_length": 0,
                "avg_response_time": 0,
                "prompt_performance": {},
                "category_performance": {},
                "detailed_responses": []  # NEW: Store all detailed responses
            }
            
            detailed_responses = []
            response_times = []
            
            # Test each prompt with each test case
            for prompt_idx, prompt in enumerate(test_prompts):
                prompt_responses = []
                
                for case_idx, test_case in enumerate(test_cases):
                    test_start = datetime.now()
                    
                    try:
                        # Combine prompt with test case
                        full_query = f"{prompt['content']}\n\nOpportunity: {test_case['description']}\nIndustry: {test_case['industry']}\nRequirements: {test_case['requirements']}"
                        
                        response = await client.post(
                            f"{self.base_url}/api/rag/search",
                            json={"query": full_query}
                        )
                        
                        test_end = datetime.now()
                        duration_ms = (test_end - test_start).total_seconds() * 1000
                        response_times.append(duration_ms)
                        
                        results["total_tests"] += 1
                        
                        # Parse response
                        response_data = None
                        if response.status_code == 200:
                            if response.headers.get('content-type', '').startswith('application/json'):
                                try:
                                    response_data = response.json()
                                except:
                                    response_data = {"raw_response": response.text}
                            else:
                                response_data = {"raw_response": response.text}
                            
                            results["successful_tests"] += 1
                            
                            # Store detailed response
                            detailed_response = {
                                "prompt_id": prompt_idx + 1,
                                "prompt_type": prompt["type"],
                                "prompt_content": prompt["content"],
                                "test_case_id": case_idx + 1,
                                "test_case": test_case,
                                "full_query": full_query,
                                "status_code": response.status_code,
                                "response_time_ms": duration_ms,
                                "response_data": response_data,
                                "success": True,
                                "has_results": "results" in response_data if isinstance(response_data, dict) else False,
                                "results_count": len(response_data.get("results", [])) if isinstance(response_data, dict) and "results" in response_data else 0
                            }
                            detailed_responses.append(detailed_response)
                            
                            if isinstance(response_data, dict):
                                response_text = str(response_data)
                                results["total_responses"] += 1
                                results["avg_response_length"] += len(response_text)
                                
                                # Track performance by prompt type
                                prompt_type = prompt.get("type", "unknown")
                                if prompt_type not in results["prompt_performance"]:
                                    results["prompt_performance"][prompt_type] = {
                                        "count": 0,
                                        "success": 0,
                                        "avg_score": 0
                                    }
                                results["prompt_performance"][prompt_type]["count"] += 1
                                results["prompt_performance"][prompt_type]["success"] += 1
                                
                                # Track performance by category
                                category = test_case.get("industry", "unknown")
                                if category not in results["category_performance"]:
                                    results["category_performance"][category] = {
                                        "count": 0,
                                        "success": 0,
                                        "avg_score": 0
                                    }
                                results["category_performance"][category]["count"] += 1
                                results["category_performance"][category]["success"] += 1
                            
                            prompt_responses.append({
                                "test_case": test_case["description"],
                                "status_code": response.status_code,
                                "response_time_ms": duration_ms,
                                "success": True,
                                "has_results": "results" in response_data if isinstance(response_data, dict) else False
                            })
                        else:
                            # Store failed response details
                            detailed_response = {
                                "prompt_id": prompt_idx + 1,
                                "prompt_type": prompt["type"],
                                "prompt_content": prompt["content"],
                                "test_case_id": case_idx + 1,
                                "test_case": test_case,
                                "full_query": full_query,
                                "status_code": response.status_code,
                                "response_time_ms": duration_ms,
                                "response_data": {"error": f"HTTP {response.status_code}", "response_text": response.text},
                                "success": False,
                                "has_results": False,
                                "results_count": 0
                            }
                            detailed_responses.append(detailed_response)
                            
                            prompt_responses.append({
                                "test_case": test_case["description"],
                                "status_code": response.status_code,
                                "response_time_ms": duration_ms,
                                "success": False,
                                "error": f"HTTP {response.status_code}"
                            })
                            
                    except Exception as test_error:
                        # Store error details
                        detailed_response = {
                            "prompt_id": prompt_idx + 1,
                            "prompt_type": prompt["type"],
                            "prompt_content": prompt["content"],
                            "test_case_id": case_idx + 1,
                            "test_case": test_case,
                            "full_query": full_query,
                            "status_code": 0,
                            "response_time_ms": 0,
                            "response_data": {"error": str(test_error)},
                            "success": False,
                            "has_results": False,
                            "results_count": 0
                        }
                        detailed_responses.append(detailed_response)
                        
                        prompt_responses.append({
                            "test_case": test_case["description"],
                            "status_code": 0,
                            "error": str(test_error),
                            "success": False
                        })
                
                # Store prompt responses for this prompt
                results["detailed_responses"].append({
                    "prompt": prompt["content"],
                    "prompt_type": prompt["type"],
                    "responses": prompt_responses,
                    "success_rate": sum(1 for r in prompt_responses if r["success"]) / len(prompt_responses) if prompt_responses else 0
                })
            
            # Save detailed responses to file
            self._save_detailed_responses(detailed_responses, f"prompt_test_{prompt_count}x{test_case_count}")
            
            # Calculate overall metrics
            success_rate = results["successful_tests"] / results["total_tests"] if results["total_tests"] > 0 else 0
            
            if results["total_responses"] > 0:
                results["avg_response_length"] /= results["total_responses"]
            
            if response_times:
                results["avg_response_time"] = sum(response_times) / len(response_times)
            
            # Calculate scores for each prompt type
            for prompt_type, perf in results["prompt_performance"].items():
                if perf["count"] > 0:
                    perf["success_rate"] = perf["success"] / perf["count"]
                    # Score based on success rate and average response quality
                    perf["avg_score"] = min(1.0, perf["success_rate"] * 0.7 + 0.3)  # Base score
            
            # Calculate score
            score_components = {}
            total_score = 0
            max_score = 100
            
            # Criteria 1: Overall success rate (40% weight)
            score_components["success_rate"] = success_rate * 40
            total_score += score_components["success_rate"]
            
            # Criteria 2: Response quality (30% weight)
            avg_results_per_test = results["total_responses"] / max(1, results["successful_tests"])
            response_quality = min(1.0, avg_results_per_test / 3)  # Target: 3 results per test
            score_components["response_quality"] = response_quality * 30
            total_score += score_components["response_quality"]
            
            # Criteria 3: Response time (20% weight)
            if results["avg_response_time"] < 3000:
                time_score = 20
            elif results["avg_response_time"] < 7000:
                time_score = 15
            elif results["avg_response_time"] < 15000:
                time_score = 10
            else:
                time_score = 5
            score_components["response_time"] = time_score
            total_score += score_components["response_time"]
            
            # Criteria 4: Coverage (10% weight)
            unique_categories = len(results["category_performance"])
            coverage_score = min(10, unique_categories * 2)  # 2 points per category up to 10
            score_components["coverage"] = coverage_score
            total_score += score_components["coverage"]
            
            # Normalize score to 0-1
            normalized_score = total_score / max_score
            
            # Determine best performing prompt type
            best_prompt_type = None
            best_prompt_score = 0
            for prompt_type, perf in results["prompt_performance"].items():
                if perf.get("avg_score", 0) > best_prompt_score:
                    best_prompt_score = perf["avg_score"]
                    best_prompt_type = prompt_type
            
            # Determine status
            if normalized_score >= 0.7:
                status = "passed"
                justification = f"Prompt testing passed with {success_rate*100:.1f}% success rate. Best prompt type: {best_prompt_type} ({best_prompt_score:.2f})"
            elif normalized_score >= 0.5:
                status = "warning"
                justification = f"Prompt testing partially passed with {success_rate*100:.1f}% success rate. Best prompt type: {best_prompt_type}"
            else:
                status = "failed"
                justification = f"Prompt testing failed with only {success_rate*100:.1f}% success rate"
            
            # End test
            self.metrics.end_test(
                timer_id=timer_id,
                status=status,
                score=normalized_score,
                outputs={
                    "summary": results,
                    "score_components": score_components,
                    "total_score": total_score,
                    "max_score": max_score,
                    "best_prompt_type": best_prompt_type,
                    "best_prompt_score": best_prompt_score,
                    "total_responses": len(detailed_responses),
                    "saved_responses_file": f"prompt_test_{prompt_count}x{test_case_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                },
                details={
                    "prompt_count": prompt_count,
                    "test_case_count": test_case_count,
                    "success_rate": success_rate,
                    "avg_response_time_ms": results["avg_response_time"],
                    "best_performing_prompt": best_prompt_type,
                    "total_detailed_responses": len(detailed_responses)
                },
                justification=justification
            )
            
            return {
                "success": status == "passed",
                "score": normalized_score,
                "timer_id": timer_id,
                "details": results
            }
                
        except Exception as e:
            self.metrics.end_test(
                timer_id=timer_id,
                status="error",
                score=0.0,
                outputs={"error": str(e)},
                justification=f"Prompt test failed with error: {str(e)}"
            )
            raise
    
    def _save_detailed_responses(self, responses: List[Dict], test_name: str):
        """Save detailed responses to a JSON file"""
        try:
            from pathlib import Path
            import json
            
            # Create responses directory
            responses_dir = Path("data/responses")
            responses_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_{timestamp}.json"
            filepath = responses_dir / filename
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump({
                    "test_name": test_name,
                    "timestamp": datetime.now().isoformat(),
                    "total_responses": len(responses),
                    "responses": responses
                }, f, indent=2, default=str)
            
            logger.info(f"Saved {len(responses)} detailed responses to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save detailed responses: {e}")
            return None
    
    def _generate_test_prompts(self, count: int) -> List[Dict]:
        """Generate test prompts for evaluation"""
        prompt_templates = [
            {
                "type": "instructional",
                "content": "Analyze the following sales opportunity and provide relevant solutions from our offerings."
            },
            {
                "type": "role-based",
                "content": "As a sales expert, review this opportunity and suggest the most appropriate solutions."
            },
            {
                "type": "concise",
                "content": "Find solutions for:"
            },
            {
                "type": "detailed",
                "content": "Please analyze this sales opportunity in detail. Consider the industry, requirements, and business objectives. Provide comprehensive recommendations with relevant solutions from our portfolio."
            },
            {
                "type": "conversational",
                "content": "Hey, I've got this opportunity. Can you help me find the right solutions? Here are the details:"
            }
        ]
        
        # Generate variations
        prompts = []
        for i in range(count):
            template = prompt_templates[i % len(prompt_templates)]
            variation = template.copy()
            variation["content"] = f"Test Prompt {i+1}: {template['content']}"
            prompts.append(variation)
        
        return prompts
    
    def _generate_test_cases(self, count: int) -> List[Dict]:
        """Generate test cases for prompt evaluation"""
        industries = ["Banking", "Retail", "Healthcare", "Manufacturing", "Technology", "Insurance", "Education", "Government"]
        opportunity_types = [
            "Digital Transformation",
            "Cloud Migration",
            "AI Implementation",
            "Cybersecurity Enhancement",
            "Data Analytics",
            "IoT Deployment",
            "Mobile App Development",
            "Process Automation"
        ]
        
        test_cases = []
        for i in range(count):
            industry = random.choice(industries)
            opp_type = random.choice(opportunity_types)
            
            test_case = {
                "id": i + 1,
                "industry": industry,
                "type": opp_type,
                "description": f"{industry} company seeking {opp_type.lower()} solutions",
                "requirements": random.sample([
                    "Scalable architecture",
                    "High security compliance",
                    "Real-time analytics",
                    "Multi-cloud support",
                    "AI/ML capabilities",
                    "Mobile access",
                    "24/7 support",
                    "Cost optimization"
                ], random.randint(2, 4)),
                "budget_range": f"${random.randint(100, 500)}K-${random.randint(500, 2000)}K",
                "timeline": f"{random.randint(3, 12)} months"
            }
            
            test_cases.append(test_case)
        
        return test_cases

# ... rest of your existing code continues ...
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()