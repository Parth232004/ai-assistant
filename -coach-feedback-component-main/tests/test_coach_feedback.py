#!/opt/anaconda3/bin/python
"""
Unit tests for coach_feedback component
32-Hour Integration Sprint - Parth's deliverable
Tests feedback persistence and coach score logic
"""

import unittest
import sqlite3
import os
import tempfile
from datetime import datetime
from pi.api.coach_feedback import (
    coach_feedback, 
    FeedbackRequest,
    calculate_aggregate_score,
    auto_score_clarity,
    auto_score_relevance,
    init_coach_feedback_table
)

class TestCoachFeedback(unittest.TestCase):
    """Unit tests for coach feedback functionality"""
    
    def setUp(self):
        """Set up test database"""
        # Use a temporary database for testing
        self.test_db = "test_assistant_demo.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Patch the database connection to use test database
        import pi.api.coach_feedback
        pi.api.coach_feedback.sqlite3.connect = lambda x: sqlite3.connect(self.test_db)
        
        # Initialize tables
        init_coach_feedback_table()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_calculate_aggregate_score(self):
        """Test score aggregation logic"""
        scores = {"clarity": 4, "relevance": 5, "tone": 3}
        result = calculate_aggregate_score(scores)
        self.assertEqual(result, 12, "Aggregate score should be sum of all scores")
        
        # Test with missing scores
        incomplete_scores = {"clarity": 4}
        result = calculate_aggregate_score(incomplete_scores)
        self.assertEqual(result, 4, "Should handle missing scores gracefully")
    
    def test_feedback_persistence(self):
        """Test that feedback is correctly stored in database"""
        # Create test feedback request
        feedback_req = FeedbackRequest(
            summary_id="test_s123",
            task_id="test_t456", 
            response_id="test_r789",
            scores={"clarity": 4, "relevance": 5, "tone": 3},
            comment="Test feedback comment"
        )
        
        # Submit feedback
        result = coach_feedback(feedback_req)
        
        # Verify response
        self.assertIsNotNone(result.feedback_id)
        self.assertEqual(result.score, 12)
        self.assertTrue(result.stored)
        
        # Verify database storage
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM coach_feedback WHERE id = ?", (result.feedback_id,))
        db_record = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(db_record, "Feedback should be stored in database")
        self.assertEqual(db_record[1], "test_s123")  # summary_id
        self.assertEqual(db_record[2], "test_t456")  # task_id
        self.assertEqual(db_record[3], "test_r789")  # response_id
        self.assertEqual(db_record[4], 12)           # score
        self.assertEqual(db_record[6], 4)            # clarity_score
        self.assertEqual(db_record[7], 5)            # relevance_score
        self.assertEqual(db_record[8], 3)            # tone_score
    
    def test_auto_scoring_logic(self):
        """Test auto-scoring algorithms"""
        # Test clarity scoring (placeholder test since it needs summaries table)
        clarity_score = auto_score_clarity("test_summary")
        self.assertIn(clarity_score, [2, 3, 4], "Clarity score should be in valid range")
        
        # Test relevance scoring (placeholder)
        relevance_score = auto_score_relevance("test_task", "test_response")
        self.assertEqual(relevance_score, 4, "Default relevance score should be 4")
    
    def test_invalid_feedback_data(self):
        """Test error handling for invalid feedback data"""
        with self.assertRaises(Exception):
            # This should fail due to validation
            invalid_req = FeedbackRequest(
                summary_id="",  # Empty string should cause issues
                task_id="test_t456",
                response_id="test_r789", 
                scores={"clarity": 6},  # Score out of range (though not enforced yet)
                comment="Test"
            )
            coach_feedback(invalid_req)
    
    def test_database_schema(self):
        """Test that database schema is created correctly"""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coach_feedback'")
        table_exists = cursor.fetchone()
        self.assertIsNotNone(table_exists, "coach_feedback table should exist")
        
        # Check table structure
        cursor.execute("PRAGMA table_info(coach_feedback)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = [
            'id', 'summary_id', 'task_id', 'response_id', 'score',
            'comment', 'clarity_score', 'relevance_score', 'tone_score', 'timestamp'
        ]
        
        for expected_col in expected_columns:
            self.assertIn(expected_col, column_names, f"Column {expected_col} should exist")
        
        conn.close()
    
    def test_multiple_feedback_entries(self):
        """Test storing multiple feedback entries"""
        # Submit multiple feedback entries
        for i in range(3):
            feedback_req = FeedbackRequest(
                summary_id=f"s{i}",
                task_id=f"t{i}",
                response_id=f"r{i}",
                scores={"clarity": 3+i, "relevance": 4, "tone": 2+i},
                comment=f"Test comment {i}"
            )
            result = coach_feedback(feedback_req)
            self.assertTrue(result.stored)
        
        # Verify all entries were stored
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM coach_feedback")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 3, "Should have 3 feedback entries in database")

class TestIntegrationPoints(unittest.TestCase):
    """Test integration points with other components"""
    
    def test_api_contract_compliance(self):
        """Test that API matches sprint specifications"""
        # Test input contract
        expected_input_fields = ['summary_id', 'task_id', 'response_id', 'scores', 'comment']
        feedback_req = FeedbackRequest(
            summary_id="s123",
            task_id="t123", 
            response_id="r123",
            scores={"clarity": 4, "relevance": 5, "tone": 4},
            comment="Test comment"
        )
        
        for field in expected_input_fields:
            self.assertTrue(hasattr(feedback_req, field), f"Input should have {field} field")
        
        # Test output contract format
        # Expected: {"feedback_id":"f123", "score":13, "stored":true}
        # This would be tested in integration tests with actual HTTP requests

if __name__ == "__main__":
    print("=" * 60)
    print("COACH FEEDBACK UNIT TESTS")
    print("32-Hour Integration Sprint - Parth's Component")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2)