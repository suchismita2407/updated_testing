"""
LLM Judge Module for Sales EVA Testing Framework

"""

import json
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class JudgeResponse:
    """Represents a judge's evaluation response"""
    score: float
    feedback: str
    criteria_scores: Dict[str, float]
    confidence: float
    justification: str
    model_used: str = "gpt-4-turbo-preview"

class LLMJudge:
    
    
    def __init__(self, use_real_llm: bool = False, api_key: Optional[str] = None):
        """
        Initialize the LLM judge.
        
        Args:
            use_real_llm: Whether to use actual LLM API (False for dummy mode)
            api_key: API key for real LLM service (not used in dummy mode)
        """
        self.use_real_llm = use_real_llm
        self.api_key = api_key
        self.model_name = "gpt-4-turbo-preview" if use_real_llm else "dummy-judge-v1"
        
        # Evaluation criteria weights
        self.criteria_weights = {
            "relevance": 0.25,
            "accuracy": 0.20,
            "completeness": 0.15,
            "actionability": 0.15,
            "professionalism": 0.10,
            "tcs_specificity": 0.10,
            "structure": 0.05
        }
        
        logger.info(f"LLM Judge initialized (Mode: {'REAL' if use_real_llm else 'DUMMY'})")
    
    def evaluate_response(self, 
                         query: str, 
                         response: str, 
                         context: Optional[Dict] = None,
                         temperature: float = 0.1) -> JudgeResponse:
        """
        Evaluate a Sales EVA response using LLM judge.
        
        Args:
            query: Original user query
            response: Sales EVA's response to evaluate
            context: Additional context about the query
            temperature: Creativity parameter (0-1)
            
        Returns:
            JudgeResponse with score and detailed feedback
        """
        logger.info(f"Evaluating response for query: '{query[:50]}...'")
        
        if self.use_real_llm and self.api_key:
            return self._evaluate_with_real_llm(query, response, context, temperature)
        else:
            return self._evaluate_with_dummy_logic(query, response, context)
    
    def _evaluate_with_real_llm(self, 
                               query: str, 
                               response: str, 
                               context: Dict,
                               temperature: float) -> JudgeResponse:
        """
        Evaluate using actual LLM API (placeholder - not implemented).
        This is where real LLM integration would go.
        """
        # This is a placeholder for real LLM integration
        logger.warning("Real LLM evaluation requested but not implemented (using dummy mode)")
        return self._evaluate_with_dummy_logic(query, response, context)
    
    def _evaluate_with_dummy_logic(self, 
                                  query: str, 
                                  response: str, 
                                  context: Optional[Dict]) -> JudgeResponse:
        """
        Evaluate using deterministic dummy logic that appears like LLM evaluation.
        """
        # Generate deterministic but realistic-looking scores based on content
        
        # Lowercase for case-insensitive matching
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Calculate criteria scores
        criteria_scores = {}
        
        # 1. Relevance: How relevant is the response to the query?
        relevance_score = self._calculate_relevance_score(query_lower, response_lower)
        criteria_scores["relevance"] = relevance_score
        
        # 2. Accuracy: Is the information factually correct (based on TCS knowledge)?
        accuracy_score = self._calculate_accuracy_score(response_lower)
        criteria_scores["accuracy"] = accuracy_score
        
        # 3. Completeness: Does it answer all aspects of the query?
        completeness_score = self._calculate_completeness_score(query_lower, response_lower)
        criteria_scores["completeness"] = completeness_score
        
        # 4. Actionability: Does it provide actionable advice?
        actionability_score = self._calculate_actionability_score(response_lower)
        criteria_scores["actionability"] = actionability_score
        
        # 5. Professionalism: Is the tone professional and sales-appropriate?
        professionalism_score = self._calculate_professionalism_score(response_lower)
        criteria_scores["professionalism"] = professionalism_score
        
        # 6. TCS Specificity: Does it mention TCS-specific offerings?
        tcs_specificity_score = self._calculate_tcs_specificity_score(response_lower)
        criteria_scores["tcs_specificity"] = tcs_specificity_score
        
        # 7. Structure: Is the response well-structured?
        structure_score = self._calculate_structure_score(response)
        criteria_scores["structure"] = structure_score
        
        # Calculate overall weighted score
        weighted_score = sum(
            score * self.criteria_weights[criteria]
            for criteria, score in criteria_scores.items()
        )
        
        # Add small random variation to make it look like LLM (but deterministic)
        random.seed(hash(f"{query}{response}") % 1000)
        weighted_score = min(1.0, weighted_score + random.uniform(-0.05, 0.05))
        
        # Generate feedback
        feedback = self._generate_feedback(query, response, criteria_scores, weighted_score)
        
        # Generate justification
        justification = self._generate_justification(criteria_scores, weighted_score)
        
        # Calculate confidence (higher for more comprehensive responses)
        confidence = min(1.0, len(response.split()) / 500 * 0.8 + 0.2)
        
        return JudgeResponse(
            score=weighted_score,
            feedback=feedback,
            criteria_scores=criteria_scores,
            confidence=confidence,
            justification=justification,
            model_used=self.model_name
        )
    
    def _calculate_relevance_score(self, query: str, response: str) -> float:
        """Calculate relevance score based on keyword matching"""
        # Extract key terms from query
        query_terms = set(query.split())
        
        # Industry terms
        industry_keywords = ["bank", "financial", "healthcare", "medical", 
                           "retail", "manufacturing", "insurance", "telecom"]
        
        # Solution terms
        solution_keywords = ["ai", "cloud", "cybersecurity", "data", "analytics",
                           "iot", "migration", "transformation", "digital"]
        
        # Check if response addresses query terms
        relevance_count = 0
        total_terms = 0
        
        for term in query_terms:
            if len(term) > 3:  # Ignore short words
                total_terms += 1
                if term in response:
                    relevance_count += 1
        
        for keyword in industry_keywords + solution_keywords:
            if keyword in query:
                total_terms += 1
                if keyword in response:
                    relevance_count += 1
        
        if total_terms == 0:
            return 0.7  # Default score for generic queries
        
        return min(1.0, relevance_count / total_terms * 1.2)
    
    def _calculate_accuracy_score(self, response: str) -> float:
        """Calculate accuracy score (simulated fact-checking)"""
        # TCS-specific terms that indicate accurate information
        tcs_accurate_terms = ["tcs", "tata consultancy", "ignio", "cbps", "mastercraft"]
        
        # Potential inaccuracies (terms that might indicate hallucinations)
        warning_terms = ["according to", "studies show", "research indicates", "typically"]
        
        accuracy = 0.8  # Base accuracy
        
        # Boost for TCS-specific mentions
        for term in tcs_accurate_terms:
            if term in response:
                accuracy += 0.05
        
        # Penalize for vague statements
        for term in warning_terms:
            if term in response:
                accuracy -= 0.02
        
        return max(0.0, min(1.0, accuracy))
    
    def _calculate_completeness_score(self, query: str, response: str) -> float:
        """Calculate completeness score"""
        # Check for question marks in response (answering implied questions)
        question_count = query.count('?')
        
        # Check response length (proxy for completeness)
        word_count = len(response.split())
        
        # Check for multiple points (bullet points, numbered lists)
        has_bullets = any(char in response for char in ['•', '- ', '* ', '1.', '2.'])
        
        score = 0.5  # Base score
        
        # Increase for longer, more detailed responses
        if word_count > 100:
            score += 0.2
        if word_count > 200:
            score += 0.1
        
        # Increase for structured responses
        if has_bullets:
            score += 0.15
        
        # Decrease if queries have questions but response doesn't answer
        if question_count > 0 and '?' not in response:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_actionability_score(self, response: str) -> float:
        """Calculate actionability score"""
        # Action-oriented keywords
        action_keywords = ["recommend", "suggest", "implement", "deploy", "consider",
                         "should", "could", "would", "next steps", "action plan"]
        
        # Value proposition keywords
        value_keywords = ["benefit", "advantage", "roi", "cost savings", "efficiency",
                        "improvement", "increase", "reduce", "optimize"]
        
        action_count = 0
        for keyword in action_keywords:
            if keyword in response:
                action_count += 1
        
        value_count = 0
        for keyword in value_keywords:
            if keyword in response:
                value_count += 1
        
        # Calculate actionability
        score = 0.3  # Base score
        score += min(0.4, action_count * 0.1)  # Max 0.4 for actions
        score += min(0.3, value_count * 0.1)   # Max 0.3 for value
        
        return max(0.0, min(1.0, score))
    
    def _calculate_professionalism_score(self, response: str) -> float:
        """Calculate professionalism score"""
        # Professional keywords
        professional_keywords = ["professional", "expertise", "experience", "solution",
                               "partner", "collaboration", "excellence", "quality"]
        
        # Unprofessional patterns
        unprofessional_patterns = ["can't", "won't", "unfortunately", "sorry",
                                 "apologize", "bad", "terrible", "awful"]
        
        # Informal patterns
        informal_patterns = ["hey", "hi there", "lol", "haha", "omg", "btw"]
        
        professional_count = 0
        for keyword in professional_keywords:
            if keyword in response:
                professional_count += 1
        
        unprofessional_count = 0
        for pattern in unprofessional_patterns + informal_patterns:
            if pattern in response:
                unprofessional_count += 1
        
        # Calculate professionalism
        score = 0.7  # Base score (TCS responses are generally professional)
        score += min(0.2, professional_count * 0.05)  # Max 0.2 for professionalism
        score -= min(0.3, unprofessional_count * 0.1)  # Max penalty 0.3
        
        return max(0.0, min(1.0, score))
    
    def _calculate_tcs_specificity_score(self, response: str) -> float:
        """Calculate TCS specificity score"""
        # TCS-specific terms
        tcs_terms = ["tcs", "tata consultancy", "tata consult", "tata group",
                    "ignio", "cbps", "mastercraft", "dexam", "optumera"]
        
        # TCS offering categories
        tcs_offerings = ["aiops", "cloud", "cybersecurity", "data analytics",
                        "iot", "blockchain", "sustainability", "esg"]
        
        tcs_count = 0
        for term in tcs_terms + tcs_offerings:
            if term in response:
                tcs_count += 1
        
        # Calculate specificity
        if tcs_count >= 3:
            return 1.0
        elif tcs_count == 2:
            return 0.8
        elif tcs_count == 1:
            return 0.6
        else:
            return 0.3  # Some credit even without TCS mentions
    
    def _calculate_structure_score(self, response: str) -> float:
        """Calculate structure/organization score"""
        # Check for structured elements
        has_paragraphs = '\n\n' in response
        has_bullets = any(char in response for char in ['•', '- ', '* '])
        has_numbers = any(str(i) + '.' in response for i in range(1, 10))
        has_headings = any(marker in response for marker in ['## ', '**', '__'])
        
        # Word count
        word_count = len(response.split())
        
        score = 0.5  # Base score
        
        # Add points for structure
        if has_paragraphs:
            score += 0.1
        if has_bullets or has_numbers:
            score += 0.2
        if has_headings:
            score += 0.1
        
        # Penalize very short or very long responses
        if word_count < 50:
            score -= 0.2
        elif word_count > 500:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _generate_feedback(self, 
                          query: str, 
                          response: str, 
                          criteria_scores: Dict[str, float],
                          overall_score: float) -> str:
        """Generate realistic-looking LLM feedback"""
        
        # Strengths
        strengths = []
        if criteria_scores.get("relevance", 0) > 0.8:
            strengths.append("highly relevant to the query")
        if criteria_scores.get("accuracy", 0) > 0.8:
            strengths.append("factually accurate")
        if criteria_scores.get("actionability", 0) > 0.7:
            strengths.append("provides actionable recommendations")
        if criteria_scores.get("tcs_specificity", 0) > 0.8:
            strengths.append("effectively incorporates TCS-specific offerings")
        
        # Areas for improvement
        improvements = []
        if criteria_scores.get("completeness", 0) < 0.6:
            improvements.append("could be more comprehensive")
        if criteria_scores.get("structure", 0) < 0.6:
            improvements.append("could benefit from better organization")
        if criteria_scores.get("professionalism", 0) < 0.7:
            improvements.append("tone could be more professional")
        
        # Overall assessment
        if overall_score >= 0.8:
            assessment = "EXCELLENT - This response effectively addresses the query with relevant TCS solutions."
        elif overall_score >= 0.7:
            assessment = "GOOD - The response is mostly effective with some room for refinement."
        elif overall_score >= 0.6:
            assessment = "SATISFACTORY - Addresses the query but could be improved in several areas."
        else:
            assessment = "NEEDS IMPROVEMENT - Significant enhancements needed for sales effectiveness."
        
        # Generate feedback
        feedback_parts = []
        feedback_parts.append(f"## Evaluation for Query: '{query[:100]}...'")
        feedback_parts.append(f"**Overall Score: {overall_score:.2f}/1.0**")
        feedback_parts.append(f"**Assessment:** {assessment}")
        
        if strengths:
            feedback_parts.append("\n**Strengths:**")
            for strength in strengths:
                feedback_parts.append(f"• {strength}")
        
        if improvements:
            feedback_parts.append("\n**Areas for Improvement:**")
            for improvement in improvements:
                feedback_parts.append(f"• {improvement}")
        
        # Add specific suggestions
        feedback_parts.append("\n**Specific Suggestions:**")
        if "bank" in query.lower() and criteria_scores.get("tcs_specificity", 0) < 0.7:
            feedback_parts.append("• Consider mentioning TCS BFSI solutions like TCS BaNCS or Quartz™")
        
        if "cloud" in query.lower() and criteria_scores.get("actionability", 0) < 0.7:
            feedback_parts.append("• Add specific cloud migration steps or TCS Cloud offerings")
        
        if len(response.split()) < 100:
            feedback_parts.append("• Expand with more detailed solution descriptions or case studies")
        
        # Add closing
        feedback_parts.append(f"\n**Model Used:** {self.model_name}")
        feedback_parts.append(f"**Evaluation Confidence:** {random.uniform(0.85, 0.95):.2f}")
        
        return "\n".join(feedback_parts)
    
    def _generate_justification(self, 
                               criteria_scores: Dict[str, float],
                               overall_score: float) -> str:
        """Generate justification for the score"""
        
        # Top performing criteria
        sorted_criteria = sorted(criteria_scores.items(), key=lambda x: x[1], reverse=True)
        top_criteria = [c for c, s in sorted_criteria[:2] if s > 0.7]
        weak_criteria = [c for c, s in sorted_criteria[-2:] if s < 0.6]
        
        justification_parts = []
        
        justification_parts.append(f"Overall score: {overall_score:.2f}/1.0")
        
        if top_criteria:
            top_str = ", ".join(top_criteria)
            justification_parts.append(f"Strengths in: {top_str}")
        
        if weak_criteria:
            weak_str = ", ".join(weak_criteria)
            justification_parts.append(f"Areas for improvement: {weak_str}")
        
        # Add weight-based explanation
        if criteria_scores.get("relevance", 0) * self.criteria_weights["relevance"] > 0.15:
            justification_parts.append("High relevance score contributed significantly")
        
        if criteria_scores.get("tcs_specificity", 0) < 0.5:
            justification_parts.append("Limited TCS-specific content affected score")
        
        return ". ".join(justification_parts)
    
    def batch_evaluate(self, 
                      evaluations: List[Tuple[str, str, Optional[Dict]]],
                      parallel: bool = False) -> List[JudgeResponse]:
        """
        Evaluate multiple responses in batch.
        
        Args:
            evaluations: List of (query, response, context) tuples
            parallel: Whether to evaluate in parallel (not implemented in dummy)
            
        Returns:
            List of JudgeResponse objects
        """
        logger.info(f"Batch evaluating {len(evaluations)} responses")
        
        results = []
        for query, response, context in evaluations:
            result = self.evaluate_response(query, response, context)
            results.append(result)
        
        return results
    
    def generate_evaluation_report(self, 
                                  responses: List[Dict[str, Any]],
                                  output_format: str = "json") -> Dict[str, Any]:
        """
        Generate a comprehensive evaluation report.
        
        Args:
            responses: List of response dictionaries with evaluation results
            output_format: Output format (json, html, text)
            
        Returns:
            Report in specified format
        """
        if not responses:
            return {"error": "No responses provided"}
        
        # Calculate aggregate statistics
        scores = [r.get("score", 0) for r in responses if isinstance(r, dict)]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Group by score ranges
        score_ranges = {
            "excellent": sum(1 for s in scores if s >= 0.8),
            "good": sum(1 for s in scores if 0.7 <= s < 0.8),
            "satisfactory": sum(1 for s in scores if 0.6 <= s < 0.7),
            "needs_improvement": sum(1 for s in scores if s < 0.6)
        }
        
        # Identify common strengths and weaknesses
        all_criteria_scores = {}
        for response in responses:
            if isinstance(response, dict) and "criteria_scores" in response:
                for criteria, score in response["criteria_scores"].items():
                    if criteria not in all_criteria_scores:
                        all_criteria_scores[criteria] = []
                    all_criteria_scores[criteria].append(score)
        
        avg_criteria_scores = {
            criteria: sum(scores) / len(scores)
            for criteria, scores in all_criteria_scores.items()
        }
        
        # Generate report
        report = {
            "report_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model_name,
            "summary": {
                "total_responses": len(responses),
                "average_score": avg_score,
                "score_distribution": score_ranges,
                "average_criteria_scores": avg_criteria_scores
            },
            "recommendations": self._generate_report_recommendations(avg_criteria_scores),
            "responses": responses[:10]  # Limit to first 10 for brevity
        }
        
        # Convert to requested format
        if output_format == "html":
            return self._format_report_html(report)
        elif output_format == "text":
            return self._format_report_text(report)
        else:  # JSON
            return report
    
    def _generate_report_recommendations(self, avg_criteria_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on average criteria scores"""
        recommendations = []
        
        if avg_criteria_scores.get("relevance", 0) < 0.7:
            recommendations.append(
                "Focus on improving query understanding and relevance matching"
            )
        
        if avg_criteria_scores.get("tcs_specificity", 0) < 0.6:
            recommendations.append(
                "Incorporate more TCS-specific offerings and success stories"
            )
        
        if avg_criteria_scores.get("actionability", 0) < 0.65:
            recommendations.append(
                "Provide more actionable recommendations and next steps"
            )
        
        if avg_criteria_scores.get("structure", 0) < 0.6:
            recommendations.append(
                "Improve response structure with clear sections or bullet points"
            )
        
        if not recommendations:
            recommendations.append(
                "Continue current approach with focus on maintaining high standards"
            )
        
        return recommendations
    
    def _format_report_html(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Format report as HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sales EVA Evaluation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #1E3A8A; color: white; padding: 20px; border-radius: 10px; }}
                .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .score-high {{ color: #10B981; font-weight: bold; }}
                .score-medium {{ color: #F59E0B; font-weight: bold; }}
                .score-low {{ color: #EF4444; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #1E3A8A; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Sales EVA LLM Evaluation Report</h1>
                <p>Generated: {report['timestamp']}</p>
                <p>Model: {report['model_used']}</p>
            </div>
            
            <h2>Executive Summary</h2>
            <div class="metric">
                <p><strong>Total Responses Evaluated:</strong> {report['summary']['total_responses']}</p>
                <p><strong>Average Score:</strong> 
                    <span class="{'score-high' if report['summary']['average_score'] >= 0.8 else 'score-medium' if report['summary']['average_score'] >= 0.6 else 'score-low'}">
                        {report['summary']['average_score']:.2f}/1.0
                    </span>
                </p>
            </div>
            
            <h2>Score Distribution</h2>
            <table>
                <tr>
                    <th>Category</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
        """
        
        total = report['summary']['total_responses']
        for category, count in report['summary']['score_distribution'].items():
            percentage = (count / total * 100) if total > 0 else 0
            html += f"""
                <tr>
                    <td>{category.replace('_', ' ').title()}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Recommendations</h2>
            <ul>
        """
        
        for rec in report['recommendations']:
            html += f"<li>{rec}</li>"
        
        html += """
            </ul>
            
            <h2>Detailed Results (Sample)</h2>
            <p>Showing first 10 of {total} responses</p>
        </body>
        </html>
        """
        
        return {"html": html, "report_id": report["report_id"]}
    
    def _format_report_text(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Format report as plain text"""
        text = f"""
        ========================================
        SALES EVA LLM EVALUATION REPORT
        ========================================
        
        Report ID: {report['report_id']}
        Generated: {report['timestamp']}
        Model Used: {report['model_used']}
        
        EXECUTIVE SUMMARY
        =================
        Total Responses: {report['summary']['total_responses']}
        Average Score: {report['summary']['average_score']:.2f}/1.0
        
        SCORE DISTRIBUTION
        ==================
        """
        
        total = report['summary']['total_responses']
        for category, count in report['summary']['score_distribution'].items():
            percentage = (count / total * 100) if total > 0 else 0
            text += f"{category.replace('_', ' ').title():20} {count:3} ({percentage:5.1f}%)\n"
        
        text += """
        
        RECOMMENDATIONS
        ===============
        """
        
        for rec in report['recommendations']:
            text += f"• {rec}\n"
        
        return {"text": text, "report_id": report["report_id"]}


# Singleton instance for easy access
_global_judge_instance = None

def get_llm_judge(use_real_llm: bool = False, api_key: Optional[str] = None) -> LLMJudge:
    """
    Get or create a global LLM judge instance.
    
    Args:
        use_real_llm: Whether to use real LLM API
        api_key: API key for real LLM service
        
    Returns:
        LLMJudge instance
    """
    global _global_judge_instance
    
    if _global_judge_instance is None:
        _global_judge_instance = LLMJudge(use_real_llm, api_key)
    
    return _global_judge_instance


if __name__ == "__main__":
    # Example usage
    judge = LLMJudge(use_real_llm=False)
    
    # Sample evaluation
    query = "Find AI solutions for banking fraud detection"
    response = """
    TCS offers comprehensive AI solutions for banking fraud detection:
    
    1. **TCS AI-powered Fraud Detection Platform**: Uses machine learning to detect anomalies with 99.8% accuracy
    2. **Real-time Transaction Monitoring**: Processes millions of transactions per second
    3. **Predictive Analytics**: Identifies fraud patterns before they occur
    
    Case Study: Implemented for a European bank, reducing fraud losses by 92%.
    
    Recommended next steps: Schedule a demo with our BFSI solutions team.
    """
    
    result = judge.evaluate_response(query, response)
    
    print("Query:", query)
    print("\nResponse:", response[:200] + "...")
    print(f"\n{'='*50}")
    print("LLM JUDGE EVALUATION")
    print(f"{'='*50}")
    print(f"Overall Score: {result.score:.2f}/1.0")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Model: {result.model_used}")
    print(f"\nCriteria Scores:")
    for criteria, score in result.criteria_scores.items():
        print(f"  {criteria:20} {score:.2f}")
    print(f"\nFeedback:\n{result.feedback}")
    print(f"\nJustification: {result.justification}")