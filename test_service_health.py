# test_sales_eva_service.py
import httpx
import asyncio
import sys
import json
from typing import Dict, Any, List

class SalesEVAServiceTester:
    """Test the actual Sales EVA service endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)
        self.session_cookie = None
    
    async def _make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request with session handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add cookies if we have a session
        if self.session_cookie:
            if 'cookies' not in kwargs:
                kwargs['cookies'] = {}
            kwargs['cookies'].update(self.session_cookie)
        
        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = await self.client.post(url, **kwargs)
            elif method.upper() == 'PUT':
                response = await self.client.put(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = await self.client.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Update session cookies if response has them
            if response.cookies:
                if not self.session_cookie:
                    self.session_cookie = {}
                self.session_cookie.update(response.cookies)
            
            return response
            
        except Exception as e:
            raise Exception(f"Request failed to {url}: {str(e)}")
    
    async def test_root_endpoint(self) -> Dict[str, Any]:
        """Test the root endpoint (GET /)"""
        print("1️⃣  Testing root endpoint (GET /)...")
        try:
            response = await self._make_request('GET', '/')
            
            result = {
                "endpoint": "/",
                "method": "GET",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if result["success"]:
                print(f"   ✅ SUCCESS: HTTP {response.status_code}")
                if isinstance(result["response"], dict):
                    print(f"      Service: {result['response'].get('service', 'Unknown')}")
                    print(f"      Status: {result['response'].get('status', 'Unknown')}")
            else:
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "endpoint": "/",
                "method": "GET",
                "success": False,
                "error": str(e)
            }
    
    async def test_login(self, username: str, password: str, expected_success: bool = True) -> Dict[str, Any]:
        """Test login endpoint"""
        test_name = f"Login as '{username}'"
        print(f"\n2️⃣  Testing {test_name} (POST /login)...")
        
        try:
            response = await self._make_request(
                'POST',
                '/login',
                json={"username": username, "password": password}
            )
            
            result = {
                "endpoint": "/login",
                "method": "POST",
                "username": username,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "has_session_cookie": bool(response.cookies),
                "response": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["response"] = data
                    result["user_data"] = data.get('user')
                    
                    if expected_success:
                        print(f"   ✅ SUCCESS: Login successful!")
                        print(f"      User: {data['user']['username']} ({data['user']['role']})")
                        print(f"      Session cookie: {'Yes' if result['has_session_cookie'] else 'No'}")
                    else:
                        print(f"   ⚠️  WARNING: Login succeeded but was expected to fail")
                        
                except:
                    result["response"] = response.text
                    print(f"   ⚠️  WARNING: Non-JSON response: {response.text[:100]}")
                    
            elif response.status_code == 401:
                result["success"] = False
                if not expected_success:
                    print(f"   ✅ SUCCESS: Login correctly rejected (invalid credentials)")
                else:
                    print(f"   ❌ FAILED: Login rejected but expected success")
                print(f"      Response: {response.text[:100]}")
                
            else:
                result["success"] = False
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "endpoint": "/login",
                "method": "POST",
                "username": username,
                "success": False,
                "error": str(e)
            }
    
    async def test_profile(self) -> Dict[str, Any]:
        """Test profile endpoint (requires authentication)"""
        print("\n3️⃣  Testing profile endpoint (GET /profile)...")
        
        try:
            response = await self._make_request('GET', '/profile')
            
            result = {
                "endpoint": "/profile",
                "method": "GET",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["response"] = data
                    print(f"   ✅ SUCCESS: Profile access granted!")
                    print(f"      User: {data.get('username', 'Unknown')}")
                    print(f"      Role: {data.get('role', 'Unknown')}")
                except:
                    result["response"] = response.text
                    print(f"   ⚠️  WARNING: Non-JSON response: {response.text[:100]}")
                    
            elif response.status_code == 401:
                result["success"] = False
                print(f"   ⚠️  AUTH REQUIRED: Profile endpoint requires login")
                print("      (This is expected if you haven't logged in yet)")
                
            else:
                result["success"] = False
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "endpoint": "/profile",
                "method": "GET",
                "success": False,
                "error": str(e)
            }
    
    async def test_opportunities(self) -> Dict[str, Any]:
        """Test opportunities endpoint"""
        print("\n4️⃣  Testing opportunities endpoint (GET /opportunities)...")
        
        try:
            response = await self._make_request('GET', '/opportunities')
            
            result = {
                "endpoint": "/opportunities",
                "method": "GET",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["response"] = data
                    opportunities = data.get('opportunities', [])
                    print(f"   ✅ SUCCESS: Opportunities retrieved!")
                    print(f"      Count: {len(opportunities)} opportunities")
                    if opportunities:
                        print(f"      Sample: {opportunities[0].get('title', 'No title')[:50]}...")
                except:
                    result["response"] = response.text
                    print(f"   ⚠️  WARNING: Non-JSON response: {response.text[:100]}")
                    
            elif response.status_code == 401:
                result["success"] = False
                print(f"   ⚠️  AUTH REQUIRED: Opportunities endpoint requires login")
                
            else:
                result["success"] = False
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "endpoint": "/opportunities",
                "method": "GET",
                "success": False,
                "error": str(e)
            }
    
    async def test_rag_search(self, query: str = "AI solutions for banking") -> Dict[str, Any]:
        """Test RAG search endpoint"""
        print(f"\n5️⃣  Testing RAG search (POST /api/rag/search)...")
        print(f"   Query: '{query[:50]}...'" if len(query) > 50 else f"   Query: '{query}'")
        
        try:
            response = await self._make_request(
                'POST',
                '/api/rag/search',
                json={"query": query}
            )
            
            result = {
                "endpoint": "/api/rag/search",
                "method": "POST",
                "query": query,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["response"] = data
                    results = data.get('results', [])
                    print(f"   ✅ SUCCESS: RAG search completed!")
                    print(f"      Results found: {len(results)}")
                    if results:
                        print(f"      First result: {results[0].get('title', 'No title')[:50]}...")
                except:
                    result["response"] = response.text
                    print(f"   ⚠️  WARNING: Non-JSON response: {response.text[:100]}")
                    
            elif response.status_code == 401:
                result["success"] = False
                print(f"   ⚠️  AUTH REQUIRED: RAG search requires login")
                
            else:
                result["success"] = False
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "endpoint": "/api/rag/search",
                "method": "POST",
                "query": query,
                "success": False,
                "error": str(e)
            }
    
    async def test_logout(self) -> Dict[str, Any]:
        """Test logout endpoint"""
        print("\n6️⃣  Testing logout (POST /logout)...")
        
        try:
            response = await self._make_request('POST', '/logout')
            
            result = {
                "endpoint": "/logout",
                "method": "POST",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["response"] = data
                    print(f"   ✅ SUCCESS: Logout completed!")
                    print(f"      Message: {data.get('message', 'Logged out')}")
                    # Clear session after logout
                    self.session_cookie = None
                except:
                    result["response"] = response.text
                    print(f"   ⚠️  WARNING: Non-JSON response: {response.text[:100]}")
                    
            elif response.status_code == 401:
                result["success"] = False
                print(f"   ⚠️  NOT LOGGED IN: Can't logout without being logged in")
                
            else:
                result["success"] = False
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "endpoint": "/logout",
                "method": "POST",
                "success": False,
                "error": str(e)
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all endpoints"""
        print("=" * 60)
        print("🚀 COMPREHENSIVE SALES EVA SERVICE TEST")
        print("=" * 60)
        print(f"Testing service at: {self.base_url}")
        print("=" * 60)
        
        all_results = []
        
        # Test 1: Root endpoint
        root_result = await self.test_root_endpoint()
        all_results.append(root_result)
        
        # Test 2: Login with invalid credentials (should fail)
        invalid_login = await self.test_login("wronguser", "wrongpass", expected_success=False)
        all_results.append(invalid_login)
        
        # Test 3: Login with valid credentials (should succeed)
        valid_login = await self.test_login("sales1", "demo123", expected_success=True)
        all_results.append(valid_login)
        
        if valid_login.get("success"):
            # Test 4: Profile (should work after login)
            profile_result = await self.test_profile()
            all_results.append(profile_result)
            
            # Test 5: Opportunities (should work after login)
            opp_result = await self.test_opportunities()
            all_results.append(opp_result)
            
            # Test 6: RAG search (should work after login)
            rag_result = await self.test_rag_search("AI fraud detection solutions")
            all_results.append(rag_result)
            
            # Test 7: Logout
            logout_result = await self.test_logout()
            all_results.append(logout_result)
            
            # Test 8: Try profile again after logout (should fail)
            print("\n7️⃣  Testing profile after logout (should fail)...")
            profile_after_logout = await self.test_profile()
            all_results.append(profile_after_logout)
        else:
            print("\n⚠️  Skipping authenticated tests because login failed")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in all_results if r.get("success", False)]
        failed_tests = [r for r in all_results if not r.get("success", False) and "error" not in r]
        error_tests = [r for r in all_results if "error" in r]
        
        print(f"Total tests: {len(all_results)}")
        print(f"✅ Successful: {len(successful_tests)}")
        print(f"❌ Failed: {len(failed_tests)}")
        print(f"⚠️  Errors: {len(error_tests)}")
        
        if failed_tests:
            print("\nFailed tests:")
            for test in failed_tests:
                endpoint = test.get("endpoint", "Unknown")
                method = test.get("method", "Unknown")
                status = test.get("status_code", "N/A")
                print(f"  ❌ {method} {endpoint} (HTTP {status})")
        
        if error_tests:
            print("\nTests with errors:")
            for test in error_tests:
                endpoint = test.get("endpoint", "Unknown")
                error = test.get("error", "Unknown error")
                print(f"  ⚠️  {endpoint}: {error}")
        
        # Overall status
        success_rate = (len(successful_tests) / len(all_results)) * 100 if all_results else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: Service is fully operational!")
        elif success_rate >= 60:
            print("👍 GOOD: Service is mostly working")
        elif success_rate >= 40:
            print("⚠️  FAIR: Service has some issues")
        else:
            print("❌ POOR: Service has significant problems")
        
        print("=" * 60)
        
        return {
            "service_url": self.base_url,
            "total_tests": len(all_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "error_tests": len(error_tests),
            "success_rate": success_rate,
            "results": all_results
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Sales EVA Service')
    parser.add_argument('--url', type=str, default='http://localhost:5000',
                       help='Sales EVA service URL')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick health check only')
    
    args = parser.parse_args()
    
    tester = SalesEVAServiceTester(args.url)
    
    try:
        if args.quick:
            # Quick health check
            print("🔍 Quick health check...")
            response = await tester.client.get(f"{args.url.rstrip('/')}/")
            if response.status_code == 200:
                print(f"✅ Service is responding at {args.url}")
                return 0
            else:
                print(f"❌ Service returned HTTP {response.status_code}")
                return 1
        else:
            # Comprehensive test
            results = await tester.run_comprehensive_test()
            
            # Save results to file
            import json
            with open('service_test_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Detailed results saved to: service_test_results.json")
            
            return 0 if results["success_rate"] >= 60 else 1
            
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        return 1
    finally:
        await tester.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)