# sales_eva_testing_framework/src/sales_eva_client.py
import httpx
import asyncio
import json
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)

class SalesEVAServiceClient:
    """Client specifically for your Sales EVA Flask + Gradio service"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SALES_EVA_API_URL.rstrip('/')
        self.auth_token = None
        self.user_info = None
        
        # Configure HTTP client
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Sales-EVA-Testing-Framework/1.0",
                "Content-Type": "application/json"
            }
        )
    
    async def login(self, username: str, password: str) -> bool:
        """Login to Sales EVA service"""
        try:
            response = await self.client.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_info = data.get("user")
                # Store any auth token if provided
                self.auth_token = data.get("token")
                logger.info(f"Logged in as {username}")
                return True
            else:
                logger.error(f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def analyze_opportunity(self, opportunity_description: str) -> Dict[str, Any]:
        """
        Analyze opportunity using Sales EVA service
        This simulates the Gradio functionality via API
        """
        try:
            # First, ensure we're logged in (use demo credentials)
            if not self.user_info:
                await self.login("sales1", "demo123")
            
            # Create opportunity in the system
            payload = {
                "title": f"Test Opportunity - {datetime.now().strftime('%H:%M:%S')}",
                "description": opportunity_description,
                "client_name": "Test Client",
                "value": 1000000,
                "sales_person": self.user_info.get("username", "sales1")
            }
            
            response = await self.client.post(
                f"{self.base_url}/opportunities",
                json=payload
            )
            
            if response.status_code == 201:
                # Opportunity created successfully
                opportunity_id = response.json().get("id")
                
                # Now simulate analysis - in real scenario, this would be done via Gradio
                # For now, we'll create a mock analysis
                analysis_result = {
                    "status": "analyzed",
                    "opportunity_id": opportunity_id,
                    "analysis": f"Analysis of: {opportunity_description[:100]}...",
                    "offerings_matched": [
                        {
                            "title": "TCS Generative AI Enterprise Suite",
                            "match_score": 0.85,
                            "description": "Comprehensive platform for building, deploying and managing GenAI applications."
                        }
                    ],
                    "gap_analysis": {
                        "requirements_identified": 5,
                        "matched_count": 3,
                        "gap_count": 2,
                        "coverage_percentage": 60.0
                    },
                    "recommendations": [
                        "Consider TCS Generative AI Suite for AI requirements",
                        "Explore cloud migration options for infrastructure needs"
                    ]
                }
                
                return analysis_result
            else:
                logger.error(f"Failed to create opportunity: {response.status_code}")
                return {"error": f"Failed to analyze opportunity: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Opportunity analysis error: {e}")
            return {"error": str(e)}
    
    async def chat_with_sales_eva(self, message: str) -> Dict[str, Any]:
        """
        Simulate chat with Sales EVA (would normally be via Gradio)
        For testing, we'll simulate a response
        """
        try:
            # Simulate RAG search for context
            rag_response = await self.client.post(
                f"{self.base_url}/api/rag/search",
                json={"query": message}
            )
            
            rag_results = []
            if rag_response.status_code == 200:
                rag_results = rag_response.json().get("results", [])
            
            # Create simulated chat response
            chat_response = {
                "query": message,
                "response": f"I received your query about '{message[:50]}...'. Based on our knowledge base, I can help with relevant offerings.",
                "rag_context": rag_results[:2] if rag_results else [],
                "timestamp": datetime.now().isoformat()
            }
            
            return chat_response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "query": message,
                "response": f"I understand you're asking about: {message}. As your sales advisor, I recommend checking our offerings database.",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> bool:
        """Check if Sales EVA API is accessible"""
        try:
            response = await self.client.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    async def get_opportunities(self) -> List[Dict]:
        """Get opportunities from Sales EVA"""
        try:
            response = await self.client.get(f"{self.base_url}/opportunities")
            if response.status_code == 200:
                return response.json().get("opportunities", [])
        except Exception as e:
            logger.warning(f"Could not fetch opportunities: {e}")
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