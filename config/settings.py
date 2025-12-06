import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Settings:
    """Configuration settings for the testing framework"""
    
    # Project paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    RESULTS_DIR = BASE_DIR / "test_results"
    LOGS_DIR = BASE_DIR / "logs"
    
    # API Configuration
    # API Configuration
    SALES_EVA_API_URL = os.getenv("SALES_EVA_API_URL", "http://localhost:5000")
    SALES_EVA_API_KEY = os.getenv("SALES_EVA_API_KEY", "")
    
    # LLM Configuration (for test data generation)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://genailab.tcs.in")
    LLM_MODEL = os.getenv("LLM_MODEL", "azure_ai/genailab-maas-DeepSeek-V3-0324")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-9VUkstxqIO9V1WPe03d6PQ")  # Your provided key
    # Testing Framework
    TESTING_MODE = os.getenv("TESTING_MODE", "development")
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
    
    # Test Parameters
    PROMPT_TEST_COUNT = int(os.getenv("PROMPT_TEST_COUNT", "50"))
    AGENT_TEST_COUNT = int(os.getenv("AGENT_TEST_COUNT", "20"))
    E2E_TEST_COUNT = int(os.getenv("E2E_TEST_COUNT", "5"))
    KB_VALIDATION_SAMPLE_SIZE = int(os.getenv("KB_VALIDATION_SAMPLE_SIZE", "50"))
    
    # Data Paths
    TEST_DATA_PATH = Path(os.getenv("TEST_DATA_PATH", "./data/test_cases.json"))
    OFFERINGS_PATH = Path(os.getenv("OFFERINGS_PATH", "./data/offerings.json"))
    KB_PATH = Path(os.getenv("KB_PATH", "./data/knowledge_base.json"))
    RESULTS_PATH = Path(os.getenv("RESULTS_PATH", "./test_results"))
    
    # Evaluation Services
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    DEEPEVAL_API_KEY = os.getenv("DEEPEVAL_API_KEY", "")
    DEEPEVAL_PROJECT_NAME = os.getenv("DEEPEVAL_PROJECT_NAME", "sales_eva_testing")
    
    # Dashboard
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))
    DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = Path(os.getenv("LOG_FILE", "./logs/testing_framework.log"))
    
    # Validation
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        required_settings = [
            "SALES_EVA_API_URL"
        ]
        
        for setting in required_settings:
            if not getattr(cls, setting):
                raise ValueError(f"Required setting {setting} is not configured")
        
        # Create directories if they don't exist
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.RESULTS_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        
        return True
    
    @classmethod
    def get_endpoints(cls) -> Dict[str, str]:
        """Get API endpoint URLs for Sales EVA service"""
        base_url = cls.SALES_EVA_API_URL.rstrip('/')
        
        # These are the actual endpoints from your Flask app.py
        return {
            "login": f"{base_url}/login",
            "register": f"{base_url}/register",
            "profile": f"{base_url}/profile",
            "opportunities": f"{base_url}/opportunities",
            "rag_search": f"{base_url}/api/rag/search",
            "health": f"{base_url}/",  # Root endpoint for health check
            
            # For backward compatibility with existing tester code
            "analyze": f"{base_url}/opportunities",  # POST to opportunities for analysis
            "offerings": f"{base_url}/opportunities",  # GET from opportunities for offerings
            "kb_query": f"{base_url}/api/rag/search",  # RAG search
        }
    
    @classmethod
    def get_test_config(cls) -> Dict[str, Any]:
        """Get test configuration"""
        return {
            "mode": cls.TESTING_MODE,
            "max_workers": cls.MAX_WORKERS,
            "timeout": cls.REQUEST_TIMEOUT,
            "max_retries": cls.MAX_RETRIES,
            "prompt_test_count": cls.PROMPT_TEST_COUNT,
            "agent_test_count": cls.AGENT_TEST_COUNT,
            "e2e_test_count": cls.E2E_TEST_COUNT
        }
    
    # LLM Configuration
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Get LLM configuration for test generation"""
        return {
            "llm_base_url": cls.LLM_BASE_URL,
            "llm_model": cls.LLM_MODEL,
            "llm_api_key": cls.LLM_API_KEY,
            "enable_llm_generation": bool(cls.LLM_API_KEY)
        }

# Create settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate()
    print("✅ Settings validated successfully")
except ValueError as e:
    print(f"❌ Settings validation failed: {e}")
    raise