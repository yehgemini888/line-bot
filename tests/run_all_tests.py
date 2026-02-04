"""
Test Runner: Execute All Tests

Run all unit tests for the Line Bot project.
Usage: python tests/run_all_tests.py
"""

import asyncio
import os
import sys
import importlib.util

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()


async def run_test(test_name: str, test_file: str):
    """Run a single test file."""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_name}")
    print(f"{'='*60}")
    
    try:
        # Import the test module
        spec = importlib.util.spec_from_file_location(
            test_name, 
            os.path.join(os.path.dirname(__file__), test_file)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find and run the main test function
        for attr_name in dir(module):
            if attr_name.startswith("test_"):
                func = getattr(module, attr_name)
                if asyncio.iscoroutinefunction(func):
                    await func()
                    break
        
        print(f"✅ {test_name} completed")
        return True
    except Exception as e:
        print(f"❌ {test_name} failed: {e}")
        return False


async def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║           Line Bot Unit Test Runner                      ║
╚══════════════════════════════════════════════════════════╝
""")
    
    tests = [
        ("Web Scraper", "test_web_scraper.py"),
        ("AI Summarization", "test_summarize.py"),
        ("YouTube Service", "test_youtube.py"),
        ("Notion Repository", "test_notion.py"),
    ]
    
    # Ask user which tests to run
    print("Available tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")
    print("  0. Run ALL tests")
    
    choice = input("\nSelect test number (0-4): ").strip()
    
    results = []
    
    if choice == "0":
        # Run all tests
        for name, file in tests:
            result = await run_test(name, file)
            results.append((name, result))
    elif choice.isdigit() and 1 <= int(choice) <= len(tests):
        name, file = tests[int(choice) - 1]
        result = await run_test(name, file)
        results.append((name, result))
    else:
        print("Invalid choice")
        return
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {name}")


if __name__ == "__main__":
    asyncio.run(main())
