#!/opt/anaconda3/bin/python
"""
Simple integration test for coach_feedback component
32-Hour Integration Sprint - Parth's deliverable
"""

import unittest
import sqlite3
import os
from pi.api.coach_feedback import (
    calculate_aggregate_score,
    auto_score_clarity, 
    auto_score_relevance
)

class TestCoachFeedbackCore(unittest.TestCase):
    """Test core coach feedback functionality without database mocking"""
    
    def test_calculate_aggregate_score(self):
        """Test score aggregation logic"""
        scores = {"clarity": 4, "relevance": 5, "tone": 3}
        result = calculate_aggregate_score(scores)
        self.assertEqual(result, 12, "Aggregate score should be sum of all scores")
        
        # Test with missing scores
        incomplete_scores = {"clarity": 4}
        result = calculate_aggregate_score(incomplete_scores)
        self.assertEqual(result, 4, "Should handle missing scores gracefully")
        
        # Test edge cases
        empty_scores = {}
        result = calculate_aggregate_score(empty_scores)
        self.assertEqual(result, 0, "Empty scores should return 0")
    
    def test_auto_scoring_algorithms(self):
        """Test auto-scoring functions"""
        # Test clarity scoring
        clarity_score = auto_score_clarity("test_summary_id")
        self.assertIn(clarity_score, [2, 3, 4], "Clarity score should be in valid range")
        self.assertIsInstance(clarity_score, int, "Clarity score should be integer")
        
        # Test relevance scoring  
        relevance_score = auto_score_relevance("test_task_id", "test_response_id")
        self.assertEqual(relevance_score, 4, "Default relevance score should be 4")
        self.assertIsInstance(relevance_score, int, "Relevance score should be integer")
    
    def test_database_exists(self):
        """Test that the main database exists and has coach_feedback table"""
        db_path = "assistant_demo.db"
        self.assertTrue(os.path.exists(db_path), "Database should exist")
        
        # Check table structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if coach_feedback table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coach_feedback'")
        table_exists = cursor.fetchone()
        self.assertIsNotNone(table_exists, "coach_feedback table should exist")
        
        # Check columns
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
    
    def test_database_has_data(self):
        """Test that our API test actually stored data"""
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM coach_feedback")
        count = cursor.fetchone()[0]
        
        self.assertGreater(count, 0, "Should have at least one feedback entry from API test")
        
        # Check data structure
        cursor.execute("SELECT * FROM coach_feedback LIMIT 1")
        sample_record = cursor.fetchone()
        
        self.assertIsNotNone(sample_record, "Should have sample data")
        self.assertEqual(len(sample_record), 10, "Record should have 10 fields")
        
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("COACH FEEDBACK CORE TESTS") 
    print("32-Hour Integration Sprint - Parth's Component")
    print("Testing core functionality and database integration")
    print("=" * 60)
    
    unittest.main(verbosity=2)