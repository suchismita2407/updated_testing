#!/usr/bin/env python3
"""
Command-line script to run Sales EVA tests
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tester import SalesEVATester
from config.settings import settings

async def run_tests(args):
    """Run tests based on command line arguments"""
    
    # Create tester
    tester = SalesEVATester(api_url=args.api_url)
    
    try:
        if args.quick:
            print("🔍 Running quick test...")
            results = await tester.run_quick_test()
            print(f"✅ Quick test completed: Score: {results.get('score', 0):.2f}")
            
        else:
            # Parse test types
            if args.test_types:
                test_types = [t.strip() for t in args.test_types.split(",")]
            else:
                test_types = None
            
            print(f"🚀 Running comprehensive tests: {test_types or 'all'}...")
            
            results = await tester.run_all_tests(
                test_types=test_types,
                save_results=True
            )
            
            # Display summary
            summary = results.get("summary", {})
            print(f"\n📊 Test Results Summary:")
            print(f"   Overall Score: {summary.get('overall_score', 0):.2f}/1.0")
            print(f"   Health: {summary.get('health_assessment', {}).get('status', 'unknown')}")
            print(f"   Tests Completed: {', '.join(summary.get('tests_completed', []))}")
            
            if summary.get('tests_failed'):
                print(f"   Tests Failed: {', '.join(summary.get('tests_failed', []))}")
        
        # Display recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"   {i}. {rec}")
        
        # Return results for programmatic use
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        await tester.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sales EVA Testing Framework CLI"
    )
    
    parser.add_argument(
        "--api-url",
        default=settings.SALES_EVA_API_URL,
        help=f"Sales EVA API URL (default: {settings.SALES_EVA_API_URL})"
    )
    
    parser.add_argument(
        "--test-types",
        help="Comma-separated test types (prompt,agent,kb,e2e). Default: all"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test only"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for results (JSON)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Run tests
    try:
        results = asyncio.run(run_tests(args))
        
        # Save output if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {args.output}")
        
        # Exit code based on success
        if results.get("summary", {}).get("overall_score", 0) > 0.6:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()