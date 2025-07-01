#!/usr/bin/env python3
"""
Run All Examples - Browser-Use Local Bridge
===========================================

Master script to run all examples in sequence with proper error handling and reporting.
Useful for testing the complete functionality of the Browser-Use Local Bridge.
"""

import asyncio
import sys
import time
import traceback
from pathlib import Path

# Add the examples directory to the path so we can import the example modules
sys.path.append(str(Path(__file__).parent))

# Import all example modules
try:
    from examples import (
        example_01_basic_web_search as ex01,
        example_02_ecommerce_automation as ex02,
        example_03_form_automation as ex03,
        example_04_n8n_integration as ex04,
        example_05_advanced_monitoring as ex05
    )
except ImportError:
    # Fallback for direct execution
    import importlib.util
    
    def load_example_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    current_dir = Path(__file__).parent
    ex01 = load_example_module("ex01", current_dir / "01_basic_web_search.py")
    ex02 = load_example_module("ex02", current_dir / "02_ecommerce_automation.py")
    ex03 = load_example_module("ex03", current_dir / "03_form_automation.py")
    ex04 = load_example_module("ex04", current_dir / "04_n8n_integration.py")
    ex05 = load_example_module("ex05", current_dir / "05_advanced_monitoring.py")


class ExampleRunner:
    """Manages running all examples with comprehensive reporting"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.total_time = 0
    
    async def run_example(self, name: str, example_func, timeout: int = 600):
        """Run a single example with error handling and timeout"""
        print(f"\n{'='*80}")
        print(f"🚀 Running Example: {name}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Run example with timeout
            result = await asyncio.wait_for(example_func(), timeout=timeout)
            
            execution_time = time.time() - start_time
            
            if result and isinstance(result, dict) and result.get('status') == 'FINISHED':
                status = "✅ SUCCESS"
                error = None
            elif result and isinstance(result, dict) and result.get('status') == 'FAILED':
                status = "❌ FAILED"
                error = result.get('error', 'Unknown error')
            else:
                status = "⚠️  COMPLETED" 
                error = None
            
            self.results[name] = {
                'status': status,
                'execution_time': execution_time,
                'error': error,
                'result': result
            }
            
            print(f"\n🏁 {name}: {status}")
            print(f"⏱️  Execution time: {execution_time:.1f} seconds")
            if error:
                print(f"❌ Error: {error}")
                
        except asyncio.TimeoutError:
            execution_time = timeout
            self.results[name] = {
                'status': "⏰ TIMEOUT",
                'execution_time': execution_time,
                'error': f"Example timed out after {timeout} seconds",
                'result': None
            }
            print(f"\n⏰ {name}: TIMEOUT after {timeout} seconds")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_details = f"{type(e).__name__}: {str(e)}"
            
            self.results[name] = {
                'status': "💥 ERROR",
                'execution_time': execution_time,
                'error': error_details,
                'result': None
            }
            
            print(f"\n💥 {name}: ERROR")
            print(f"❌ {error_details}")
            if '--debug' in sys.argv:
                print(f"\n🔍 Full traceback:")
                traceback.print_exc()
    
    def print_summary(self):
        """Print comprehensive summary of all example results"""
        print(f"\n\n{'='*80}")
        print(f"📊 EXAMPLE EXECUTION SUMMARY")
        print(f"{'='*80}")
        
        total_examples = len(self.results)
        successful = len([r for r in self.results.values() if "SUCCESS" in r['status']])
        failed = len([r for r in self.results.values() if "FAILED" in r['status'] or "ERROR" in r['status']])
        timeouts = len([r for r in self.results.values() if "TIMEOUT" in r['status']])
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Examples: {total_examples}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏰ Timeouts: {timeouts}")
        print(f"   🕐 Total Runtime: {self.total_time:.1f} seconds")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for name, result in self.results.items():
            print(f"\n   {result['status']} {name}")
            print(f"      Time: {result['execution_time']:.1f}s")
            if result['error']:
                print(f"      Error: {result['error']}")
        
        # Success rate
        success_rate = (successful / total_examples) * 100 if total_examples > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 All examples completed successfully!")
        elif success_rate >= 80:
            print("👍 Most examples completed successfully!")
        elif success_rate >= 50:
            print("⚠️  Some examples had issues - check configuration")
        else:
            print("❌ Many examples failed - check API and configuration")


async def check_api_health():
    """Check if the API is available before running examples"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=10.0)
            if response.status_code == 200:
                print("✅ API health check passed")
                return True
            else:
                print(f"❌ API health check failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure the Browser-Use Local Bridge is running:")
        print("   python main.py")
        return False


async def main():
    """Run all examples in sequence"""
    print("🌐 Browser-Use Local Bridge - Complete Example Suite")
    print("=" * 60)
    print("This script will run all 5 examples to demonstrate the full capabilities")
    print("of the Browser-Use Local Bridge API.\n")
    
    # Check command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python run_all_examples.py [options]")
        print("\nOptions:")
        print("  --help, -h     Show this help message")
        print("  --debug        Show full error tracebacks")
        print("  --quick        Run with shorter timeouts")
        print("  --skip-health  Skip API health check")
        return
    
    quick_mode = '--quick' in sys.argv
    skip_health = '--skip-health' in sys.argv
    
    # Check API health
    if not skip_health:
        print("🔍 Checking API availability...")
        if not await check_api_health():
            print("\n💡 To start the API:")
            print("   1. Open a terminal in the project directory")
            print("   2. Run: python main.py")
            print("   3. Wait for 'API is healthy and ready' message")
            print("   4. Run this script again")
            return
    
    runner = ExampleRunner()
    runner.start_time = time.time()
    
    # Define examples with their timeouts
    examples = [
        ("01 - Basic Web Search", ex01.main, 180 if quick_mode else 300),
        ("02 - E-Commerce Automation", ex02.main, 300 if quick_mode else 600),
        ("03 - Form Automation", ex03.main, 240 if quick_mode else 480),
        ("04 - n8n Integration", ex04.main, 120 if quick_mode else 240),
        ("05 - Advanced Monitoring", ex05.main, 360 if quick_mode else 720),
    ]
    
    print(f"📋 Scheduled {len(examples)} examples for execution")
    if quick_mode:
        print("⚡ Quick mode enabled - using shorter timeouts")
    
    # Run all examples
    for name, func, timeout in examples:
        await runner.run_example(name, func, timeout)
        
        # Brief pause between examples
        if name != examples[-1][0]:  # Don't pause after last example
            print(f"\n⏳ Pausing 5 seconds before next example...")
            await asyncio.sleep(5)
    
    runner.total_time = time.time() - runner.start_time
    
    # Print comprehensive summary
    runner.print_summary()
    
    # Final recommendations
    print(f"\n💡 Next Steps:")
    print(f"   • Review the detailed API documentation at http://localhost:8000/docs")
    print(f"   • Check the examples/README.md for more information")
    print(f"   • Explore individual examples to understand specific features")
    print(f"   • Customize examples for your specific use cases")
    
    # Exit code based on success rate
    successful = len([r for r in runner.results.values() if "SUCCESS" in r['status']])
    success_rate = (successful / len(runner.results)) * 100
    
    if success_rate == 100:
        sys.exit(0)  # All good
    elif success_rate >= 80:
        sys.exit(1)  # Mostly good but some issues
    else:
        sys.exit(2)  # Major issues


if __name__ == "__main__":
    asyncio.run(main()) 