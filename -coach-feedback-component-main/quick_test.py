#!/opt/anaconda3/bin/python
"""
Quick API Test for Coach Feedback Component
Use this for fast verification of API functionality
"""

import requests
import json
import time

def quick_api_test():
    base_url = "http://localhost:8001"
    
    print("🚀 Quick API Test - Coach Feedback Component")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print(f"✅ Health Check: {response.json()}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test 2: Submit Feedback
    print("\n2. Testing feedback submission...")
    test_feedback = {
        "summary_id": f"quick_test_{int(time.time())}",
        "task_id": f"task_{int(time.time())}",
        "response_id": f"resp_{int(time.time())}",
        "scores": {"clarity": 5, "relevance": 4, "tone": 4},
        "comment": "Quick test feedback - excellent response!"
    }
    
    try:
        response = requests.post(f"{base_url}/api/coach_feedback", json=test_feedback)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Feedback Submitted: ID={data['feedback_id']}, Score={data['score']}")
            feedback_id = data['feedback_id']
        else:
            print(f"❌ Feedback Submission Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Submission Error: {e}")
        return False
    
    # Test 3: Retrieve Feedback
    print("\n3. Testing feedback retrieval...")
    try:
        response = requests.get(f"{base_url}/api/coach_feedback/{feedback_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Feedback Retrieved: Score={data['score']}, Comment='{data['comment'][:30]}...'")
        else:
            print(f"❌ Retrieval Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Retrieval Error: {e}")
        return False
    
    # Test 4: List Feedback
    print("\n4. Testing feedback listing...")
    try:
        response = requests.get(f"{base_url}/api/coach_feedback?limit=3")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Feedback Listing: {data['count']} total entries")
        else:
            print(f"❌ Listing Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Listing Error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL QUICK TESTS PASSED!")
    print("✅ Coach Feedback API is working correctly")
    return True

if __name__ == "__main__":
    success = quick_api_test()
    if not success:
        print("\n❌ Some tests failed. Check server status and try again.")
    else:
        print("✅ Ready for production use!")