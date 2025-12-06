# test_sales_eva_service.py
import asyncio
import sys
sys.path.insert(0, '.')

from src.sales_eva_client import SalesEVAServiceClient

async def test_sales_eva_service():
    """Test integration with Sales EVA service"""
    print("Testing Sales EVA Service Integration...")
    
    # Initialize client
    client = SalesEVAServiceClient(base_url="http://localhost:5000")
    
    try:
        # 1. Test health check
        print("\n1. Testing health check...")
        health = await client.health_check()
        print(f"   ✅ Health check: {'PASS' if health else 'FAIL'}")
        
        if not health:
            print("   ❌ Service not running at http://localhost:5000")
            print("   Please start your Sales EVA service with: python app.py")
            return False
        
        # 2. Test login
        print("\n2. Testing login...")
        login_success = await client.login("sales1", "demo123")
        print(f"   ✅ Login: {'PASS' if login_success else 'FAIL'}")
        
        # 3. Test opportunity analysis
        print("\n3. Testing opportunity analysis...")
        test_opportunity = "Bank needs AI-powered fraud detection system with cloud deployment"
        analysis = await client.analyze_opportunity(test_opportunity)
        
        if "error" not in analysis:
            print(f"   ✅ Opportunity analysis: PASS")
            print(f"   📊 Analysis results: {analysis.get('status', 'unknown')}")
            print(f"   📈 Offerings matched: {len(analysis.get('offerings_matched', []))}")
        else:
            print(f"   ❌ Opportunity analysis: FAIL - {analysis.get('error')}")
        
        # 4. Test chat
        print("\n4. Testing chat...")
        chat_response = await client.chat_with_sales_eva("What AI solutions do you have?")
        print(f"   ✅ Chat response: {chat_response.get('response', '')[:100]}...")
        
        # 5. Test opportunities list
        print("\n5. Testing opportunities retrieval...")
        opportunities = await client.get_opportunities()
        print(f"   ✅ Opportunities retrieved: {len(opportunities)}")
        
        # Cleanup
        await client.close()
        
        print("\n" + "="*50)
        print("🎉 Sales EVA Service Integration Test COMPLETE!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sales_eva_service())
    sys.exit(0 if success else 1)