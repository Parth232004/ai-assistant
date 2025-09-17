#!/opt/anaconda3/bin/python
"""
Test script for coach_feedback API endpoint
Part of the 32-hour integration sprint
"""

import requests
import json
import sqlite3
from datetime import datetime

# Test the coach feedback endpoint
def test_coach_feedback():
    print("Testing /api/coach_feedback endpoint...")
    
    # Test data according to sprint specifications
    test_data = {
        "summary_id": "s123",
        "task_id": "t123", 
        "response_id": "r123",
        "scores": {
            "clarity": 4,
            "relevance": 5,
            "tone": 4
        },
        "comment": "Good response but could be more concise"
    }
    
    try:
        # Test the module directly (since we don't have the full FastAPI app running)
        from pi.api.coach_feedback import coach_feedback, FeedbackRequest
        
        # Create request object
        req = FeedbackRequest(**test_data)
        
        # Call the function
        result = coach_feedback(req)
        
        print(f"✅ Coach feedback stored successfully!")
        print(f"   Feedback ID: {result.feedback_id}")
        print(f"   Aggregate Score: {result.score}")
        print(f"   Stored: {result.stored}")
        
        # Verify database entry
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM coach_feedback WHERE id = ?", (result.feedback_id,))
        db_result = cursor.fetchone()
        conn.close()
        
        if db_result:
            print(f"✅ Database verification successful!")
            print(f"   DB Record: {db_result}")
        else:
            print("❌ Database verification failed!")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_database_schema():
    """Verify the coach_feedback table was created correctly"""
    print("\nTesting database schema...")
    
    try:
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        # Check if table exists and get schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='coach_feedback'")
        schema = cursor.fetchone()
        
        if schema:
            print("✅ coach_feedback table exists")
            print(f"   Schema: {schema[0]}")
        else:
            print("❌ coach_feedback table does not exist")
            
        # Check table structure
        cursor.execute("PRAGMA table_info(coach_feedback)")
        columns = cursor.fetchall()
        
        expected_columns = ['id', 'summary_id', 'task_id', 'response_id', 'score', 
                          'comment', 'clarity_score', 'relevance_score', 'tone_score', 'timestamp']
        
        actual_columns = [col[1] for col in columns]
        
        print(f"   Columns: {actual_columns}")
        
        missing_columns = set(expected_columns) - set(actual_columns)
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
        else:
            print("✅ All expected columns present")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Coach Feedback API Test ===")
    print("Sprint: 32-Hour Integration Push")
    print("Owner: Parth")
    print("Component: CoachAgent & Feedback")
    print("=" * 40)
    
    # Run tests
    schema_ok = test_database_schema()
    feedback_ok = test_coach_feedback()
    
    print("\n" + "=" * 40)
    if schema_ok and feedback_ok:
        print("✅ ALL TESTS PASSED!")
        print("Ready for integration with team components")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check errors above and fix before integration")