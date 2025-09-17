#!/opt/anaconda3/bin/python
"""
COMPREHENSIVE SYSTEM TEST
32-Hour Integration Sprint - Parth's Coach Feedback Component
Tests ALL accessories and components
"""

import requests
import sqlite3
import json
import time
from datetime import datetime

class ComprehensiveTest:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append(f"{status} - {test_name}")
        if details:
            self.test_results.append(f"    {details}")
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_server_connectivity(self):
        """Test 1: Server is running and responsive"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}, Response: {response.json()}"
            self.log_test("Server Connectivity", passed, details)
            return passed
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Error: {e}")
            return False
    
    def test_health_endpoint(self):
        """Test 2: Health endpoint functionality"""
        try:
            response = requests.get(f"{self.base_url}/health")
            data = response.json()
            passed = (response.status_code == 200 and 
                     data.get("status") == "healthy" and 
                     data.get("component") == "coach_feedback")
            self.log_test("Health Endpoint", passed, f"Response: {data}")
            return passed
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {e}")
            return False
    
    def test_database_schema(self):
        """Test 3: Database schema integrity"""
        try:
            conn = sqlite3.connect("assistant_demo.db")
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coach_feedback'")
            table_exists = cursor.fetchone() is not None
            
            # Check all required columns
            cursor.execute("PRAGMA table_info(coach_feedback)")
            columns = [col[1] for col in cursor.fetchall()]
            required_columns = ['id', 'summary_id', 'task_id', 'response_id', 'score', 
                              'comment', 'clarity_score', 'relevance_score', 'tone_score', 'timestamp']
            
            all_columns_present = all(col in columns for col in required_columns)
            
            conn.close()
            
            passed = table_exists and all_columns_present
            details = f"Table exists: {table_exists}, Columns: {len(columns)}/10 required"
            self.log_test("Database Schema", passed, details)
            return passed
        except Exception as e:
            self.log_test("Database Schema", False, f"Error: {e}")
            return False
    
    def test_coach_feedback_submission(self):
        """Test 4: Coach feedback submission with valid data"""
        test_data = {
            "summary_id": f"test_s{int(time.time())}",
            "task_id": f"test_t{int(time.time())}",
            "response_id": f"test_r{int(time.time())}",
            "scores": {"clarity": 4, "relevance": 5, "tone": 3},
            "comment": "Comprehensive system test feedback"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/coach_feedback", json=test_data)
            data = response.json()
            
            passed = (response.status_code == 200 and 
                     'feedback_id' in data and 
                     data.get('score') == 12 and  # 4+5+3
                     data.get('stored') == True)
            
            details = f"Status: {response.status_code}, Score: {data.get('score')}, ID: {data.get('feedback_id')}"
            self.log_test("Feedback Submission", passed, details)
            
            # Store feedback_id for next test
            self.last_feedback_id = data.get('feedback_id') if passed else None
            return passed
        except Exception as e:
            self.log_test("Feedback Submission", False, f"Error: {e}")
            return False
    
    def test_feedback_retrieval(self):
        """Test 5: Individual feedback retrieval"""
        if not hasattr(self, 'last_feedback_id') or not self.last_feedback_id:
            self.log_test("Feedback Retrieval", False, "No feedback ID from previous test")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/api/coach_feedback/{self.last_feedback_id}")
            data = response.json()
            
            passed = (response.status_code == 200 and 
                     data.get('feedback_id') == self.last_feedback_id and
                     'scores' in data and 
                     'timestamp' in data)
            
            details = f"Retrieved ID: {data.get('feedback_id')}, Score: {data.get('score')}"
            self.log_test("Feedback Retrieval", passed, details)
            return passed
        except Exception as e:
            self.log_test("Feedback Retrieval", False, f"Error: {e}")
            return False
    
    def test_feedback_listing(self):
        """Test 6: Feedback listing functionality"""
        try:
            response = requests.get(f"{self.base_url}/api/coach_feedback?limit=10")
            data = response.json()
            
            passed = (response.status_code == 200 and 
                     'feedback' in data and 
                     'count' in data and 
                     isinstance(data['feedback'], list))
            
            details = f"Count: {data.get('count')}, Entries: {len(data.get('feedback', []))}"
            self.log_test("Feedback Listing", passed, details)
            return passed
        except Exception as e:
            self.log_test("Feedback Listing", False, f"Error: {e}")
            return False
    
    def test_error_handling(self):
        """Test 7: Error handling with invalid data"""
        invalid_data = {"summary_id": "test", "scores": {}}  # Missing required fields
        
        try:
            response = requests.post(f"{self.base_url}/api/coach_feedback", json=invalid_data)
            
            passed = response.status_code == 422  # Unprocessable Entity
            details = f"Status: {response.status_code} (Expected: 422)"
            self.log_test("Error Handling", passed, details)
            return passed
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {e}")
            return False
    
    def test_404_handling(self):
        """Test 8: 404 handling for non-existent feedback"""
        try:
            response = requests.get(f"{self.base_url}/api/coach_feedback/nonexistent123")
            
            passed = response.status_code == 404
            details = f"Status: {response.status_code} (Expected: 404)"
            self.log_test("404 Handling", passed, details)
            return passed
        except Exception as e:
            self.log_test("404 Handling", False, f"Error: {e}")
            return False
    
    def test_score_calculation(self):
        """Test 9: Score calculation accuracy"""
        from pi.api.coach_feedback import calculate_aggregate_score
        
        test_cases = [
            ({"clarity": 3, "relevance": 4, "tone": 2}, 9),
            ({"clarity": 5, "relevance": 5, "tone": 5}, 15),
            ({"clarity": 1}, 1),
            ({}, 0)
        ]
        
        all_passed = True
        for scores, expected in test_cases:
            result = calculate_aggregate_score(scores)
            if result != expected:
                all_passed = False
                break
        
        details = f"Tested {len(test_cases)} calculation scenarios"
        self.log_test("Score Calculation", all_passed, details)
        return all_passed
    
    def test_database_data_integrity(self):
        """Test 10: Database data integrity"""
        try:
            conn = sqlite3.connect("assistant_demo.db")
            cursor = conn.cursor()
            
            # Count total feedback entries
            cursor.execute("SELECT COUNT(*) FROM coach_feedback")
            total_count = cursor.fetchone()[0]
            
            # Check recent entries have all required fields
            cursor.execute("""
                SELECT id, summary_id, task_id, response_id, score, timestamp 
                FROM coach_feedback 
                WHERE id IS NOT NULL AND summary_id IS NOT NULL 
                AND task_id IS NOT NULL AND response_id IS NOT NULL
                ORDER BY timestamp DESC LIMIT 3
            """)
            valid_entries = cursor.fetchall()
            
            conn.close()
            
            passed = total_count > 0 and len(valid_entries) > 0
            details = f"Total entries: {total_count}, Valid recent entries: {len(valid_entries)}"
            self.log_test("Database Data Integrity", passed, details)
            return passed
        except Exception as e:
            self.log_test("Database Data Integrity", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("=" * 70)
        print("COMPREHENSIVE SYSTEM TEST - ALL ACCESSORIES")
        print("32-Hour Integration Sprint - Parth's Coach Feedback Component")
        print("=" * 70)
        print()
        
        tests = [
            self.test_server_connectivity,
            self.test_health_endpoint,
            self.test_database_schema,
            self.test_coach_feedback_submission,
            self.test_feedback_retrieval,
            self.test_feedback_listing,
            self.test_error_handling,
            self.test_404_handling,
            self.test_score_calculation,
            self.test_database_data_integrity
        ]
        
        for i, test in enumerate(tests, 1):
            print(f"Running Test {i}/10: {test.__doc__.split(':')[1].strip()}")
            test()
            print()
        
        # Print summary
        print("=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        
        for result in self.test_results:
            print(result)
        
        print()
        print(f"TOTAL TESTS: {self.passed + self.failed}")
        print(f"✅ PASSED: {self.passed}")
        print(f"❌ FAILED: {self.failed}")
        print(f"SUCCESS RATE: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        
        if self.failed == 0:
            print()
            print("🎉 ALL SYSTEMS OPERATIONAL!")
            print("✅ Coach Feedback Component is 100% functional")
            print("✅ All accessories are working correctly")
            print("✅ Ready for team integration!")
        else:
            print()
            print("⚠️  Some tests failed - review and fix issues")

if __name__ == "__main__":
    tester = ComprehensiveTest()
    tester.run_all_tests()