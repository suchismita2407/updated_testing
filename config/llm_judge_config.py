"""
Configuration for LLM Judge module.
"""

import os
from typing import Dict, Any

class LLMJudgeConfig:
    """Configuration for LLM Judge"""
    
    # Mode settings
    USE_REAL_LLM = False  # Set to True to use actual LLM API
    DUMMY_MODE = True     # Set to False to disable dummy mode
    
    # API settings (for real mode)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE = 0.1
    OPENAI_MAX_TOKENS = 1000
    
    # Dummy mode settings
    DUMMY_MODEL_NAME = "gpt-4-turbo-preview-simulated"
    DUMMY_RESPONSE_TIME_MS = 150  # Simulated response time
    
    # Evaluation criteria weights
    CRITERIA_WEIGHTS = {
        "relevance": 0.25,
        "accuracy": 0.20,
        "completeness": 0.15,
        "actionability": 0.15,
        "professionalism": 0.10,
        "tcs_specificity": 0.10,
        "structure": 0.05
    }
    
    # Score thresholds
    SCORE_THRESHOLDS = {
        "excellent": 0.8,
        "good": 0.7,
        "satisfactory": 0.6,
        "needs_improvement": 0.0
    }
    
    # Feedback templates
    FEEDBACK_TEMPLATES = {
        "excellent": "EXCELLENT - Response effectively addresses the query with comprehensive, actionable TCS solutions.",
        "good": "GOOD - Response is mostly effective with minor areas for improvement.",
        "satisfactory": "SATISFACTORY - Addresses the query adequately but could be enhanced.",
        "needs_improvement": "NEEDS IMPROVEMENT - Significant enhancements needed for sales effectiveness."
    }
    
    # Industry-specific keywords for evaluation
    INDUSTRY_KEYWORDS = {
        "banking": ["bank", "financial", "fraud", "transaction", "compliance"],
        "healthcare": ["medical", "hospital", "patient", "diagnosis", "fda"],
        "retail": ["inventory", "supply chain", "customer", "e-commerce", "logistics"],
        "manufacturing": ["iot", "predictive", "maintenance", "quality", "automation"]
    }
    
    # TCS-specific terms
    TCS_TERMS = [
        "tcs", "tata consultancy", "ignio", "cbps", "mastercraft",
        "dexam", "optumera", "quartz", "bancs", "jile"
    ]
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get complete configuration as dictionary"""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("__") and not callable(value)
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        try:
            # Check weights sum to 1
            weights_sum = sum(cls.CRITERIA_WEIGHTS.values())
            if abs(weights_sum - 1.0) > 0.001:
                raise ValueError(f"Criteria weights must sum to 1.0, got {weights_sum}")
            
            # Check thresholds are in order
            thresholds = list(cls.SCORE_THRESHOLDS.values())
            if not all(thresholds[i] >= thresholds[i+1] for i in range(len(thresholds)-1)):
                raise ValueError("Score thresholds must be in descending order")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False

# Create config instance
config = LLMJudgeConfig()

if __name__ == "__main__":
    # Test configuration
    print("LLM Judge Configuration:")
    print("=" * 50)
    
    for key, value in config.get_config().items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        elif isinstance(value, list):
            print(f"\n{key}:")
            for item in value[:5]:  # Show first 5 items
                print(f"  • {item}")
            if len(value) > 5:
                print(f"  ... and {len(value) - 5} more")
        else:
            print(f"{key}: {value}")
    
    print("\n" + "=" * 50)
    if config.validate_config():
        print("✅ Configuration validated successfully")
    else:
        print("❌ Configuration validation failed")