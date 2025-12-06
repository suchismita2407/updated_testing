# test_deepseek_integration.py
import sys
sys.path.insert(0, '.')

from src.api_client import TestDataGenerator

# Test the LLM integration
try:
    print("Testing DeepSeek LLM integration...")
    
    # Initialize the test data generator
    generator = TestDataGenerator()
    
    # Test with a simple prompt
    print("Testing basic LLM call...")
    test_response = generator._call_llm_api("Hello, please respond with 'LLM is working' if you can read this.")
    print(f"✅ LLM Response: {test_response[:100]}...")
    
    # Test generating a small number of prompts
    print("\nTesting prompt generation...")
    prompts = generator.generate_system_prompts(count=2)
    print(f"✅ Generated {len(prompts)} prompts")
    for prompt in prompts:
        print(f"  - {prompt['name']}: {prompt['content'][:50]}...")
    
    # Test generating test cases
    print("\nTesting test case generation...")
    test_cases = generator.generate_test_cases(count=2)
    print(f"✅ Generated {len(test_cases)} test cases")
    for case in test_cases:
        print(f"  - {case['id']}: {case['opportunity'][:50]}...")
    
    print("\n🎉 All tests passed! DeepSeek LLM integration is working.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()