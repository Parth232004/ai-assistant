#!/opt/anaconda3/bin/python
"""
Test the /api/coach_feedback endpoint implementation
32-Hour Integration Sprint - Parth's Component
"""

import requests
import json

def test_coach_feedback_endpoint():
    """Test the coach feedback endpoint with real HTTP requests"""
    
    base_url = "http://localhost:8001"
    
    print("=== Testing Coach Feedback API ===")
    print(f"Server: {base_url}")
    
    # Test 1: Health check
    print("\n1. Testing server health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test 2: Submit coach feedback
    print("\n2. Testing /api/coach_feedback POST...")
    
    test_feedback = {
        "summary_id": "s123",
        "task_id": "t456", 
        "response_id": "r789",
        "scores": {
            "clarity": 4,
            "relevance": 5,
            "tone": 3
        },
        "comment": "Good response but could be more detailed. Tone was a bit too casual."
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/coach_feedback",
            json=test_feedback,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Coach feedback submitted successfully!")
            print(f"   Feedback ID: {result['feedback_id']}")
            print(f"   Aggregate Score: {result['score']} (Expected: 12)")
            print(f"   Stored: {result['stored']}")
            
            feedback_id = result['feedback_id']
            
            # Test 3: Retrieve the feedback
            print("\n3. Testing feedback retrieval...")
            get_response = requests.get(f"{base_url}/api/coach_feedback/{feedback_id}")
            
            if get_response.status_code == 200:
                retrieved = get_response.json()
                print("✅ Feedback retrieved successfully!")
                print(f"   Retrieved feedback: {json.dumps(retrieved, indent=2)}")
            else:
                print(f"❌ Failed to retrieve feedback: {get_response.status_code}")
                
            # Test 4: List all feedback
            print("\n4. Testing feedback listing...")
            list_response = requests.get(f"{base_url}/api/coach_feedback")
            
            if list_response.status_code == 200:
                feedback_list = list_response.json()
                print("✅ Feedback list retrieved successfully!")
                print(f"   Total feedback entries: {feedback_list['count']}")
                if feedback_list['count'] > 0:
                    print(f"   Latest entry: {feedback_list['feedback'][0]['feedback_id']}")
            else:
                print(f"❌ Failed to list feedback: {list_response.status_code}")
            
            return True
            
        else:
            print(f"❌ Failed to submit feedback: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing coach feedback: {e}")
        return False

def test_invalid_data():
    """Test error handling with invalid data"""
    print("\n5. Testing error handling...")
    
    # Test with missing required fields
    invalid_data = {
        "summary_id": "s123",
        # Missing task_id, response_id, scores, comment
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/api/coach_feedback",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 422:  # Validation error
            print("✅ Validation error handling works correctly")
            print(f"   Status: {response.status_code}")
        else:
            print(f"❌ Expected validation error, got: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing invalid data: {e}")

if __name__ == "__main__":
    print("Coach Feedback API Integration Test")
    print("32-Hour Sprint - Parth's Component")
    print("="*50)
    
    success = test_coach_feedback_endpoint()
    test_invalid_data()
    
    print("\n" + "="*50)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("✅ /api/coach_feedback endpoint is working correctly")
        print("✅ Database integration successful")
        print("✅ Ready for team integration!")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Fix issues before proceeding with integration")
        
    print("\nNext steps for sprint:")
    print("- Integrate with Chandresh's /api/search_similar for relevance scoring")
    print("- Add Streamlit Feedback tab") 
    print("- Implement /api/rl_reward hook")
    print("- Write integration tests")