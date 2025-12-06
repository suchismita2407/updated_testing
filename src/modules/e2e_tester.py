import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from tqdm import tqdm

from src.api_client import APIClient, TestDataGenerator
from config.settings import settings

logger = logging.getLogger(__name__)

class EndToEndTester:
    """
    Test the complete Sales EVA system end-to-end
    
    Tests:
    1. Complete opportunity analysis workflow
    2. Business impact and sales readiness
    3. Real-world scenario validation
    4. System integration and reliability
    """
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.test_generator = TestDataGenerator()
        self.results = []
        
    async def run_tests(self, test_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Run comprehensive end-to-end tests
        
        Steps:
        1. Generate realistic sales scenarios using LLM
        2. Execute full analysis for each scenario
        3. Evaluate business impact and readiness
        4. Analyze system reliability and performance
        """
        logger.info("Starting end-to-end testing...")
        
        test_count = test_count or settings.E2E_TEST_COUNT
        
        # Generate realistic test scenarios using LLM
        logger.info(f"Generating {test_count} end-to-end test scenarios using LLM...")
        test_scenarios = self._generate_e2e_scenarios(test_count)
        
        if not test_scenarios:
            raise ValueError("Failed to generate test scenarios")
        
        logger.info(f"Running {len(test_scenarios)} end-to-end scenarios...")
        
        # Run E2E tests
        test_results = await self._run_e2e_tests_parallel(test_scenarios)
        
        # Analyze results
        analysis = self._analyze_e2e_results(test_results)
        
        # Save results
        self._save_results(analysis)
        
        logger.info(f"E2E testing completed. Overall score: {analysis.get('overall_score', 0):.2f}")
        
        return analysis
    
    def _generate_e2e_scenarios(self, count: int) -> List[Dict]:
        """Generate realistic end-to-end test scenarios using LLM"""
        prompt = f"""Generate {count} realistic end-to-end test scenarios for a Sales Virtual Assistant.
        
        Each scenario should simulate a complete sales opportunity with:
        1. Company background and industry context
        2. Detailed business requirements and challenges
        3. Budget constraints and timeline
        4. Specific technical and business needs
        5. Success criteria for the engagement
        
        Return ONLY a JSON array with this structure:
        {{
            "id": "E2E_TEST_001",
            "title": "Descriptive title",
            "scenario": "Detailed multi-paragraph scenario description",
            "company": "Company name and background",
            "industry": "Industry sector",
            "budget": "Budget range",
            "timeline": "Project timeline",
            "key_requirements": ["req1", "req2", "req3", "req4", "req5"],
            "success_criteria": [
                "Should match with relevant TCS offerings",
                "Should identify implementation approach",
                "Should provide ROI justification",
                "Should include case study references",
                "Should propose next steps"
            ],
            "complexity": "low/medium/high",
            "priority": "low/medium/high/critical"
        }}
        
        Make scenarios diverse across industries and complexity levels."""
        
        try:
            response = self.test_generator._call_groq_api(prompt)
            
            # Parse JSON response
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            scenarios = json.loads(response.strip())
            
            # Validate and clean scenarios
            validated_scenarios = []
            industry_counts = {}
            complexity_counts = {"low": 0, "medium": 0, "high": 0}
            
            for i, scenario in enumerate(scenarios[:count]):
                if not isinstance(scenario, dict):
                    continue
                
                # Clean and validate fields
                validated = {
                    "id": scenario.get("id", f"E2E_TEST_{i+1:03d}"),
                    "title": str(scenario.get("title", "")).strip(),
                    "scenario": str(scenario.get("scenario", "")).strip(),
                    "company": str(scenario.get("company", "")).strip(),
                    "industry": str(scenario.get("industry", "")).strip(),
                    "budget": str(scenario.get("budget", "")).strip(),
                    "timeline": str(scenario.get("timeline", "")).strip(),
                    "key_requirements": [
                        str(req).strip()
                        for req in scenario.get("key_requirements", [])
                        if req and len(str(req).strip()) > 3
                    ],
                    "success_criteria": [
                        str(crit).strip()
                        for crit in scenario.get("success_criteria", [])
                        if crit
                    ],
                    "complexity": str(scenario.get("complexity", "medium")).lower(),
                    "priority": str(scenario.get("priority", "medium")).lower()
                }
                
                # Only add if we have substantial content
                if validated["scenario"] and len(validated["scenario"]) > 100:
                    # Track distributions
                    industry = validated["industry"]
                    industry_counts[industry] = industry_counts.get(industry, 0) + 1
                    
                    complexity = validated["complexity"]
                    if complexity in complexity_counts:
                        complexity_counts[complexity] += 1
                    
                    validated_scenarios.append(validated)
            
            logger.info(f"Generated scenarios - Industries: {industry_counts}, Complexities: {complexity_counts}")
            return validated_scenarios
            
        except Exception as e:
            logger.error(f"Failed to generate E2E scenarios: {e}")
            return self._generate_fallback_scenarios(count)
    
    def _generate_fallback_scenarios(self, count: int) -> List[Dict]:
        """Generate fallback E2E scenarios"""
        scenarios = []
        
        # Template scenarios for different industries
        templates = [
            {
                "title": "Global Bank Digital Transformation",
                "company": "Major European banking institution with operations in 30+ countries",
                "industry": "Banking & Finance",
                "budget": "$50-75M",
                "timeline": "18-24 months",
                "key_requirements": [
                    "Cloud migration of legacy systems",
                    "AI-powered fraud detection",
                    "Customer experience modernization",
                    "Regulatory compliance automation",
                    "Data analytics platform"
                ]
            },
            {
                "title": "Retail Chain AI Optimization",
                "company": "National retail chain with 500+ stores",
                "industry": "Retail",
                "budget": "$10-15M",
                "timeline": "12 months",
                "key_requirements": [
                    "Inventory optimization using AI",
                    "Customer personalization engine",
                    "Supply chain automation",
                    "Mobile app enhancement",
                    "In-store IoT implementation"
                ]
            },
            {
                "title": "Healthcare Data Modernization",
                "company": "Hospital network with 20+ facilities",
                "industry": "Healthcare",
                "budget": "$25-35M",
                "timeline": "24 months",
                "key_requirements": [
                    "Patient data platform",
                    "HIPAA compliance automation",
                    "Telemedicine integration",
                    "Predictive analytics for patient care",
                    "Interoperability with existing systems"
                ]
            },
            {
                "title": "Manufacturing Smart Factory",
                "company": "Automotive parts manufacturer",
                "industry": "Manufacturing",
                "budget": "$30-40M",
                "timeline": "18 months",
                "key_requirements": [
                    "IoT sensor implementation",
                    "Predictive maintenance system",
                    "Supply chain optimization",
                    "Quality control automation",
                    "Energy consumption optimization"
                ]
            }
        ]
        
        # Create scenarios from templates
        for i in range(count):
            template = templates[i % len(templates)]
            scenarios.append({
                "id": f"E2E_FB_{i+1:03d}",
                "title": f"{template['title']} - Scenario {i+1}",
                "scenario": f"{template['company']} seeks digital transformation. Key requirements include: {', '.join(template['key_requirements'][:3])}. Budget: {template['budget']}. Timeline: {template['timeline']}.",
                "company": template["company"],
                "industry": template["industry"],
                "budget": template["budget"],
                "timeline": template["timeline"],
                "key_requirements": template["key_requirements"],
                "success_criteria": [
                    "Match with relevant offerings",
                    "Provide implementation approach",
                    "Include ROI analysis",
                    "Reference case studies",
                    "Propose next steps"
                ],
                "complexity": "high" if i % 3 == 0 else "medium" if i % 3 == 1 else "low",
                "priority": "critical" if i % 4 == 0 else "high" if i % 4 == 1 else "medium"
            })
        
        return scenarios[:count]
    
    async def _run_e2e_tests_parallel(self, scenarios: List[Dict]) -> List[Dict]:
        """Run E2E tests in parallel"""
        results = []
        
        # Create tasks for each scenario
        tasks = []
        for scenario in scenarios:
            tasks.append(self._execute_e2e_scenario(scenario))
        
        # Execute with progress bar
        with tqdm(total=len(tasks), desc="Running E2E tests") as pbar:
            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    logger.warning(f"E2E test failed: {e}")
                    # Create error result
                    results.append({
                        "scenario_id": "unknown",
                        "error": str(e),
                        "scores": {"overall": 0, "error": 1.0},
                        "timestamp": datetime.now().isoformat()
                    })
                finally:
                    pbar.update(1)
        
        return results
    
    async def _execute_e2e_scenario(self, scenario: Dict) -> Dict[str, Any]:
        """Execute a single E2E scenario"""
        scenario_id = scenario["id"]
        title = scenario["title"]
        scenario_text = scenario["scenario"]
        
        try:
            # Prepare the full query
            query = self._prepare_e2e_query(scenario)
            
            # Execute with timing
            start_time = datetime.now()
            
            response = await self.api_client.analyze_opportunity(
                opportunity_description=query
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            
            # Comprehensive evaluation
            evaluation = self._evaluate_e2e_response(
                response=response,
                scenario=scenario,
                latency=latency
            )
            
            # Calculate business impact score
            business_impact = self._calculate_business_impact(
                evaluation, 
                scenario
            )
            
            # Generate improvement suggestions
            suggestions = self._generate_improvement_suggestions(
                evaluation, 
                scenario
            )
            
            return {
                "scenario_id": scenario_id,
                "title": title,
                "industry": scenario["industry"],
                "complexity": scenario["complexity"],
                "priority": scenario["priority"],
                "latency": latency,
                "scores": evaluation,
                "business_impact": business_impact,
                "response_summary": self._summarize_response(response),
                "improvement_suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"E2E scenario {scenario_id} failed: {e}")
            return {
                "scenario_id": scenario_id,
                "title": title,
                "error": str(e),
                "scores": {"overall": 0, "error": 1.0},
                "business_impact": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_e2e_query(self, scenario: Dict) -> str:
        """Prepare comprehensive query for E2E scenario"""
        query_parts = [
            f"Scenario: {scenario['title']}",
            f"Company: {scenario['company']}",
            f"Industry: {scenario['industry']}",
            f"Budget: {scenario['budget']}",
            f"Timeline: {scenario['timeline']}",
            f"Requirements: {', '.join(scenario['key_requirements'][:5])}",
            scenario["scenario"]
        ]
        
        return "\n\n".join(filter(None, query_parts))
    
    def _evaluate_e2e_response(self, 
                              response: Dict, 
                              scenario: Dict,
                              latency: float) -> Dict[str, float]:
        """Comprehensive evaluation of E2E response"""
        scores = {"overall": 0.0}
        
        try:
            response_text = json.dumps(response).lower()
            scenario_text = scenario["scenario"].lower()
            
            # 1. Requirement Coverage
            requirement_coverage = self._evaluate_requirement_coverage(
                response_text, scenario["key_requirements"]
            )
            scores["requirement_coverage"] = requirement_coverage
            
            # 2. Solution Matching
            solution_matching = self._evaluate_solution_matching(
                response_text, scenario
            )
            scores["solution_matching"] = solution_matching
            
            # 3. Business Relevance
            business_relevance = self._evaluate_business_relevance(
                response_text, scenario
            )
            scores["business_relevance"] = business_relevance
            
            # 4. Actionability
            actionability = self._evaluate_actionability(response_text)
            scores["actionability"] = actionability
            
            # 5. Completeness
            completeness = self._evaluate_completeness(
                response_text, scenario["success_criteria"]
            )
            scores["completeness"] = completeness
            
            # 6. Structure and Clarity
            structure = self._evaluate_structure(response_text)
            scores["structure"] = structure
            
            # 7. Performance (latency-based)
            performance = self._evaluate_performance(latency)
            scores["performance"] = performance
            
            # Calculate overall weighted score
            weights = {
                "requirement_coverage": 0.25,
                "solution_matching": 0.20,
                "business_relevance": 0.15,
                "actionability": 0.15,
                "completeness": 0.10,
                "structure": 0.10,
                "performance": 0.05
            }
            
            overall = sum(
                scores.get(metric, 0) * weight
                for metric, weight in weights.items()
                if metric in scores
            )
            scores["overall"] = min(1.0, overall)
            
        except Exception as e:
            logger.warning(f"E2E evaluation failed: {e}")
            scores = {"error": 1.0, "overall": 0.0}
        
        return scores
    
    def _evaluate_requirement_coverage(self, 
                                      response_text: str, 
                                      requirements: List[str]) -> float:
        """Evaluate coverage of key requirements"""
        coverage_score = 0
        checked_requirements = 0
        
        for requirement in requirements[:10]:  # Check first 10 requirements
            if len(requirement) > 3:  # Ignore very short requirements
                req_lower = requirement.lower()
                # Check for requirement or its key terms
                req_terms = req_lower.split()
                term_matches = sum(
                    1 for term in req_terms[:5] 
                    if len(term) > 3 and term in response_text
                )
                
                if term_matches >= min(2, len(req_terms)):  # At least 2 matching terms
                    coverage_score += 0.1
                checked_requirements += 1
        
        if checked_requirements > 0:
            return min(1.0, coverage_score / (checked_requirements * 0.1))
        return 0.0
    
    def _evaluate_solution_matching(self, response_text: str, scenario: Dict) -> float:
        """Evaluate matching with appropriate solutions"""
        score = 0
        
        # Check for solution indicators
        solution_indicators = [
            "solution", "offering", "service", "product", "capability",
            "framework", "platform", "tool", "technology", "approach"
        ]
        
        for indicator in solution_indicators:
            if indicator in response_text:
                score += 0.1
        
        # Check for industry-specific solutions
        industry = scenario["industry"].lower()
        industry_indicators = {
            "banking": ["bank", "financial", "transaction", "compliance", "fraud"],
            "retail": ["retail", "inventory", "customer", "store", "ecommerce"],
            "healthcare": ["health", "patient", "medical", "hospital", "clinical"],
            "manufacturing": ["manufactur", "factory", "production", "supply", "quality"]
        }
        
        for ind_key, indicators in industry_indicators.items():
            if ind_key in industry:
                for indicator in indicators:
                    if indicator in response_text:
                        score += 0.05
        
        return min(1.0, score)
    
    def _evaluate_business_relevance(self, response_text: str, scenario: Dict) -> float:
        """Evaluate business relevance"""
        score = 0
        
        # Business value indicators
        business_indicators = [
            "roi", "return on investment", "value", "benefit", "impact",
            "savings", "efficiency", "productivity", "revenue", "growth",
            "competitive", "advantage", "differentiator", "strategic"
        ]
        
        for indicator in business_indicators:
            if indicator in response_text:
                score += 0.066  # 15 indicators max
        
        # Budget and timeline relevance
        budget = scenario["budget"].lower()
        timeline = scenario["timeline"].lower()
        
        # Check if response acknowledges constraints
        constraint_indicators = ["budget", "cost", "investment", "timeline", "schedule", "time"]
        for indicator in constraint_indicators:
            if indicator in response_text:
                score += 0.05
        
        return min(1.0, score)
    
    def _evaluate_actionability(self, response_text: str) -> float:
        """Evaluate actionability of recommendations"""
        score = 0
        
        # Action-oriented indicators
        action_indicators = [
            "recommend", "suggest", "propose", "should", "could", "would",
            "next steps", "action plan", "implementation", "deployment",
            "roadmap", "timeline", "milestone", "deliverable", "phase"
        ]
        
        for indicator in action_indicators:
            if indicator in response_text:
                score += 0.066  # 15 indicators max
        
        return min(1.0, score)
    
    def _evaluate_completeness(self, response_text: str, success_criteria: List[str]) -> float:
        """Evaluate completeness against success criteria"""
        score = 0
        
        for criterion in success_criteria[:5]:  # Check first 5 criteria
            crit_lower = criterion.lower()
            # Check for criterion keywords
            crit_terms = crit_lower.split()
            term_matches = sum(
                1 for term in crit_terms[:3]
                if len(term) > 3 and term in response_text
            )
            
            if term_matches >= min(1, len(crit_terms)):
                score += 0.2
        
        return min(1.0, score)
    
    def _evaluate_structure(self, response_text: str) -> float:
        """Evaluate structure and clarity"""
        score = 0.3  # Base score
        
        # Structure indicators
        structure_indicators = [
            "##", "###",  # Markdown headers
            "1.", "2.", "3.", "4.", "5.",  # Numbered lists
            "- ", "* ",  # Bullet points
            "\n\n",  # Paragraph breaks
            "introduction", "summary", "conclusion", "recommendation"
        ]
        
        for indicator in structure_indicators:
            if indicator in response_text:
                score += 0.1
        
        return min(1.0, score)
    
    def _evaluate_performance(self, latency: float) -> float:
        """Evaluate performance based on latency"""
        if latency < 2.0:
            return 1.0
        elif latency < 5.0:
            return 0.8
        elif latency < 10.0:
            return 0.6
        elif latency < 20.0:
            return 0.4
        elif latency < 30.0:
            return 0.2
        else:
            return 0.1
    
    def _calculate_business_impact(self, evaluation: Dict, scenario: Dict) -> Dict[str, Any]:
        """Calculate business impact score"""
        # Base impact calculation
        base_score = evaluation.get("overall", 0)
        
        # Weight by scenario priority
        priority_weights = {
            "critical": 1.2,
            "high": 1.1,
            "medium": 1.0,
            "low": 0.9
        }
        
        priority = scenario.get("priority", "medium")
        priority_weight = priority_weights.get(priority, 1.0)
        
        # Weight by complexity
        complexity_weights = {
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }
        
        complexity = scenario.get("complexity", "medium")
        complexity_weight = complexity_weights.get(complexity, 1.0)
        
        # Calculate final impact score
        impact_score = base_score * priority_weight * complexity_weight
        
        # Determine impact level
        if impact_score >= 0.8:
            impact_level = "High"
            impact_description = "Significant positive business impact"
        elif impact_score >= 0.6:
            impact_level = "Medium"
            impact_description = "Moderate business impact"
        elif impact_score >= 0.4:
            impact_level = "Low"
            impact_description = "Limited business impact"
        else:
            impact_level = "Minimal"
            impact_description = "Insufficient for business needs"
        
        return {
            "score": impact_score,
            "level": impact_level,
            "description": impact_description,
            "priority_multiplier": priority_weight,
            "complexity_multiplier": complexity_weight
        }
    
    def _generate_improvement_suggestions(self, evaluation: Dict, scenario: Dict) -> List[str]:
        """Generate improvement suggestions based on evaluation"""
        suggestions = []
        
        scores = evaluation
        
        # Check each metric and suggest improvements
        if scores.get("requirement_coverage", 0) < 0.7:
            suggestions.append("Improve coverage of client requirements")
        
        if scores.get("solution_matching", 0) < 0.7:
            suggestions.append("Provide more specific solution matching")
        
        if scores.get("business_relevance", 0) < 0.6:
            suggestions.append("Increase focus on business value and ROI")
        
        if scores.get("actionability", 0) < 0.6:
            suggestions.append("Make recommendations more actionable with clear next steps")
        
        if scores.get("completeness", 0) < 0.7:
            suggestions.append("Address more success criteria from the scenario")
        
        if scores.get("structure", 0) < 0.6:
            suggestions.append("Improve response structure with clear sections")
        
        if scores.get("performance", 0) < 0.5:
            suggestions.append("Optimize response time for better performance")
        
        # Overall suggestion based on score
        overall = scores.get("overall", 0)
        if overall < 0.6:
            suggestions.append("Overall response quality needs significant improvement")
        elif overall < 0.8:
            suggestions.append("Good response, but can be improved for higher impact")
        
        # Limit suggestions
        return suggestions[:5]
    
    def _summarize_response(self, response: Dict, max_length: int = 150) -> str:
        """Create a short summary of the response"""
        try:
            response_str = json.dumps(response)
            if len(response_str) > max_length:
                return response_str[:max_length] + "..."
            return response_str
        except:
            return str(response)[:max_length]
    
    def _analyze_e2e_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze all E2E test results"""
        
        # Filter out error results
        valid_results = [r for r in results if "error" not in r]
        error_results = [r for r in results if "error" in r]
        
        if not valid_results:
            return {
                "summary": {
                    "total_tests": len(results),
                    "valid_tests": 0,
                    "error_tests": len(error_results),
                    "overall_score": 0,
                    "business_impact_score": 0,
                    "timestamp": datetime.now().isoformat()
                },
                "errors": error_results[:5]
            }
        
        # Calculate overall metrics
        overall_scores = [r.get("scores", {}).get("overall", 0) for r in valid_results]
        business_impact_scores = [r.get("business_impact", {}).get("score", 0) for r in valid_results]
        latencies = [r.get("latency", 0) for r in valid_results]
        
        overall_score = sum(overall_scores) / len(overall_scores)
        business_impact_score = sum(business_impact_scores) / len(business_impact_scores)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Analyze by industry
        industry_analysis = {}
        for result in valid_results:
            industry = result.get("industry", "Unknown")
            if industry not in industry_analysis:
                industry_analysis[industry] = []
            industry_analysis[industry].append(result.get("scores", {}).get("overall", 0))
        
        industry_stats = {}
        for industry, scores in industry_analysis.items():
            if scores:
                industry_stats[industry] = {
                    "count": len(scores),
                    "avg_score": sum(scores) / len(scores),
                    "max_score": max(scores),
                    "min_score": min(scores)
                }
        
        # Analyze by complexity
        complexity_analysis = {"low": [], "medium": [], "high": []}
        for result in valid_results:
            complexity = result.get("complexity", "medium")
            if complexity in complexity_analysis:
                complexity_analysis[complexity].append(result.get("scores", {}).get("overall", 0))
        
        complexity_stats = {}
        for complexity, scores in complexity_analysis.items():
            if scores:
                complexity_stats[complexity] = {
                    "count": len(scores),
                    "avg_score": sum(scores) / len(scores),
                    "success_rate": sum(1 for s in scores if s > 0.6) / len(scores)
                }
        
        # Analyze by metric
        metric_analysis = {}
        metrics = ["requirement_coverage", "solution_matching", "business_relevance", 
                  "actionability", "completeness", "structure", "performance"]
        
        for metric in metrics:
            metric_scores = []
            for result in valid_results:
                score = result.get("scores", {}).get(metric, 0)
                if score > 0:  # Only include if metric was evaluated
                    metric_scores.append(score)
            
            if metric_scores:
                metric_analysis[metric] = {
                    "avg_score": sum(metric_scores) / len(metric_scores),
                    "max_score": max(metric_scores),
                    "min_score": min(metric_scores)
                }
        
        # Identify best and worst scenarios
        best_scenarios = sorted(
            valid_results,
            key=lambda x: x.get("scores", {}).get("overall", 0),
            reverse=True
        )[:3]
        
        worst_scenarios = sorted(
            valid_results,
            key=lambda x: x.get("scores", {}).get("overall", 0)
        )[:3]
        
        # Generate overall recommendations
        recommendations = self._generate_overall_recommendations(
            overall_score, 
            metric_analysis,
            complexity_stats
        )
        
        # Calculate success rate
        success_count = sum(1 for r in valid_results if r.get("scores", {}).get("overall", 0) > 0.7)
        success_rate = success_count / len(valid_results) if valid_results else 0
        
        return {
            "summary": {
                "total_tests": len(results),
                "valid_tests": len(valid_results),
                "error_tests": len(error_results),
                "overall_score": overall_score,
                "business_impact_score": business_impact_score,
                "avg_latency": avg_latency,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "industry_analysis": industry_stats,
            "complexity_analysis": complexity_stats,
            "metric_analysis": metric_analysis,
            "performance_insights": {
                "best_scenarios": [
                    {
                        "title": s.get("title", "Unknown"),
                        "industry": s.get("industry", "Unknown"),
                        "score": s.get("scores", {}).get("overall", 0),
                        "business_impact": s.get("business_impact", {}).get("level", "Unknown")
                    }
                    for s in best_scenarios
                ],
                "worst_scenarios": [
                    {
                        "title": s.get("title", "Unknown"),
                        "industry": s.get("industry", "Unknown"),
                        "score": s.get("scores", {}).get("overall", 0),
                        "primary_issue": self._identify_primary_issue(s)
                    }
                    for s in worst_scenarios
                ]
            },
            "recommendations": recommendations,
            "sample_results": self._get_sample_results(valid_results),
            "errors": error_results[:3] if error_results else None
        }
    
    def _identify_primary_issue(self, result: Dict) -> str:
        """Identify primary issue in a result"""
        scores = result.get("scores", {})
        
        if scores.get("overall", 0) < 0.5:
            # Find lowest scoring metric
            metrics = ["requirement_coverage", "solution_matching", "business_relevance",
                      "actionability", "completeness", "structure", "performance"]
            
            min_metric = min(
                [(metric, scores.get(metric, 0)) for metric in metrics],
                key=lambda x: x[1]
            )
            
            issue_map = {
                "requirement_coverage": "Insufficient requirement coverage",
                "solution_matching": "Poor solution matching",
                "business_relevance": "Lacks business relevance",
                "actionability": "Not actionable enough",
                "completeness": "Incomplete response",
                "structure": "Poor structure and clarity",
                "performance": "Performance issues"
            }
            
            return issue_map.get(min_metric[0], "Multiple issues")
        
        return "No major issues identified"
    
    def _get_sample_results(self, results: List[Dict], count: int = 3) -> List[Dict]:
        """Get sample results for display"""
        if not results:
            return []
        
        # Get a mix of good, average, and poor results
        sorted_results = sorted(
            results,
            key=lambda x: x.get("scores", {}).get("overall", 0)
        )
        
        samples = []
        if len(sorted_results) >= 3:
            samples.extend([
                sorted_results[0],  # Worst
                sorted_results[len(sorted_results)//2],  # Middle
                sorted_results[-1]  # Best
            ])
        else:
            samples = sorted_results
        
        # Simplify for display
        simplified = []
        for result in samples[:count]:
            simplified.append({
                "title": result.get("title", "Unknown"),
                "industry": result.get("industry", "Unknown"),
                "score": result.get("scores", {}).get("overall", 0),
                "business_impact": result.get("business_impact", {}).get("level", "Unknown"),
                "latency": result.get("latency", 0),
                "key_strength": self._identify_key_strength(result),
                "key_weakness": self._identify_key_weakness(result)
            })
        
        return simplified
    
    def _identify_key_strength(self, result: Dict) -> str:
        """Identify key strength in a result"""
        scores = result.get("scores", {})
        
        if scores.get("overall", 0) > 0.7:
            # Find highest scoring metric
            metrics = ["requirement_coverage", "solution_matching", "business_relevance",
                      "actionability", "completeness", "structure", "performance"]
            
            max_metric = max(
                [(metric, scores.get(metric, 0)) for metric in metrics],
                key=lambda x: x[1]
            )
            
            strength_map = {
                "requirement_coverage": "Excellent requirement coverage",
                "solution_matching": "Strong solution matching",
                "business_relevance": "High business relevance",
                "actionability": "Very actionable",
                "completeness": "Comprehensive response",
                "structure": "Well-structured",
                "performance": "Excellent performance"
            }
            
            return strength_map.get(max_metric[0], "Good overall performance")
        
        return "No major strengths identified"
    
    def _identify_key_weakness(self, result: Dict) -> str:
        """Identify key weakness in a result"""
        scores = result.get("scores", {})
        
        if scores.get("overall", 0) < 0.8:
            # Find lowest scoring metric
            metrics = ["requirement_coverage", "solution_matching", "business_relevance",
                      "actionability", "completeness", "structure", "performance"]
            
            min_metric = min(
                [(metric, scores.get(metric, 0)) for metric in metrics],
                key=lambda x: x[1]
            )
            
            weakness_map = {
                "requirement_coverage": "Weak requirement coverage",
                "solution_matching": "Poor solution matching",
                "business_relevance": "Low business relevance",
                "actionability": "Not actionable enough",
                "completeness": "Incomplete response",
                "structure": "Poor structure",
                "performance": "Performance issues"
            }
            
            return weakness_map.get(min_metric[0], "Room for improvement")
        
        return "No major weaknesses"
    
    def _generate_overall_recommendations(self,
                                         overall_score: float,
                                         metric_analysis: Dict,
                                         complexity_stats: Dict) -> List[str]:
        """Generate overall system recommendations"""
        recommendations = []
        
        # Overall score recommendations
        if overall_score < 0.6:
            recommendations.append("System needs significant improvement in core capabilities")
        elif overall_score < 0.8:
            recommendations.append("System performs adequately but can be enhanced")
        else:
            recommendations.append("System performs well - focus on maintenance and optimization")
        
        # Metric-specific recommendations
        for metric, analysis in metric_analysis.items():
            avg_score = analysis.get("avg_score", 0)
            
            if avg_score < 0.6:
                metric_name = metric.replace("_", " ").title()
                recommendations.append(f"Improve {metric_name} (current: {avg_score:.2f})")
        
        # Complexity-based recommendations
        for complexity, stats in complexity_stats.items():
            success_rate = stats.get("success_rate", 0)
            if success_rate < 0.5:
                recommendations.append(f"Improve handling of {complexity} complexity scenarios")
        
        # Performance recommendations
        if metric_analysis.get("performance", {}).get("avg_score", 0) < 0.7:
            recommendations.append("Optimize system performance and response times")
        
        # Limit to top 5 recommendations
        return recommendations[:5]
    
    def _save_results(self, analysis: Dict):
        """Save E2E test results to file"""
        try:
            results_dir = settings.RESULTS_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"e2e_test_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"E2E test results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save E2E results: {e}")