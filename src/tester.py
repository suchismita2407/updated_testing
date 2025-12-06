import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.api_client import APIClient
from src.sales_eva_client import SalesEVAServiceClient  # Add this import
from src.metrics_collector import MetricsCollector  
from src.modules.prompt_tester import PromptTester
from src.modules.agent_tester import AgentTester
from src.modules.kb_validator import KnowledgeBaseValidator
from src.modules.e2e_tester import EndToEndTester
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

class SalesEVATester:
    """
    Main testing orchestrator for Sales EVA system
    
    Orchestrates all testing modules:
    1. Prompt Testing & Optimization
    2. Agent Capability Testing
    3. Knowledge Base Validation
    4. End-to-End System Testing
    """
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the testing framework
        
        Args:
            api_url: URL of the Sales EVA API (optional, uses settings if not provided)
        """
        self.api_url = api_url or settings.SALES_EVA_API_URL
        
        self.metrics = MetricsCollector()
        # Initialize API client - Use the new specialized client
        try:
            from src.sales_eva_client import SalesEVAServiceClient
            self.api_client = SalesEVAServiceClient(base_url=self.api_url)
        except ImportError:
            # Fall back to original client
            from src.api_client import APIClient
            self.api_client = APIClient(base_url=self.api_url)
        
        # Initialize testing modules
        self.prompt_tester = PromptTester(self.api_client, self.metrics)
        self.agent_tester = AgentTester(self.api_client, self.metrics)
        self.kb_validator = KnowledgeBaseValidator(self.api_client, self.metrics)
        self.e2e_tester = EndToEndTester(self.api_client, self.metrics)
        
        self.results = {}
        self.test_history = []
        
        logger.info(f"Sales EVA Tester initialized for API: {self.api_url}")

    async def run_all_tests(self, 
                           test_types: Optional[List[str]] = None,
                           save_results: bool = True) -> Dict[str, Any]:
        
        test_start_timer = self.metrics.start_test(
            test_id="full_test_suite",
            test_type="comprehensive",
            test_name="Full Test Suite Execution"
        )
        """
        Run comprehensive testing suite
        
        Args:
            test_types: List of test types to run. If None, runs all tests.
                       Options: ['prompt', 'agent', 'kb', 'e2e']
            save_results: Whether to save results to file
        
        Returns:
            Comprehensive test results
        """
        if test_types is None:
            test_types = ['prompt', 'agent', 'kb', 'e2e']
        
        logger.info(f"Starting comprehensive testing: {test_types}")
        
        # Health check
        if not await self._health_check():
            raise ConnectionError(f"Cannot connect to Sales EVA API at {self.api_url}")
        
        test_start_time = datetime.now()
        
        # Run selected tests
        results = {}
        errors = {}
        
        if 'prompt' in test_types:
            try:
                logger.info("Running prompt tests...")
                results['prompt'] = await self.prompt_tester.run_tests()
                logger.info(f"Prompt tests completed: Score: {results['prompt'].get('summary', {}).get('average_score', 0):.2f}")
            except Exception as e:
                errors['prompt'] = str(e)
                logger.error(f"Prompt tests failed: {e}")
        
        if 'agent' in test_types:
            try:
                logger.info("Running agent tests...")
                results['agent'] = await self.agent_tester.run_tests()
                logger.info(f"Agent tests completed: Overall score: {results['agent'].get('summary', {}).get('overall_score', 0):.2f}")
            except Exception as e:
                errors['agent'] = str(e)
                logger.error(f"Agent tests failed: {e}")
        
        if 'kb' in test_types:
            try:
                logger.info("Running KB validation...")
                results['kb'] = await self.kb_validator.run_validation()
                logger.info(f"KB validation completed: Health: {results['kb'].get('summary', {}).get('overall_health', 0):.2f}")
            except Exception as e:
                errors['kb'] = str(e)
                logger.error(f"KB validation failed: {e}")
        
        if 'e2e' in test_types:
            try:
                logger.info("Running E2E tests...")
                results['e2e'] = await self.e2e_tester.run_tests()
                logger.info(f"E2E tests completed: Overall score: {results['e2e'].get('summary', {}).get('overall_score', 0):.2f}")
            except Exception as e:
                errors['e2e'] = str(e)
                logger.error(f"E2E tests failed: {e}")
        
        test_duration = (datetime.now() - test_start_time).total_seconds()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(results, errors, test_duration)
        
        # Store results
        self.results = results
        self.test_history.append({
            "timestamp": datetime.now().isoformat(),
            "test_types": test_types,
            "results": report
        })
        
        # Save results if requested
        if save_results:
            self._save_comprehensive_report(report)
        
        # Cleanup
        await self.api_client.close()
        
        self.metrics.end_test(
            timer_id=test_start_timer,
            status="completed",
            score=report.get("summary", {}).get("overall_score", 0),
            details={"test_types": test_types, "duration": test_duration}
        )



        logger.info(f"Testing completed in {test_duration:.1f} seconds")
        




        return report
    
    async def run_quick_test(self) -> Dict[str, Any]:
        """
        Run a quick health and functionality test
        
        Returns:
            Quick test results
        """
        logger.info("Running quick test...")
        
        test_start_time = datetime.now()
        
        try:
            # Health check
            health_status = await self._health_check()
            
            # Run a simple E2E test
            simple_scenario = {
                "id": "QUICK_TEST_001",
                "title": "Quick Test Scenario",
                "scenario": "Test if the Sales EVA system is functioning correctly with a basic banking opportunity.",
                "company": "Test Bank",
                "industry": "Banking",
                "budget": "$1M",
                "timeline": "6 months",
                "key_requirements": ["Basic analysis", "Solution matching"],
                "success_criteria": ["Should respond", "Should be relevant"],
                "complexity": "low",
                "priority": "medium"
            }
            
            response = await self.api_client.analyze_opportunity(
                opportunity_description=simple_scenario["scenario"]
            )
            
            test_duration = (datetime.now() - test_start_time).total_seconds()
            
            # Simple evaluation
            response_str = json.dumps(response).lower()
            score = 0.5  # Base score
            
            if "solution" in response_str or "offering" in response_str:
                score += 0.3
            if "bank" in response_str or "financial" in response_str:
                score += 0.2
            
            result = {
                "status": "completed",
                "health_check": health_status,
                "score": min(1.0, score),
                "latency": test_duration,
                "response_received": bool(response),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.api_client.close()
            
            logger.info(f"Quick test completed: Score: {result['score']:.2f}, Latency: {test_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Quick test failed: {e}")
            
            await self.api_client.close()
            
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _health_check(self) -> bool:
        """Check if API is accessible"""
        try:
            return await self.api_client.health_check()
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def _generate_comprehensive_report(self, 
                                     results: Dict[str, Any], 
                                     errors: Dict[str, str],
                                     duration: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Calculate overall scores
        scores = {}
        for test_type, result in results.items():
            if test_type == 'prompt':
                scores[test_type] = result.get('summary', {}).get('average_score', 0)
            elif test_type == 'agent':
                scores[test_type] = result.get('summary', {}).get('overall_score', 0)
            elif test_type == 'kb':
                scores[test_type] = result.get('summary', {}).get('overall_health', 0)
            elif test_type == 'e2e':
                scores[test_type] = result.get('summary', {}).get('overall_score', 0)
        
        # Calculate overall system score
        if scores:
            overall_score = sum(scores.values()) / len(scores)
        else:
            overall_score = 0
        
        # Generate recommendations
        recommendations = self._generate_system_recommendations(results, scores)
        
        # System health assessment
        health_assessment = self._assess_system_health(scores, errors)
        
        report = {
            "metadata": {
                "api_url": self.api_url,
                "test_timestamp": datetime.now().isoformat(),
                "test_duration_seconds": duration,
                "testing_framework_version": "1.0.0"
            },
            "summary": {
                "overall_score": overall_score,
                "individual_scores": scores,
                "tests_completed": list(results.keys()),
                "tests_failed": list(errors.keys()),
                "health_assessment": health_assessment
            },
            "detailed_results": results,
            "errors": errors if errors else None,
            "recommendations": recommendations,
            "action_items": self._generate_action_items(results, errors)
        }
        
        return report
    
    def _generate_system_recommendations(self, 
                                        results: Dict[str, Any],
                                        scores: Dict[str, float]) -> List[str]:
        """Generate system-level recommendations"""
        recommendations = []
        
        # Score-based recommendations
        for test_type, score in scores.items():
            if score < 0.6:
                recommendations.append(f"Critical: Improve {test_type} performance (score: {score:.2f})")
            elif score < 0.8:
                recommendations.append(f"Improve {test_type} (score: {score:.2f})")
            elif score > 0.9:
                recommendations.append(f"Excellent {test_type} performance (score: {score:.2f})")
        
        # Specific recommendations from test results
        if 'prompt' in results:
            prompt_recs = results['prompt'].get('recommendations', [])
            recommendations.extend(prompt_recs[:2])
        
        if 'agent' in results:
            agent_recs = results['agent'].get('recommendations', [])
            recommendations.extend(agent_recs[:2])
        
        if 'kb' in results:
            kb_recs = results['kb'].get('recommendations', [])
            recommendations.extend(kb_recs[:2])
        
        if 'e2e' in results:
            e2e_recs = results['e2e'].get('recommendations', [])
            recommendations.extend(e2e_recs[:2])
        
        # Remove duplicates and limit
        unique_recs = list(dict.fromkeys(recommendations))
        return unique_recs[:10]
    
    def _assess_system_health(self, scores: Dict[str, float], errors: Dict[str, str]) -> Dict[str, Any]:
        """Assess overall system health"""
        
        if errors:
            health_status = "unhealthy"
            health_description = f"System has {len(errors)} critical failures"
            priority = "critical"
        
        elif not scores:
            health_status = "unknown"
            health_description = "No test results available"
            priority = "medium"
        
        else:
            # Calculate health score
            avg_score = sum(scores.values()) / len(scores)
            
            if avg_score >= 0.8:
                health_status = "excellent"
                health_description = "System performing at high level"
                priority = "low"
            elif avg_score >= 0.7:
                health_status = "good"
                health_description = "System performing adequately"
                priority = "medium"
            elif avg_score >= 0.6:
                health_status = "fair"
                health_description = "System needs improvement"
                priority = "high"
            else:
                health_status = "poor"
                health_description = "System needs significant improvement"
                priority = "critical"
        
        return {
            "status": health_status,
            "description": health_description,
            "priority": priority,
            "avg_score": sum(scores.values()) / len(scores) if scores else 0
        }
    
    def _generate_action_items(self, results: Dict[str, Any], errors: Dict[str, str]) -> List[Dict[str, str]]:
        """Generate actionable items from test results"""
        action_items = []
        
        # Error handling actions
        for test_type, error in errors.items():
            action_items.append({
                "type": "critical",
                "test": test_type,
                "action": f"Fix error: {error[:100]}...",
                "priority": "high"
            })
        
        # Improvement actions from results
        if 'prompt' in results:
            best_prompt = results['prompt'].get('best_prompts', [{}])[0]
            action_items.append({
                "type": "optimization",
                "test": "prompt",
                "action": f"Use prompt '{best_prompt.get('prompt_name', '')}' (score: {best_prompt.get('score', 0):.2f})",
                "priority": "medium"
            })
        
        if 'agent' in results:
            weakest = results['agent'].get('summary', {}).get('weakest_function', {})
            if weakest.get('score', 1) < 0.7:
                action_items.append({
                    "type": "improvement",
                    "test": "agent",
                    "action": f"Improve {weakest.get('function', 'unknown')} function (score: {weakest.get('score', 0):.2f})",
                    "priority": "high"
                })
        
        if 'kb' in results:
            gaps = results['kb'].get('kb_gaps', [])
            if gaps:
                action_items.append({
                    "type": "content",
                    "test": "kb",
                    "action": f"Address knowledge gap: {gaps[0].get('query', '')[:50]}...",
                    "priority": "medium"
                })
        
        if 'e2e' in results:
            worst_scenario = results['e2e'].get('performance_insights', {}).get('worst_scenarios', [{}])[0]
            if worst_scenario.get('score', 1) < 0.6:
                action_items.append({
                    "type": "scenario",
                    "test": "e2e",
                    "action": f"Improve handling of '{worst_scenario.get('title', '')[:30]}...' scenario",
                    "priority": "medium"
                })
        
        return action_items[:5]
    
    def _save_comprehensive_report(self, report: Dict[str, Any]):
        """Save comprehensive report to file"""
        try:
            results_dir = settings.RESULTS_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"comprehensive_test_report_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Comprehensive report saved to {filename}")
            
            # Also save a summary file
            summary = {
                "timestamp": report["metadata"]["test_timestamp"],
                "overall_score": report["summary"]["overall_score"],
                "health_status": report["summary"]["health_assessment"]["status"],
                "tests_completed": report["summary"]["tests_completed"],
                "key_recommendations": report["recommendations"][:3]
            }
            
            summary_filename = results_dir / f"test_summary_{timestamp}.json"
            with open(summary_filename, 'w') as f:
                json.dump(summary, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def get_test_history(self, limit: int = 10) -> List[Dict]:
        """Get recent test history"""
        return self.test_history[-limit:]
    
    def get_latest_results(self) -> Optional[Dict]:
        """Get latest test results"""
        if self.test_history:
            return self.test_history[-1]
        return None
    
    async def close(self):
        """Cleanup resources"""
        await self.api_client.close()