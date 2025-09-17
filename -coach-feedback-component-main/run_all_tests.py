#!/opt/anaconda3/bin/python
"""
Master Test Runner - Run All Tests for Coach Feedback Component
32-Hour Integration Sprint - Parth's Component
"""

import subprocess
import sys
import time
import requests

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_test_file(test_file, description):
    """Run a specific test file"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"File: {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ TEST PASSED")
            print(result.stdout)
            return True
        else:
            print("❌ TEST FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ TEST TIMEOUT (30s)")
        return False
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        return False

def main():
    print("🚀 MASTER TEST RUNNER")
    print("32-Hour Integration Sprint - Coach Feedback Component")
    print("Author: Parth")
    print("="*60)
    
    # Check server status
    print("\n🔍 Checking server status...")
    if check_server():
        print("✅ Server is running on http://localhost:8001")
    else:
        print("❌ Server is not running!")
        print("Please start the server first:")
        print("  python main.py")
        return False
    
    # Define tests to run
    tests = [
        ("test_database.py", "Database Schema & Integrity Test"),
        ("quick_test.py", "Quick API Functionality Test"), 
        ("test_core.py", "Core Business Logic Test"),
        ("test_api.py", "API Integration Test"),
        ("test_comprehensive.py", "Comprehensive System Test")
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    # Run all tests
    for test_file, description in tests:
        success = run_test_file(test_file, description)
        if success:
            passed_tests += 1
        
        # Small delay between tests
        time.sleep(1)
    
    # Final summary
    print("\n" + "="*60)
    print("📊 FINAL TEST SUMMARY")
    print("="*60)
    print(f"Total Tests Run: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Coach Feedback Component is fully operational")
        print("✅ Ready for team integration")
        print("✅ Production ready!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        print("Please review the failed tests and fix issues")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)