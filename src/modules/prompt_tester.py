import asyncio
import concurrent.futures
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from tqdm import tqdm

from src.api_client import APIClient, TestDataGenerator
from config.settings import settings

logger = logging.getLogger(__name__)

class PromptTester:
    """Test and optimize system prompts using LLM-generated prompts"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.test_generator = TestDataGenerator()
        self.results = []
        
    async def run_tests(self, prompt_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Run comprehensive prompt testing
        
        Steps:
        1. Generate prompt variations using LLM
        2. Generate test cases using LLM  
        3. Test each prompt with sample test cases
        4. Evaluate and rank prompts
        """
        logger.info("Starting prompt testing...")
        
        prompt_count = prompt_count or settings.PROMPT_TEST_COUNT
        test_case_count = min(20, prompt_count // 5)  # 20 test cases or 1/5 of prompts
        
        # Generate test data using LLM
        logger.info(f"Generating {prompt_count} prompt variations using LLM...")
        prompts = self.test_generator.generate_system_prompts(prompt_count)
        
        logger.info(f"Generating {test_case_count} test cases using LLM...")
        test_cases = self.test_generator.generate_test_cases(test_case_count)
        
        if not prompts or not test_cases:
            raise ValueError("Failed to generate test data")
        
        logger.info(f"Testing {len(prompts)} prompts with {len(test_cases)} test cases...")
        
        # Test each prompt with a subset of test cases
        results = await self._test_prompts_parallel(prompts, test_cases)
        
        # Analyze results
        analysis = self._analyze_results(results, prompts, test_cases)
        
        # Save results
        self._save_results(analysis)
        
        logger.info(f"Prompt testing completed. Best prompt score: {analysis.get('best_score', 0):.2f}")
        
        return analysis
    
    async def _test_prompts_parallel(self, 
                                    prompts: List[Dict], 
                                    test_cases: List[Dict]) -> List[Dict]:
        """Test prompts in parallel with error handling"""
        results = []
        
        # Use a subset of test cases for prompt testing (for speed)
        test_subset = test_cases[:min(10, len(test_cases))]
        
        # Create tasks for each prompt
        tasks = []
        for prompt in prompts:
            tasks.append(self._test_single_prompt(prompt, test_subset))
        
        # Execute in parallel with progress bar
        with tqdm(total=len(tasks), desc="Testing prompts") as pbar:
            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Prompt test failed: {e}")
                finally:
                    pbar.update(1)
        
        return results
    
    async def _test_single_prompt(self, 
                                 prompt: Dict, 
                                 test_cases: List[Dict]) -> Dict:
        """Test a single prompt with multiple test cases"""
        prompt_id = prompt["id"]
        prompt_content = prompt["content"]
        
        prompt_results = []
        
        for test_case in test_cases[:5]:  # Limit to 5 test cases per prompt
            try:
                # Call Sales EVA API with this prompt
                start_time = datetime.now()
                
                response = await self.api_client.analyze_opportunity(
                    opportunity_description=test_case["opportunity"],
                    prompt_override=prompt_content
                )
                
                latency = (datetime.now() - start_time).total_seconds()
                
                # Evaluate response
                evaluation = self._evaluate_response(
                    response=response,
                    test_case=test_case,
                    prompt=prompt
                )
                
                prompt_results.append({
                    "test_case_id": test_case["id"],
                    "latency": latency,
                    "scores": evaluation,
                    "response_summary": self._summarize_response(response)
                })
                
            except Exception as e:
                logger.debug(f"Test case {test_case['id']} failed for prompt {prompt_id}: {e}")
                prompt_results.append({
                    "test_case_id": test_case["id"],
                    "error": str(e),
                    "scores": {"error": 1.0}
                })
        
        # Calculate aggregate scores for this prompt
        aggregate_score = self._calculate_aggregate_score(prompt_results)
        
        return {
            "prompt_id": prompt_id,
            "prompt_name": prompt["name"],
            "prompt_style": prompt.get("style", "unknown"),
            "prompt_length": prompt.get("length", "medium"),
            "results": prompt_results,
            "aggregate_score": aggregate_score,
            "success_rate": self._calculate_success_rate(prompt_results)
        }
    
    def _evaluate_response(self, 
                          response: Dict, 
                          test_case: Dict,
                          prompt: Dict) -> Dict[str, float]:
        """
        Evaluate API response based on test case criteria
        
        This evaluates:
        1. Completeness - Does response contain expected elements?
        2. Relevance - Is response relevant to the opportunity?
        3. Actionability - Can sales team use this?
        4. Structure - Is response well-structured?
        """
        scores = {}
        
        try:
            # Extract response text
            response_text = json.dumps(response).lower()
            
            # Check for key elements
            required_elements = [
                "offerings", "solutions", "recommendations",
                "analysis", "match", "case"
            ]
            
            completeness_score = 0
            for element in required_elements:
                if element in response_text:
                    completeness_score += 0.2  # 0.2 per element, max 1.0
            
            scores["completeness"] = min(1.0, completeness_score)
            
            # Check relevance to test case requirements
            relevance_score = 0
            requirements = test_case.get("requirements", [])
            for req in requirements[:5]:  # Check first 5 requirements
                if req.lower() in response_text:
                    relevance_score += 0.2
            
            scores["relevance"] = min(1.0, relevance_score)
            
            # Check for actionability indicators
            action_words = ["should", "recommend", "suggest", "next steps", "action"]
            actionability_score = 0
            for word in action_words:
                if word in response_text:
                    actionability_score += 0.2
            
            scores["actionability"] = min(1.0, actionability_score)
            
            # Check structure (basic heuristic)
            structure_score = 0.5  # Base score
            
            # Additional points for good structure indicators
            structure_indicators = [
                "##", "###",  # Markdown headers
                "1.", "2.", "3.",  # Numbered lists
                "- ", "* ",  # Bullet points
                "\n\n"  # Paragraph breaks
            ]
            
            for indicator in structure_indicators:
                if indicator in response_text:
                    structure_score += 0.1
            
            scores["structure"] = min(1.0, structure_score)
            
            # Overall score (weighted average)
            weights = {
                "completeness": 0.3,
                "relevance": 0.3,
                "actionability": 0.25,
                "structure": 0.15
            }
            
            overall_score = sum(scores[key] * weights[key] for key in scores.keys())
            scores["overall"] = overall_score
            
        except Exception as e:
            logger.warning(f"Evaluation failed: {e}")
            scores = {"error": 0.0, "overall": 0.0}
        
        return scores
    
    def _calculate_aggregate_score(self, prompt_results: List[Dict]) -> Dict[str, float]:
        """Calculate aggregate scores across all test cases for a prompt"""
        if not prompt_results:
            return {"overall": 0.0}
        
        aggregate = {
            "completeness": [],
            "relevance": [],
            "actionability": [],
            "structure": [],
            "overall": [],
            "latency": []
        }
        
        for result in prompt_results:
            if "scores" in result:
                for key in aggregate.keys():
                    if key in result["scores"]:
                        aggregate[key].append(result["scores"][key])
                if "latency" in result:
                    aggregate["latency"].append(result["latency"])
        
        # Calculate averages
        avg_scores = {}
        for key, values in aggregate.items():
            if values:
                avg_scores[f"avg_{key}"] = sum(values) / len(values)
            else:
                avg_scores[f"avg_{key}"] = 0.0
        
        # Overall weighted score
        weights = {
            "avg_completeness": 0.3,
            "avg_relevance": 0.3,
            "avg_actionability": 0.25,
            "avg_structure": 0.15
        }
        
        weighted_score = sum(
            avg_scores.get(f"avg_{key}", 0) * weight 
            for key, weight in weights.items()
        )
        
        avg_scores["weighted_overall"] = weighted_score
        return avg_scores
    
    def _calculate_success_rate(self, prompt_results: List[Dict]) -> float:
        """Calculate success rate (non-error responses)"""
        if not prompt_results:
            return 0.0
        
        successful = sum(1 for r in prompt_results if "error" not in r)
        return successful / len(prompt_results)
    
    def _summarize_response(self, response: Dict, max_length: int = 200) -> str:
        """Create a short summary of the response"""
        try:
            response_str = json.dumps(response)
            if len(response_str) > max_length:
                return response_str[:max_length] + "..."
            return response_str
        except:
            return str(response)[:max_length]
    
    def _analyze_results(self, 
                        results: List[Dict],
                        prompts: List[Dict],
                        test_cases: List[Dict]) -> Dict[str, Any]:
        """Analyze all test results and generate insights"""
        
        # Sort prompts by score
        sorted_results = sorted(
            results, 
            key=lambda x: x.get("aggregate_score", {}).get("weighted_overall", 0),
            reverse=True
        )
        
        # Get best and worst prompts
        best_prompts = sorted_results[:5]
        worst_prompts = sorted_results[-5:] if len(sorted_results) > 5 else []
        
        # Calculate statistics
        all_scores = [
            r.get("aggregate_score", {}).get("weighted_overall", 0)
            for r in results
        ]
        
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            min_score = min(all_scores)
        else:
            avg_score = max_score = min_score = 0.0
        
        # Analyze by prompt style
        style_scores = {}
        for result in results:
            style = result.get("prompt_style", "unknown")
            score = result.get("aggregate_score", {}).get("weighted_overall", 0)
            
            if style not in style_scores:
                style_scores[style] = []
            style_scores[style].append(score)
        
        style_analysis = {
            style: {
                "count": len(scores),
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "max_score": max(scores) if scores else 0
            }
            for style, scores in style_scores.items()
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(best_prompts, worst_prompts, style_analysis)
        
        return {
            "summary": {
                "total_prompts_tested": len(results),
                "total_test_cases": len(test_cases),
                "average_score": avg_score,
                "best_score": max_score,
                "worst_score": min_score,
                "timestamp": datetime.now().isoformat()
            },
            "best_prompts": [
                {
                    "rank": i + 1,
                    "prompt_id": p["prompt_id"],
                    "prompt_name": p["prompt_name"],
                    "score": p["aggregate_score"].get("weighted_overall", 0),
                    "success_rate": p.get("success_rate", 0),
                    "style": p.get("prompt_style", "unknown"),
                    "length": p.get("prompt_length", "medium")
                }
                for i, p in enumerate(best_prompts)
            ],
            "style_analysis": style_analysis,
            "performance_metrics": {
                "score_distribution": all_scores,
                "prompt_length_impact": self._analyze_length_impact(results),
                "style_impact": style_analysis
            },
            "recommendations": recommendations,
            "raw_results": results[:10]  # Include first 10 raw results for debugging
        }
    
    def _analyze_length_impact(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze impact of prompt length on performance"""
        length_scores = {"short": [], "medium": [], "long": []}
        
        for result in results:
            length = result.get("prompt_length", "medium")
            score = result.get("aggregate_score", {}).get("weighted_overall", 0)
            
            if length in length_scores:
                length_scores[length].append(score)
        
        analysis = {}
        for length, scores in length_scores.items():
            if scores:
                analysis[length] = {
                    "count": len(scores),
                    "avg_score": sum(scores) / len(scores),
                    "max_score": max(scores),
                    "min_score": min(scores)
                }
            else:
                analysis[length] = {"count": 0, "avg_score": 0, "max_score": 0, "min_score": 0}
        
        return analysis
    
    def _generate_recommendations(self, 
                                 best_prompts: List[Dict],
                                 worst_prompts: List[Dict],
                                 style_analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if not best_prompts:
            return ["No valid prompts tested"]
        
        # Identify best performing style
        best_style = None
        best_style_score = 0
        
        for style, analysis in style_analysis.items():
            if analysis["avg_score"] > best_style_score:
                best_style_score = analysis["avg_score"]
                best_style = style
        
        if best_style:
            recommendations.append(f"Use '{best_style}' style prompts (avg score: {best_style_score:.2f})")
        
        # Analyze length impact
        best_prompt = best_prompts[0]
        best_length = best_prompt.get("prompt_length", "medium")
        recommendations.append(f"Optimal prompt length: {best_length}")
        
        # Common patterns in best prompts
        top_scores = [p["aggregate_score"].get("weighted_overall", 0) for p in best_prompts[:3]]
        if all(score > 0.7 for score in top_scores):
            recommendations.append("Top prompts consistently score >0.7 - use these as templates")
        
        # Issues in worst prompts
        if worst_prompts:
            worst_style = worst_prompts[0].get("prompt_style", "unknown")
            recommendations.append(f"Avoid '{worst_style}' style (lowest performance)")
        
        return recommendations
    
    def _save_results(self, analysis: Dict):
        """Save test results to file"""
        try:
            results_dir = settings.RESULTS_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"prompt_test_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")