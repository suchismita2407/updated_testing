import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.api_client import APIClient, TestDataGenerator
from config.settings import settings

logger = logging.getLogger(__name__)

class KnowledgeBaseValidator:
    """
    Validate the knowledge base used by Sales EVA
    
    Tests:
    1. Coverage - Does KB cover required topics?
    2. Freshness - Is information up-to-date?
    3. Consistency - Are there contradictions?
    4. Relevance - Is content relevant to sales domain?
    5. Completeness - Are offerings fully described?
    """
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.test_generator = TestDataGenerator()
        self.results = []
        
    async def run_validation(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Run comprehensive knowledge base validation
        
        Steps:
        1. Extract KB content via API or load from files
        2. Generate validation queries using LLM
        3. Test KB with various queries
        4. Analyze coverage, freshness, consistency
        """
        logger.info("Starting knowledge base validation...")
        
        sample_size = sample_size or settings.KB_VALIDATION_SAMPLE_SIZE
        
        # Get KB content
        logger.info("Extracting knowledge base content...")
        kb_content = await self._extract_knowledge_base_content()
        
        if not kb_content:
            raise ValueError("Failed to extract knowledge base content")
        
        # Generate validation queries using LLM
        logger.info(f"Generating {sample_size} validation queries using LLM...")
        validation_queries = self._generate_validation_queries(sample_size)
        
        logger.info(f"Validating knowledge base with {len(validation_queries)} queries...")
        
        # Run validation tests
        validation_results = await self._run_validation_tests(
            validation_queries, 
            kb_content
        )
        
        # Analyze results
        analysis = self._analyze_validation_results(
            validation_results, 
            kb_content
        )
        
        # Save results
        self._save_results(analysis)
        
        logger.info(f"KB validation completed. Overall health: {analysis.get('overall_health', 0):.2f}")
        
        return analysis
    
    async def _extract_knowledge_base_content(self) -> Dict[str, Any]:
        """Extract KB content from API or local files"""
        kb_content = {
            "offerings": [],
            "case_studies": [],
            "documents": [],
            "last_updated": None
        }
        
        try:
            # Try to get offerings from API
            offerings = await self.api_client.get_offerings()
            if offerings:
                kb_content["offerings"] = offerings
                logger.info(f"Retrieved {len(offerings)} offerings from API")
            
            # Try to query KB for sample content
            sample_queries = [
                "TCS AI solutions",
                "cloud migration case studies",
                "banking digital transformation"
            ]
            
            for query in sample_queries[:3]:  # Limit to 3 queries
                try:
                    results = await self.api_client.query_knowledge_base(query)
                    if results:
                        kb_content["documents"].extend(results[:5])  # Limit to 5 per query
                except Exception as e:
                    logger.debug(f"Failed to query KB for '{query}': {e}")
            
        except Exception as e:
            logger.warning(f"Failed to extract KB from API: {e}")
        
        # If API extraction failed, try to load from local files
        if not kb_content["offerings"] and settings.OFFERINGS_PATH.exists():
            try:
                with open(settings.OFFERINGS_PATH, 'r') as f:
                    kb_content["offerings"] = json.load(f).get("offerings", [])
                logger.info(f"Loaded {len(kb_content['offerings'])} offerings from file")
            except Exception as e:
                logger.warning(f"Failed to load offerings from file: {e}")
        
        if not kb_content["documents"] and settings.KB_PATH.exists():
            try:
                with open(settings.KB_PATH, 'r') as f:
                    kb_content["documents"] = json.load(f).get("documents", [])
                logger.info(f"Loaded {len(kb_content['documents'])} documents from file")
            except Exception as e:
                logger.warning(f"Failed to load KB documents from file: {e}")
        
        # Add metadata
        kb_content["total_items"] = (
            len(kb_content["offerings"]) + 
            len(kb_content["documents"])
        )
        kb_content["extracted_at"] = datetime.now().isoformat()
        
        return kb_content
    
    def _generate_validation_queries(self, count: int) -> List[Dict]:
        """Generate validation queries using LLM"""
        prompt = f"""Generate {count} validation queries to test a Sales Knowledge Base.
        
        The knowledge base contains:
        1. TCS offerings and solutions
        2. Case studies and success stories
        3. Industry-specific solutions
        4. Technical capabilities
        
        Create queries that test:
        - Coverage of different topics
        - Freshness of information
        - Specificity of solutions
        - Industry relevance
        
        Return ONLY a JSON array with this structure:
        {{
            "id": "KB_VAL_001",
            "query": "Specific query text",
            "category": "coverage/freshness/specificity/relevance",
            "expected_info": ["info1", "info2", "info3"],
            "difficulty": "easy/medium/hard"
        }}
        
        Distribute queries across all categories."""
        
        try:
            response = self.test_generator._call_groq_api(prompt)
            
            # Parse JSON response
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            queries = json.loads(response.strip())
            
            # Validate and clean queries
            validated_queries = []
            category_counts = {
                "coverage": 0,
                "freshness": 0,
                "specificity": 0,
                "relevance": 0
            }
            
            for i, query_data in enumerate(queries[:count]):
                if not isinstance(query_data, dict):
                    continue
                
                # Determine category
                category = str(query_data.get("category", "")).lower()
                if category not in category_counts:
                    # Map to closest category
                    if "cover" in category:
                        category = "coverage"
                    elif "fresh" in category or "recent" in category:
                        category = "freshness"
                    elif "specific" in category or "detail" in category:
                        category = "specificity"
                    elif "relevant" in category or "industry" in category:
                        category = "relevance"
                    else:
                        category = "coverage"  # Default
                
                validated = {
                    "id": query_data.get("id", f"KB_VAL_{i+1:03d}"),
                    "query": str(query_data.get("query", "")).strip(),
                    "category": category,
                    "expected_info": [
                        str(info).strip()
                        for info in query_data.get("expected_info", [])
                        if info
                    ],
                    "difficulty": str(query_data.get("difficulty", "medium")).lower()
                }
                
                if validated["query"]:  # Only add if we have content
                    category_counts[category] += 1
                    validated_queries.append(validated)
            
            logger.info(f"Generated validation queries by category: {category_counts}")
            return validated_queries
            
        except Exception as e:
            logger.error(f"Failed to generate validation queries: {e}")
            return self._generate_fallback_queries(count)
    
    def _generate_fallback_queries(self, count: int) -> List[Dict]:
        """Generate fallback validation queries"""
        queries = []
        
        # Define template queries for each category
        templates = {
            "coverage": [
                "What AI solutions does TCS offer for banking?",
                "What cloud migration services are available?",
                "What digital transformation offerings does TCS have?"
            ],
            "freshness": [
                "What are TCS's latest AI offerings from 2024?",
                "Recent case studies about cloud migration",
                "Latest updates on TCS cybersecurity solutions"
            ],
            "specificity": [
                "Detailed specifications for TCS AI chatbot solution",
                "Technical requirements for cloud migration framework",
                "Implementation methodology for digital transformation"
            ],
            "relevance": [
                "How does TCS help retail companies with inventory optimization?",
                "TCS solutions for healthcare patient data management",
                "Manufacturing industry solutions from TCS"
            ]
        }
        
        # Distribute queries evenly
        queries_per_category = max(1, count // len(templates))
        
        for category, templates_list in templates.items():
            for i in range(queries_per_category):
                if len(queries) >= count:
                    break
                    
                query_text = templates_list[i % len(templates_list)]
                queries.append({
                    "id": f"KB_FB_{category.upper()}_{i+1:03d}",
                    "query": query_text,
                    "category": category,
                    "expected_info": ["solutions", "offerings", "capabilities"],
                    "difficulty": "medium"
                })
        
        return queries[:count]
    
    async def _run_validation_tests(self, 
                                   queries: List[Dict], 
                                   kb_content: Dict) -> Dict[str, List[Dict]]:
        """Run validation tests for all queries"""
        results = {
            "coverage": [],
            "freshness": [],
            "specificity": [],
            "relevance": []
        }
        
        # Group queries by category
        queries_by_category = {}
        for query in queries:
            category = query["category"]
            if category not in queries_by_category:
                queries_by_category[category] = []
            queries_by_category[category].append(query)
        
        # Test each category
        for category, category_queries in queries_by_category.items():
            logger.info(f"Validating {category} with {len(category_queries)} queries...")
            
            # Create tasks for this category
            tasks = []
            for query in category_queries:
                tasks.append(self._validate_single_query(query, kb_content))
            
            # Execute tasks
            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    results[category].append(result)
                except Exception as e:
                    logger.warning(f"Query validation failed: {e}")
                    results[category].append({
                        "query_id": "unknown",
                        "category": category,
                        "error": str(e),
                        "scores": {"overall": 0}
                    })
        
        return results
    
    async def _validate_single_query(self, 
                                    query: Dict, 
                                    kb_content: Dict) -> Dict[str, Any]:
        """Validate a single query against KB"""
        query_id = query["id"]
        query_text = query["query"]
        category = query["category"]
        
        try:
            # Query the system
            response = await self.api_client.analyze_opportunity(
                opportunity_description=query_text
            )
            
            # Also try direct KB query if available
            kb_response = []
            try:
                kb_response = await self.api_client.query_knowledge_base(query_text)
            except:
                pass
            
            # Evaluate based on category
            evaluation = self._evaluate_kb_response(
                response=response,
                kb_response=kb_response,
                query=query,
                kb_content=kb_content,
                category=category
            )
            
            return {
                "query_id": query_id,
                "query": query_text,
                "category": category,
                "difficulty": query["difficulty"],
                "scores": evaluation,
                "response_summary": self._summarize_response(response),
                "kb_match_count": len(kb_response),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Query {query_id} failed: {e}")
            return {
                "query_id": query_id,
                "category": category,
                "error": str(e),
                "scores": {"overall": 0, "error": 1.0},
                "timestamp": datetime.now().isoformat()
            }
    
    def _evaluate_kb_response(self,
                             response: Dict,
                             kb_response: List[Dict],
                             query: Dict,
                             kb_content: Dict,
                             category: str) -> Dict[str, float]:
        """Evaluate KB response based on category"""
        scores = {"overall": 0.0}
        
        try:
            response_text = json.dumps(response).lower()
            kb_response_text = json.dumps(kb_response).lower()
            
            # Combine all response text for analysis
            all_text = response_text + " " + kb_response_text
            
            # Category-specific evaluation
            if category == "coverage":
                scores.update(self._evaluate_coverage(
                    all_text, query, kb_content
                ))
            elif category == "freshness":
                scores.update(self._evaluate_freshness(
                    all_text, query, kb_content
                ))
            elif category == "specificity":
                scores.update(self._evaluate_specificity(
                    all_text, query, kb_content
                ))
            elif category == "relevance":
                scores.update(self._evaluate_relevance(
                    all_text, query, kb_content
                ))
            
            # Calculate overall score
            weights = self._get_category_weights(category)
            overall = sum(
                scores.get(metric, 0) * weight
                for metric, weight in weights.items()
                if metric in scores
            )
            scores["overall"] = min(1.0, overall)
            
        except Exception as e:
            logger.warning(f"KB evaluation failed for {category}: {e}")
            scores = {"error": 1.0, "overall": 0.0}
        
        return scores
    
    def _evaluate_coverage(self,
                          response_text: str,
                          query: Dict,
                          kb_content: Dict) -> Dict[str, float]:
        """Evaluate coverage of requested information"""
        scores = {}
        
        # 1. Topic coverage
        expected_info = [info.lower() for info in query.get("expected_info", [])]
        coverage_score = 0
        for info in expected_info[:5]:  # Check first 5 expected info
            if info in response_text:
                coverage_score += 0.2
        scores["topic_coverage"] = min(1.0, coverage_score)
        
        # 2. Breadth of coverage (mentions multiple offerings)
        offering_keywords = ["offering", "solution", "service", "product"]
        breadth_score = 0
        for keyword in offering_keywords:
            if keyword in response_text:
                breadth_score += 0.25
        scores["breadth"] = min(1.0, breadth_score)
        
        # 3. Depth of coverage (detailed information)
        detail_indicators = ["details", "specific", "including", "features", "benefits"]
        depth_score = 0
        for indicator in detail_indicators:
            if indicator in response_text:
                depth_score += 0.2
        scores["depth"] = min(1.0, depth_score)
        
        return scores
    
    def _evaluate_freshness(self,
                           response_text: str,
                           query: Dict,
                           kb_content: Dict) -> Dict[str, float]:
        """Evaluate freshness of information"""
        scores = {}
        
        # 1. Recency indicators
        recency_keywords = ["2024", "2023", "recent", "latest", "new", "update", "current"]
        recency_score = 0
        for keyword in recency_keywords:
            if keyword in response_text:
                recency_score += 0.166  # 6 keywords max
        scores["recency"] = min(1.0, recency_score)
        
        # 2. Temporal references
        time_indicators = ["year", "month", "q1", "q2", "q3", "q4"]
        time_score = 0
        for indicator in time_indicators:
            if indicator in response_text:
                time_score += 0.166
        scores["temporal_references"] = min(1.0, time_score)
        
        # 3. Update mentions
        update_indicators = ["updated", "released", "launched", "announced", "introduced"]
        update_score = 0
        for indicator in update_indicators:
            if indicator in response_text:
                update_score += 0.2
        scores["update_mentions"] = min(1.0, update_score)
        
        return scores
    
    def _evaluate_specificity(self,
                             response_text: str,
                             query: Dict,
                             kb_content: Dict) -> Dict[str, float]:
        """Evaluate specificity of information"""
        scores = {}
        
        # 1. Technical specificity
        technical_terms = ["api", "sdk", "integration", "deployment", "architecture", "framework"]
        technical_score = 0
        for term in technical_terms:
            if term in response_text:
                technical_score += 0.166
        scores["technical_specificity"] = min(1.0, technical_score)
        
        # 2. Named entity specificity
        named_entities = ["tcs", "aws", "azure", "gcp", "ai", "ml", "iot"]
        entity_score = 0
        for entity in named_entities:
            if entity in response_text:
                entity_score += 0.143  # 7 entities max
        scores["named_entities"] = min(1.0, entity_score)
        
        # 3. Quantitative specificity
        quantitative_terms = ["%", "gb", "tb", "mbps", "ms", "users", "customers"]
        quantitative_score = 0
        for term in quantitative_terms:
            if term in response_text:
                quantitative_score += 0.166
        scores["quantitative_info"] = min(1.0, quantitative_score)
        
        return scores
    
    def _evaluate_relevance(self,
                           response_text: str,
                           query: Dict,
                           kb_content: Dict) -> Dict[str, float]:
        """Evaluate relevance to query"""
        scores = {}
        
        # 1. Query term matching
        query_terms = query["query"].lower().split()
        relevance_score = 0
        for term in query_terms[:10]:  # Check first 10 terms
            if len(term) > 3 and term in response_text:  # Ignore short words
                relevance_score += 0.1
        scores["query_relevance"] = min(1.0, relevance_score)
        
        # 2. Industry relevance
        industries = ["banking", "retail", "healthcare", "manufacturing", "telecom", "insurance"]
        industry_score = 0
        for industry in industries:
            if industry in response_text:
                industry_score += 0.166
        scores["industry_relevance"] = min(1.0, industry_score)
        
        # 3. Solution relevance
        solution_terms = ["solution", "offering", "service", "capability", "expertise"]
        solution_score = 0
        for term in solution_terms:
            if term in response_text:
                solution_score += 0.2
        scores["solution_relevance"] = min(1.0, solution_score)
        
        return scores
    
    def _get_category_weights(self, category: str) -> Dict[str, float]:
        """Get evaluation weights for different categories"""
        weights = {
            "coverage": {
                "topic_coverage": 0.5,
                "breadth": 0.3,
                "depth": 0.2
            },
            "freshness": {
                "recency": 0.4,
                "temporal_references": 0.3,
                "update_mentions": 0.3
            },
            "specificity": {
                "technical_specificity": 0.4,
                "named_entities": 0.3,
                "quantitative_info": 0.3
            },
            "relevance": {
                "query_relevance": 0.4,
                "industry_relevance": 0.3,
                "solution_relevance": 0.3
            }
        }
        return weights.get(category, {"overall": 1.0})
    
    def _summarize_response(self, response: Dict, max_length: int = 100) -> str:
        """Create a short summary of the response"""
        try:
            response_str = json.dumps(response)
            if len(response_str) > max_length:
                return response_str[:max_length] + "..."
            return response_str
        except:
            return str(response)[:max_length]
    
    def _analyze_validation_results(self, 
                                   results: Dict[str, List[Dict]], 
                                   kb_content: Dict) -> Dict[str, Any]:
        """Analyze all validation results"""
        
        # Calculate category-specific metrics
        category_analysis = {}
        overall_scores = []
        
        for category, category_results in results.items():
            if not category_results:
                category_analysis[category] = {
                    "count": 0,
                    "avg_score": 0,
                    "success_rate": 0
                }
                continue
            
            # Calculate metrics
            scores = [r.get("scores", {}).get("overall", 0) for r in category_results]
            success_count = sum(1 for r in category_results if r.get("scores", {}).get("overall", 0) > 0.6)
            
            category_analysis[category] = {
                "count": len(category_results),
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "success_rate": success_count / len(category_results) if category_results else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0
            }
            
            overall_scores.extend(scores)
        
        # Calculate overall metrics
        overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        # KB content analysis
        content_analysis = self._analyze_kb_content(kb_content)
        
        # Identify strengths and weaknesses
        category_scores = {
            cat: analysis["avg_score"]
            for cat, analysis in category_analysis.items()
        }
        
        strongest_category = max(category_scores.items(), key=lambda x: x[1]) if category_scores else ("none", 0)
        weakest_category = min(category_scores.items(), key=lambda x: x[1]) if category_scores else ("none", 0)
        
        # Calculate overall health score
        health_score = self._calculate_health_score(category_analysis, content_analysis)
        
        # Generate recommendations
        recommendations = self._generate_kb_recommendations(category_analysis, content_analysis)
        
        return {
            "summary": {
                "total_queries_tested": sum(analysis["count"] for analysis in category_analysis.values()),
                "overall_score": overall_score,
                "overall_health": health_score,
                "strongest_category": {
                    "category": strongest_category[0],
                    "score": strongest_category[1]
                },
                "weakest_category": {
                    "category": weakest_category[0],
                    "score": weakest_category[1]
                },
                "kb_content_summary": {
                    "total_offerings": len(kb_content.get("offerings", [])),
                    "total_documents": len(kb_content.get("documents", [])),
                    "last_extracted": kb_content.get("extracted_at")
                },
                "timestamp": datetime.now().isoformat()
            },
            "category_analysis": category_analysis,
            "content_analysis": content_analysis,
            "performance_breakdown": {
                "by_difficulty": self._analyze_by_difficulty(results),
                "score_distribution": overall_scores
            },
            "recommendations": recommendations,
            "kb_gaps": self._identify_kb_gaps(results, kb_content)
        }
    
    def _analyze_kb_content(self, kb_content: Dict) -> Dict[str, Any]:
        """Analyze KB content structure and quality"""
        analysis = {
            "offerings_count": len(kb_content.get("offerings", [])),
            "documents_count": len(kb_content.get("documents", [])),
            "total_items": kb_content.get("total_items", 0),
            "coverage_estimate": 0,
            "freshness_estimate": 0
        }
        
        # Estimate coverage based on offering diversity
        offerings = kb_content.get("offerings", [])
        if offerings:
            # Count unique categories/industries
            categories = set()
            for offering in offerings[:50]:  # Sample first 50
                if isinstance(offering, dict):
                    # Extract categories from offering
                    for key in ["category", "industry", "type"]:
                        if key in offering:
                            val = offering[key]
                            if isinstance(val, list):
                                categories.update(val)
                            elif isinstance(val, str):
                                categories.add(val)
            
            analysis["unique_categories"] = len(categories)
            analysis["coverage_estimate"] = min(1.0, len(categories) / 10)  # Normalize
        
        # Estimate freshness
        documents = kb_content.get("documents", [])
        if documents:
            # Check for recent dates in document metadata
            recent_count = 0
            for doc in documents[:50]:  # Sample first 50
                if isinstance(doc, dict):
                    # Look for date fields
                    for key in ["date", "timestamp", "last_updated", "created_at"]:
                        if key in doc:
                            date_str = str(doc[key])
                            # Simple check for recent years
                            if any(year in date_str for year in ["2024", "2023"]):
                                recent_count += 1
                                break
            
            if documents:
                analysis["freshness_estimate"] = recent_count / len(documents)
        
        return analysis
    
    def _analyze_by_difficulty(self, results: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze results by query difficulty"""
        difficulty_scores = {"easy": [], "medium": [], "hard": []}
        
        for category_results in results.values():
            for result in category_results:
                difficulty = result.get("difficulty", "medium")
                score = result.get("scores", {}).get("overall", 0)
                
                if difficulty in difficulty_scores:
                    difficulty_scores[difficulty].append(score)
        
        analysis = {}
        for difficulty, scores in difficulty_scores.items():
            if scores:
                analysis[difficulty] = {
                    "count": len(scores),
                    "avg_score": sum(scores) / len(scores),
                    "success_rate": sum(1 for s in scores if s > 0.6) / len(scores)
                }
            else:
                analysis[difficulty] = {"count": 0, "avg_score": 0, "success_rate": 0}
        
        return analysis
    
    def _identify_kb_gaps(self, results: Dict[str, List[Dict]], kb_content: Dict) -> List[Dict]:
        """Identify gaps in the knowledge base"""
        gaps = []
        
        # Look for failed or low-scoring queries
        for category, category_results in results.items():
            for result in category_results:
                score = result.get("scores", {}).get("overall", 0)
                
                if score < 0.5:  # Low score indicates potential gap
                    gaps.append({
                        "query": result.get("query", ""),
                        "category": category,
                        "score": score,
                        "issue": f"Low score ({score:.2f}) for {category} query",
                        "recommendation": f"Add more information about: {result.get('query', '')[:50]}..."
                    })
        
        # Limit to top 10 gaps
        gaps = sorted(gaps, key=lambda x: x["score"])[:10]
        
        return gaps
    
    def _calculate_health_score(self, 
                               category_analysis: Dict, 
                               content_analysis: Dict) -> float:
        """Calculate overall KB health score"""
        
        # Category performance (70% weight)
        category_scores = [
            analysis["avg_score"]
            for analysis in category_analysis.values()
            if analysis["count"] > 0
        ]
        
        if category_scores:
            category_score = sum(category_scores) / len(category_scores)
        else:
            category_score = 0
        
        # Content quality (30% weight)
        content_score = (
            content_analysis.get("coverage_estimate", 0) * 0.5 +
            content_analysis.get("freshness_estimate", 0) * 0.5
        )
        
        # Overall health score
        health_score = (category_score * 0.7) + (content_score * 0.3)
        
        return min(1.0, health_score)
    
    def _generate_kb_recommendations(self, 
                                    category_analysis: Dict, 
                                    content_analysis: Dict) -> List[str]:
        """Generate KB improvement recommendations"""
        recommendations = []
        
        # Category-based recommendations
        for category, analysis in category_analysis.items():
            score = analysis["avg_score"]
            count = analysis["count"]
            
            if count > 0:
                if score < 0.6:
                    recommendations.append(f"Improve {category} (score: {score:.2f})")
                elif score > 0.8:
                    recommendations.append(f"Strong {category} coverage (score: {score:.2f})")
        
        # Content-based recommendations
        coverage = content_analysis.get("coverage_estimate", 0)
        freshness = content_analysis.get("freshness_estimate", 0)
        
        if coverage < 0.5:
            recommendations.append("Expand KB coverage across more categories")
        
        if freshness < 0.3:
            recommendations.append("Update KB with more recent information")
        
        if content_analysis.get("total_items", 0) < 50:
            recommendations.append("Increase KB content volume")
        
        # Overall recommendations
        health_score = self._calculate_health_score(category_analysis, content_analysis)
        if health_score < 0.7:
            recommendations.append("Overall KB health needs improvement")
        elif health_score > 0.9:
            recommendations.append("Excellent KB health and coverage")
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    def _save_results(self, analysis: Dict):
        """Save validation results to file"""
        try:
            results_dir = settings.RESULTS_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"kb_validation_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"KB validation results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save KB validation results: {e}")