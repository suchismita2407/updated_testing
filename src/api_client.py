import httpx
import asyncio
import json
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)

class APIClient:
    """Client to interact with Sales EVA API"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SALES_EVA_API_URL.rstrip('/')
        self.endpoints = settings.get_endpoints()
        
        # Configure HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Sales-EVA-Testing-Framework/1.0",
                "Content-Type": "application/json"
            }
        )
        
        # Add API key if configured
        if settings.SALES_EVA_API_KEY:
            self.client.headers["Authorization"] = f"Bearer {settings.SALES_EVA_API_KEY}"
    
    async def analyze_opportunity(self, 
                                 opportunity_description: str,
                                 prompt_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Send opportunity analysis request to Sales EVA
        """
        payload = {
            "opportunity_description": opportunity_description,
            "timestamp": datetime.now().isoformat()
        }
        
        if prompt_override:
            payload["prompt_override"] = prompt_override
        
        try:
            response = await self.client.post(
                self.endpoints["analyze"],
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed with status {e.response.status_code}: {e}")
            raise Exception(f"API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if API is accessible"""
        try:
            response = await self.client.get(self.endpoints["health"], timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    async def get_offerings(self) -> List[Dict]:
        """Get available offerings from API (if endpoint exists)"""
        try:
            response = await self.client.get(self.endpoints["offerings"], timeout=15)
            if response.status_code == 200:
                return response.json().get("offerings", [])
        except Exception as e:
            logger.warning(f"Could not fetch offerings: {e}")
        return []
    
    async def query_knowledge_base(self, query: str) -> List[Dict]:
        """Query knowledge base (if endpoint exists)"""
        try:
            response = await self.client.post(
                self.endpoints["kb_query"],
                json={"query": query}
            )
            if response.status_code == 200:
                return response.json().get("results", [])
        except Exception as e:
            logger.warning(f"Could not query knowledge base: {e}")
        return []
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def __del__(self):
        """Ensure client is closed on destruction"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
        except:
            pass


class TestDataGenerator:
    """Generate test data using LLM (DeepSeek)"""
    
    def __init__(self):
        self.llm_api_key = settings.LLM_API_KEY
        self.llm_model = settings.LLM_MODEL
        self.llm_base_url = settings.LLM_BASE_URL
        
    def _call_llm_api(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call DeepSeek LLM API"""
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY not configured")
        
        try:
            # Import here to avoid dependency issues
            import httpx
            from langchain_openai import ChatOpenAI
            
            # Create HTTP client
            http_client = httpx.Client(verify=False)
            
            # Initialize LLM
            llm = ChatOpenAI(
                base_url=self.llm_base_url,
                model=self.llm_model,
                api_key=self.llm_api_key,
                http_client=http_client
            )
            
            # Generate response
            response = llm.invoke(prompt)
            
            # Close HTTP client
            http_client.close()
            
            return response.content
            
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            raise
    
    def generate_system_prompts(self, count: int = 100) -> List[Dict]:
        """Generate system prompt variations using LLM"""
        prompt = f"""Generate {count} variations of a system prompt for a Sales Virtual Assistant named "Sales EVA".
        
        The assistant should:
        1. Help sales teams find relevant offerings for customer opportunities
        2. Analyze gaps between customer needs and available solutions
        3. Provide actionable recommendations
        4. Reference case studies and success stories
        5. Be professional, concise, and helpful
        
        Return ONLY a JSON array with this exact structure for each prompt:
        {{
            "id": "PROMPT_001",
            "name": "Descriptive name",
            "content": "Full prompt text here",
            "style": "instructional/role-based/concise/detailed",
            "length": "short/medium/long"
        }}
        
        Make each prompt unique in style, tone, and approach."""
        
        try:
            response = self._call_llm_api(prompt)
            # Parse JSON from response
            lines = response.strip().split('\n')
            json_start = None
            json_end = None
            
            for i, line in enumerate(lines):
                if line.strip().startswith('['):
                    json_start = i
                if line.strip().endswith(']'):
                    json_end = i
            
            if json_start is not None and json_end is not None:
                json_str = '\n'.join(lines[json_start:json_end+1])
                prompts = json.loads(json_str)
                
                # Ensure we have exactly count prompts
                if len(prompts) > count:
                    prompts = prompts[:count]
                elif len(prompts) < count:
                    # Generate more if needed
                    additional = count - len(prompts)
                    more_prompts = self._generate_additional_prompts(additional)
                    prompts.extend(more_prompts)
                
                return prompts
            else:
                raise ValueError("Could not parse JSON from LLM response")
                
        except Exception as e:
            logger.error(f"Failed to generate prompts: {e}")
            # Return fallback prompts
            return self._generate_fallback_prompts(count)
    
    def generate_test_cases(self, count: int = 50) -> List[Dict]:
        """Generate test cases for evaluating the system"""
        prompt = f"""Generate {count} test cases for evaluating a Sales Virtual Assistant.
        
        Each test case should have:
        1. A realistic sales opportunity description
        2. Industry context (banking, retail, healthcare, etc.)
        3. Budget range
        4. Specific requirements
        
        Return ONLY a JSON array with this exact structure:
        {{
            "id": "TEST_001",
            "opportunity": "Detailed opportunity description",
            "industry": "Industry name",
            "budget_range": "$ amount range",
            "requirements": ["req1", "req2", "req3"],
            "complexity": "low/medium/high",
            "expected_output_criteria": [
                "Should match with relevant offerings",
                "Should identify gaps",
                "Should provide case studies"
            ]
        }}"""
        
        try:
            response = self._call_llm_api(prompt)
            
            # Parse JSON (handle potential markdown formatting)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            test_cases = json.loads(response.strip())
            
            # Validate and clean
            validated_cases = []
            for i, tc in enumerate(test_cases[:count]):
                if not isinstance(tc, dict):
                    continue
                
                validated = {
                    "id": tc.get("id", f"TEST_{i+1:03d}"),
                    "opportunity": str(tc.get("opportunity", "")).strip(),
                    "industry": str(tc.get("industry", "general")).strip(),
                    "budget_range": str(tc.get("budget_range", "$1M-$5M")).strip(),
                    "requirements": [str(r).strip() for r in tc.get("requirements", []) if r],
                    "complexity": str(tc.get("complexity", "medium")).strip().lower(),
                    "expected_output_criteria": [str(c).strip() for c in tc.get("expected_output_criteria", []) if c]
                }
                
                if validated["opportunity"]:  # Only add if we have content
                    validated_cases.append(validated)
            
            return validated_cases
            
        except Exception as e:
            logger.error(f"Failed to generate test cases: {e}")
            return self._generate_fallback_test_cases(count)
    
    def _generate_additional_prompts(self, count: int) -> List[Dict]:
        """Generate additional prompts if initial generation was insufficient"""
        base_prompts = [
            {
                "id": f"PROMPT_EXTRA_{i+1:03d}",
                "name": f"Sales Assistant Variant {i+1}",
                "content": f"You are Sales EVA, an AI sales assistant. Your task is to analyze sales opportunities and match them with relevant solutions. Provide clear, actionable recommendations. Style: Professional, Tone: Helpful, Length: Medium",
                "style": "professional",
                "length": "medium"
            }
            for i in range(count)
        ]
        return base_prompts
    
    def _generate_fallback_prompts(self, count: int) -> List[Dict]:
        """Generate fallback prompts if LLM fails"""
        templates = [
            "You are Sales EVA, a virtual sales advisor. Analyze this opportunity and provide relevant solutions.",
            "As Sales EVA, your role is to match customer needs with appropriate offerings. Provide detailed analysis.",
            "Sales EVA here. I'll help you find the best solutions for this opportunity. Let me analyze...",
            "Acting as Sales EVA, I will evaluate this opportunity and suggest relevant offerings with case studies.",
            "I am Sales EVA, an AI sales assistant. My task is to analyze opportunities and identify matching solutions."
        ]
        
        prompts = []
        for i in range(count):
            template = templates[i % len(templates)]
            prompts.append({
                "id": f"PROMPT_FB_{i+1:03d}",
                "name": f"Fallback Prompt {i+1}",
                "content": template,
                "style": "instructional",
                "length": "short"
            })
        
        return prompts
    
    def _generate_fallback_test_cases(self, count: int) -> List[Dict]:
        """Generate fallback test cases if LLM fails"""
        industries = ["Banking", "Retail", "Healthcare", "Manufacturing", "Telecom"]
        budgets = ["$1M-$5M", "$5M-$10M", "$10M-$20M", "$20M-$50M", "$50M+"]
        requirements = [
            ["Cloud Migration", "Digital Transformation", "Security"],
            ["AI Implementation", "Data Analytics", "Automation"],
            ["Customer Experience", "Mobile Apps", "IoT Integration"],
            ["Legacy Modernization", "Cost Optimization", "Scalability"],
            ["Compliance", "Risk Management", "Business Continuity"]
        ]
        
        test_cases = []
        for i in range(count):
            industry = industries[i % len(industries)]
            budget = budgets[i % len(budgets)]
            reqs = requirements[i % len(requirements)]
            
            test_cases.append({
                "id": f"TEST_FB_{i+1:03d}",
                "opportunity": f"{industry} company needs digital transformation including {', '.join(reqs[:2])}. Budget: {budget}. Timeline: 12-18 months.",
                "industry": industry,
                "budget_range": budget,
                "requirements": reqs,
                "complexity": "medium",
                "expected_output_criteria": [
                    "Match with relevant offerings",
                    "Identify potential gaps",
                    "Provide actionable recommendations"
                ]
            })
        
        return test_cases