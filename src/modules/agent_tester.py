import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from tqdm import tqdm

from src.api_client import APIClient, TestDataGenerator
from config.settings import settings

logger = logging.getLogger(__name__)

class AgentTester:
    """
    Test Sales EVA agent capabilities without multi-agent complexity
    
    Tests the system's ability to:
    1. Match opportunities with offerings (Match Agent function)
    2. Identify gaps in offerings (Gap Agent function)
    3. Research and provide latest info (Research Agent function)
    4. Generate actionable reports (Report Agent function)
    """
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.test_generator = TestDataGenerator()
        self.results = []
        
    async def run_tests(self, test_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Run comprehensive agent capability tests
        
        Steps:
        1. Generate test opportunities using LLM
        2. Test each agent function with appropriate test cases
        3. Evaluate responses against expected criteria
        4. Generate performance analysis
        """
        logger.info("Starting agent capability testing...")
        
        test_count = test_count or settings.AGENT_TEST_COUNT
        
        # Generate test data using LLM
        logger.info(f"Generating {test_count} test scenarios using LLM...")
        test_scenarios = self._generate_agent_test_scenarios(test_count)
        
        if not test_scenarios:
            raise ValueError("Failed to generate test scenarios")
        
        logger.info(f"Testing agent functions with {len(test_scenarios)} scenarios...")
        
        # Run tests for each agent function
        test_results = await self._run_agent_tests_parallel(test_scenarios)
        
        # Analyze results
        analysis = self._analyze_agent_results(test_results)
        
        # Save results
        self._save_results(analysis)
        
        logger.info(f"Agent testing completed. Overall score: {analysis.get('overall_score', 0):.2f}")
        
        return analysis
    
    def _generate_agent_test_scenarios(self, count: int) -> List[Dict]:
        """Generate test scenarios for different agent functions using LLM"""
        prompt = f"""Generate {count} test scenarios for evaluating a Sales Virtual Assistant's capabilities.
        
        Create scenarios that test these functions:
        1. MATCHING: Finding relevant offerings/solutions for opportunities
        2. GAP ANALYSIS: Identifying missing offerings or capabilities
        3. RESEARCH: Finding latest information and case studies
        4. REPORTING: Generating comprehensive sales proposals
        
        Return ONLY a JSON array with this structure:
        {{
            "id": "AGENT_TEST_001",
            "function": "matching/gap_analysis/research/reporting",
            "scenario": "Detailed scenario description",
            "expected_elements": ["element1", "element2", "element3"],
            "complexity": "low/medium/high",
            "success_criteria": [
                "Should contain specific solution mentions",
                "Should identify gaps if any",
                "Should provide actionable insights"
            ]
        }}
        
        Distribute scenarios across all 4 functions."""
        
        try:
            response = self.test_generator._call_groq_api(prompt)
            
            # Parse JSON response
            import json
            
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            scenarios = json.loads(response.strip())
            
            # Validate and clean scenarios
            validated_scenarios = []
            function_counts = {
                "matching": 0,
                "gap_analysis": 0,
                "research": 0,
                "reporting": 0
            }
            
            for i, scenario in enumerate(scenarios[:count]):
                if not isinstance(scenario, dict):
                    continue
                
                # Determine function type
                function = str(scenario.get("function", "")).lower().replace(" ", "_")
                if function not in function_counts:
                    # Map to closest function
                    if "match" in function:
                        function = "matching"
                    elif "gap" in function:
                        function = "gap_analysis"
                    elif "research" in function:
                        function = "research"
                    elif "report" in function:
                        function = "reporting"
                    else:
                        function = "matching"  # Default
                
                validated = {
                    "id": scenario.get("id", f"AGENT_TEST_{i+1:03d}"),
                    "function": function,
                    "scenario": str(scenario.get("scenario", "")).strip(),
                    "expected_elements": [
                        str(e).strip() 
                        for e in scenario.get("expected_elements", []) 
                        if e
                    ],
                    "complexity": str(scenario.get("complexity", "medium")).lower(),
                    "success_criteria": [
                        str(c).strip()
                        for c in scenario.get("success_criteria", [])
                        if c
                    ]
                }
                
                if validated["scenario"]:  # Only add if we have content
                    function_counts[function] += 1
                    validated_scenarios.append(validated)
            
            logger.info(f"Generated scenarios by function: {function_counts}")
            return validated_scenarios
            
        except Exception as e:
            logger.error(f"Failed to generate agent test scenarios: {e}")
            return self._generate_fallback_scenarios(count)
    
    def _generate_fallback_scenarios(self, count: int) -> List[Dict]:
        """Generate fallback test scenarios"""
        scenarios = []
        
        # Define template scenarios for each function
        templates = {
            "matching": [
                "Find relevant offerings for a bank that needs AI-powered fraud detection.",
                "Match solutions for a retail chain wanting to optimize inventory with AI.",
                "Identify appropriate offerings for a hospital seeking patient data analytics."
            ],
            "gap_analysis": [
                "Analyze what's missing for a telecom company wanting quantum-safe encryption.",
                "Identify capability gaps for a manufacturing firm seeking predictive maintenance.",
                "Find missing offerings for an insurance company wanting blockchain solutions."
            ],
            "research": [
                "Find latest case studies about TCS AI implementations in banking.",
                "Research recent TCS cloud migration success stories.",
                "Find up-to-date information about TCS cybersecurity offerings."
            ],
            "reporting": [
                "Generate a sales proposal for a $50M digital transformation project.",
                "Create an executive summary for an AI implementation opportunity.",
                "Prepare a solution overview for a cloud migration engagement."
            ]
        }
        
        # Distribute scenarios evenly
        scenarios_per_function = max(1, count // len(templates))
        
        for function, templates_list in templates.items():
            for i in range(scenarios_per_function):
                if len(scenarios) >= count:
                    break
                    
                scenario_text = templates_list[i % len(templates_list)]
                scenarios.append({
                    "id": f"AGENT_FB_{function.upper()}_{i+1:03d}",
                    "function": function,
                    "scenario": scenario_text,
                    "expected_elements": ["solutions", "recommendations", "case_studies"],
                    "complexity": "medium",
                    "success_criteria": [
                        "Should provide relevant information",
                        "Should be actionable",
                        "Should reference TCS offerings"
                    ]
                })
        
        return scenarios[:count]
    
    async def _run_agent_tests_parallel(self, scenarios: List[Dict]) -> Dict[str, List[Dict]]:
        """Run tests for all scenarios in parallel"""
        results = {
            "matching": [],
            "gap_analysis": [],
            "research": [],
            "reporting": []
        }
        
        # Group scenarios by function
        scenarios_by_function = {}
        for scenario in scenarios:
            function = scenario["function"]
            if function not in scenarios_by_function:
                scenarios_by_function[function] = []
            scenarios_by_function[function].append(scenario)
        
        # Test each function group
        for function, function_scenarios in scenarios_by_function.items():
            logger.info(f"Testing {function} function with {len(function_scenarios)} scenarios...")
            
            # Create tasks for this function
            tasks = []
            for scenario in function_scenarios:
                tasks.append(self._test_single_scenario(scenario))
            
            # Execute with progress bar
            with tqdm(total=len(tasks), desc=f"Testing {function}") as pbar:
                for task in asyncio.as_completed(tasks):
                    try:
                        result = await task
                        results[function].append(result)
                    except Exception as e:
                        logger.warning(f"Scenario test failed: {e}")
                        results[function].append({
                            "scenario_id": "unknown",
                            "function": function,
                            "error": str(e),
                            "scores": {"overall": 0}
                        })
                    finally:
                        pbar.update(1)
        
        return results
    
    async def _test_single_scenario(self, scenario: Dict) -> Dict[str, Any]:
        """Test a single scenario"""
        scenario_id = scenario["id"]
        function = scenario["function"]
        scenario_text = scenario["scenario"]
        
        try:
            # Call Sales EVA API
            start_time = datetime.now()
            
            # For different functions, we might format the query differently
            query = self._format_query_for_function(scenario_text, function)
            
            response = await self.api_client.analyze_opportunity(
                opportunity_description=query
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            
            # Evaluate based on function type
            evaluation = self._evaluate_agent_response(
                response=response,
                scenario=scenario,
                function=function
            )
            
            return {
                "scenario_id": scenario_id,
                "function": function,
                "scenario": scenario_text,
                "latency": latency,
                "scores": evaluation,
                "response_summary": self._summarize_response(response),
                "complexity": scenario["complexity"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scenario {scenario_id} failed: {e}")
            return {
                "scenario_id": scenario_id,
                "function": function,
                "error": str(e),
                "scores": {"overall": 0, "error": 1.0},
                "timestamp": datetime.now().isoformat()
            }
    
    def _format_query_for_function(self, scenario_text: str, function: str) -> str:
        """Format query based on agent function being tested"""
        if function == "matching":
            return f"Find relevant offerings for: {scenario_text}"
        elif function == "gap_analysis":
            return f"Analyze what offerings are missing for: {scenario_text}"
        elif function == "research":
            return f"Find latest information about: {scenario_text}"
        elif function == "reporting":
            return f"Generate a comprehensive report for: {scenario_text}"
        else:
            return scenario_text
    
    def _evaluate_agent_response(self, 
                                response: Dict, 
                                scenario: Dict,
                                function: str) -> Dict[str, float]:
        """
        Evaluate response based on agent function and scenario criteria
        """
        scores = {"overall": 0.0}
        
        try:
            response_text = json.dumps(response).lower()
            expected_elements = [e.lower() for e in scenario["expected_elements"]]
            success_criteria = [c.lower() for c in scenario["success_criteria"]]
            
            # Function-specific evaluation
            if function == "matching":
                scores.update(self._evaluate_matching_function(
                    response_text, expected_elements, success_criteria
                ))
            elif function == "gap_analysis":
                scores.update(self._evaluate_gap_analysis_function(
                    response_text, expected_elements, success_criteria
                ))
            elif function == "research":
                scores.update(self._evaluate_research_function(
                    response_text, expected_elements, success_criteria
                ))
            elif function == "reporting":
                scores.update(self._evaluate_reporting_function(
                    response_text, expected_elements, success_criteria
                ))
            
            # Calculate overall score (weighted based on function)
            weights = self._get_function_weights(function)
            overall = sum(
                scores.get(metric, 0) * weight 
                for metric, weight in weights.items() 
                if metric in scores
            )
            scores["overall"] = min(1.0, overall)
            
        except Exception as e:
            logger.warning(f"Evaluation failed for {function}: {e}")
            scores = {"error": 1.0, "overall": 0.0}
        
        return scores
    
    def _evaluate_matching_function(self, 
                                   response_text: str,
                                   expected_elements: List[str],
                                   success_criteria: List[str]) -> Dict[str, float]:
        """Evaluate matching agent function"""
        scores = {}
        
        # 1. Solution coverage (are expected elements mentioned?)
        coverage_score = 0
        for element in expected_elements[:5]:  # Check first 5 elements
            if element in response_text:
                coverage_score += 0.2
        scores["solution_coverage"] = min(1.0, coverage_score)
        
        # 2. Relevance to criteria
        relevance_score = 0
        for criterion in success_criteria[:3]:  # Check first 3 criteria
            if any(word in response_text for word in criterion.split()[:3]):
                relevance_score += 0.33
        scores["relevance"] = min(1.0, relevance_score)
        
        # 3. Actionability (presence of action words)
        action_words = ["offer", "solution", "recommend", "suggest", "implement"]
        action_score = 0
        for word in action_words:
            if word in response_text:
                action_score += 0.2
        scores["actionability"] = min(1.0, action_score)
        
        # 4. Specificity (mentions specific offerings/solutions)
        specificity_indicators = ["tcs", "cloud", "ai", "digital", "transformation"]
        specificity_score = 0
        for indicator in specificity_indicators:
            if indicator in response_text:
                specificity_score += 0.2
        scores["specificity"] = min(1.0, specificity_score)
        
        return scores
    
    def _evaluate_gap_analysis_function(self,
                                       response_text: str,
                                       expected_elements: List[str],
                                       success_criteria: List[str]) -> Dict[str, float]:
        """Evaluate gap analysis function"""
        scores = {}
        
        # 1. Gap identification
        gap_words = ["gap", "missing", "lack", "need", "require", "improve"]
        gap_score = 0
        for word in gap_words:
            if word in response_text:
                gap_score += 0.166  # 6 words max
        scores["gap_identification"] = min(1.0, gap_score)
        
        # 2. Recommendation quality
        recommendation_words = ["recommend", "suggest", "propose", "should", "could"]
        recommendation_score = 0
        for word in recommendation_words:
            if word in response_text:
                recommendation_score += 0.2
        scores["recommendation_quality"] = min(1.0, recommendation_score)
        
        # 3. Critical thinking (analysis indicators)
        analysis_words = ["analysis", "evaluate", "assess", "consider", "however", "although"]
        analysis_score = 0
        for word in analysis_words:
            if word in response_text:
                analysis_score += 0.166
        scores["critical_thinking"] = min(1.0, analysis_score)
        
        return scores
    
    def _evaluate_research_function(self,
                                   response_text: str,
                                   expected_elements: List[str],
                                   success_criteria: List[str]) -> Dict[str, float]:
        """Evaluate research function"""
        scores = {}
        
        # 1. Information freshness indicators
        freshness_words = ["recent", "latest", "new", "2024", "update", "current"]
        freshness_score = 0
        for word in freshness_words:
            if word in response_text:
                freshness_score += 0.166
        scores["freshness"] = min(1.0, freshness_score)
        
        # 2. Source credibility
        source_words = ["case", "study", "client", "success", "implementation", "results"]
        source_score = 0
        for word in source_words:
            if word in response_text:
                source_score += 0.166
        scores["source_credibility"] = min(1.0, source_score)
        
        # 3. Detail level
        detail_indicators = ["details", "specific", "example", "instance", "including"]
        detail_score = 0
        for indicator in detail_indicators:
            if indicator in response_text:
                detail_score += 0.2
        scores["detail_level"] = min(1.0, detail_score)
        
        return scores
    
    def _evaluate_reporting_function(self,
                                    response_text: str,
                                    expected_elements: List[str],
                                    success_criteria: List[str]) -> Dict[str, float]:
        """Evaluate reporting function"""
        scores = {}
        
        # 1. Structure and organization
        structure_indicators = ["##", "###", "1.", "2.", "3.", "- ", "* ", "\n\n"]
        structure_score = 0
        for indicator in structure_indicators:
            if indicator in response_text:
                structure_score += 0.143  # 7 indicators max
        scores["structure"] = min(1.0, structure_score)
        
        # 2. Business focus
        business_words = ["business", "roi", "value", "benefit", "impact", "advantage"]
        business_score = 0
        for word in business_words:
            if word in response_text:
                business_score += 0.166
        scores["business_focus"] = min(1.0, business_score)
        
        # 3. Completeness
        completeness_elements = ["executive", "summary", "solution", "recommendation", "next"]
        completeness_score = 0
        for element in completeness_elements:
            if element in response_text:
                completeness_score += 0.2
        scores["completeness"] = min(1.0, completeness_score)
        
        return scores
    
    def _get_function_weights(self, function: str) -> Dict[str, float]:
        """Get evaluation weights for different functions"""
        weights = {
            "matching": {
                "solution_coverage": 0.4,
                "relevance": 0.3,
                "actionability": 0.2,
                "specificity": 0.1
            },
            "gap_analysis": {
                "gap_identification": 0.4,
                "recommendation_quality": 0.3,
                "critical_thinking": 0.3
            },
            "research": {
                "freshness": 0.4,
                "source_credibility": 0.4,
                "detail_level": 0.2
            },
            "reporting": {
                "structure": 0.3,
                "business_focus": 0.4,
                "completeness": 0.3
            }
        }
        return weights.get(function, {"overall": 1.0})
    
    def _summarize_response(self, response: Dict, max_length: int = 150) -> str:
        """Create a short summary of the response"""
        try:
            response_str = json.dumps(response)
            if len(response_str) > max_length:
                return response_str[:max_length] + "..."
            return response_str
        except:
            return str(response)[:max_length]
    
    def _analyze_agent_results(self, results: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze all agent test results"""
        
        # Calculate function-specific metrics
        function_analysis = {}
        overall_scores = []
        
        for function, function_results in results.items():
            if not function_results:
                function_analysis[function] = {
                    "count": 0,
                    "avg_score": 0,
                    "success_rate": 0,
                    "avg_latency": 0
                }
                continue
            
            # Calculate metrics
            scores = [r.get("scores", {}).get("overall", 0) for r in function_results]
            latencies = [r.get("latency", 0) for r in function_results if "latency" in r]
            success_count = sum(1 for r in function_results if r.get("scores", {}).get("overall", 0) > 0.5)
            
            function_analysis[function] = {
                "count": len(function_results),
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "success_rate": success_count / len(function_results) if function_results else 0,
                "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0
            }
            
            overall_scores.extend(scores)
        
        # Calculate overall metrics
        overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        # Identify strongest and weakest functions
        function_scores = {
            func: analysis["avg_score"] 
            for func, analysis in function_analysis.items()
        }
        
        strongest_function = max(function_scores.items(), key=lambda x: x[1]) if function_scores else ("none", 0)
        weakest_function = min(function_scores.items(), key=lambda x: x[1]) if function_scores else ("none", 0)
        
        # Generate recommendations
        recommendations = self._generate_agent_recommendations(function_analysis)
        
        return {
            "summary": {
                "total_scenarios_tested": sum(analysis["count"] for analysis in function_analysis.values()),
                "overall_score": overall_score,
                "strongest_function": {
                    "function": strongest_function[0],
                    "score": strongest_function[1]
                },
                "weakest_function": {
                    "function": weakest_function[0],
                    "score": weakest_function[1]
                },
                "timestamp": datetime.now().isoformat()
            },
            "function_analysis": function_analysis,
            "performance_breakdown": {
                "by_complexity": self._analyze_by_complexity(results),
                "score_distribution": overall_scores
            },
            "recommendations": recommendations,
            "sample_results": self._get_sample_results(results)
        }
    
    def _analyze_by_complexity(self, results: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze results by scenario complexity"""
        complexity_scores = {"low": [], "medium": [], "high": []}
        
        for function_results in results.values():
            for result in function_results:
                complexity = result.get("complexity", "medium")
                score = result.get("scores", {}).get("overall", 0)
                
                if complexity in complexity_scores:
                    complexity_scores[complexity].append(score)
        
        analysis = {}
        for complexity, scores in complexity_scores.items():
            if scores:
                analysis[complexity] = {
                    "count": len(scores),
                    "avg_score": sum(scores) / len(scores),
                    "success_rate": sum(1 for s in scores if s > 0.5) / len(scores)
                }
            else:
                analysis[complexity] = {"count": 0, "avg_score": 0, "success_rate": 0}
        
        return analysis
    
    def _get_sample_results(self, results: Dict[str, List[Dict]], max_per_function: int = 2) -> Dict[str, List]:
        """Get sample results for each function"""
        samples = {}
        
        for function, function_results in results.items():
            if function_results:
                # Get best and worst from this function
                sorted_results = sorted(
                    function_results,
                    key=lambda x: x.get("scores", {}).get("overall", 0),
                    reverse=True
                )
                
                samples[function] = [
                    {
                        "scenario_id": r["scenario_id"],
                        "score": r.get("scores", {}).get("overall", 0),
                        "scenario_summary": r.get("scenario", "")[:100] + "...",
                        "response_preview": r.get("response_summary", "")[:100] + "..."
                    }
                    for r in sorted_results[:max_per_function]
                ]
        
        return samples
    
    def _generate_agent_recommendations(self, function_analysis: Dict) -> List[str]:
        """Generate recommendations based on agent performance"""
        recommendations = []
        
        # Identify functions needing improvement
        for function, analysis in function_analysis.items():
            score = analysis["avg_score"]
            count = analysis["count"]
            
            if count > 0:
                if score < 0.6:
                    recommendations.append(f"Improve {function} function (score: {score:.2f})")
                elif score > 0.8:
                    recommendations.append(f"Strong performance in {function} (score: {score:.2f})")
        
        # Overall recommendations
        overall_score = function_analysis.get("overall", {}).get("avg_score", 0)
        if overall_score < 0.7:
            recommendations.append("Overall agent performance needs improvement")
        elif overall_score > 0.85:
            recommendations.append("Excellent overall agent performance")
        
        # Latency recommendations
        for function, analysis in function_analysis.items():
            latency = analysis.get("avg_latency", 0)
            if latency > 5.0:
                recommendations.append(f"Optimize {function} latency (current: {latency:.1f}s)")
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    def _save_results(self, analysis: Dict):
        """Save test results to file"""
        try:
            results_dir = settings.RESULTS_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"agent_test_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"Agent test results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save agent results: {e}")