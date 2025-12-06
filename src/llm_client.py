# sales_eva_testing_framework/src/llm_client.py
import os
import httpx
from typing import Optional, Dict, Any
import logging
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class DeepSeekLLMClient:
    """Client for DeepSeek LLM via TCS GenAI Lab"""
    
    def __init__(self, base_url: Optional[str] = None, 
                 model: Optional[str] = None,
                 api_key: Optional[str] = None):
        
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://genailab.tcs.in")
        self.model = model or os.getenv("LLM_MODEL", "azure_ai/genailab-maas-DeepSeek-V3-0324")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY is required for DeepSeek LLM")
        
        # Create HTTP client with SSL verification disabled
        self.http_client = httpx.Client(verify=False)
        
        # Initialize LangChain ChatOpenAI client
        self.llm = ChatOpenAI(
            base_url=self.base_url,
            model=self.model,
            api_key=self.api_key,
            http_client=self.http_client
        )
        
        logger.info(f"DeepSeek LLM Client initialized: {self.model}")
    
    def generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using DeepSeek LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"DeepSeek LLM generation failed: {e}")
      # sales_eva_testing_framework/src/llm_client.py
import os
import httpx
from typing import Optional, Dict, Any
import logging
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class DeepSeekLLMClient:
    """Client for DeepSeek LLM via TCS GenAI Lab"""
    
    def __init__(self, base_url: Optional[str] = None, 
                 model: Optional[str] = None,
                 api_key: Optional[str] = None):
        
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://genailab.tcs.in")
        self.model = model or os.getenv("LLM_MODEL", "azure_ai/genailab-maas-DeepSeek-V3-0324")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY is required for DeepSeek LLM")
        
        # Create HTTP client with SSL verification disabled
        self.http_client = httpx.Client(verify=False)
        
        # Initialize LangChain ChatOpenAI client
        self.llm = ChatOpenAI(
            base_url=self.base_url,
            model=self.model,
            api_key=self.api_key,
            http_client=self.http_client
        )
        
        logger.info(f"DeepSeek LLM Client initialized: {self.model}")
    
    def generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using DeepSeek LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"DeepSeek LLM generation failed: {e}")
            raise
    
    def __del__(self):
        """Cleanup HTTP client"""
        try:
            self.http_client.close()
        except:
            pass      raise
    
    def __del__(self):
        """Cleanup HTTP client"""
        try:
            self.http_client.close()
        except:
            pass