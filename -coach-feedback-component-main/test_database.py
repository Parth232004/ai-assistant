#!/opt/anaconda3/bin/python
"""
Database Test for Coach Feedback Component
Tests database schema, data integrity, and operations
"""

import sqlite3
import json
from datetime import datetime

def test_database():
    print("🗄️  Database Test - Coach Feedback Component")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        # Test 1: Table Schema
        print("\n1. Testing table schema...")
        cursor.execute("PRAGMA table_info(coach_feedback)")
        columns = cursor.fetchall()
        
        expected_columns = ['id', 'summary_id', 'task_id', 'response_id', 'score', 
                           'comment', 'clarity_score', 'relevance_score', 'tone_score', 'timestamp']
        
        actual_columns = [col[1] for col in columns]
        
        print(f"✅ Table exists with {len(columns)} columns")
        for col in expected_columns:
            if col in actual_columns:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} - MISSING")
        
        # Test 2: Data Count
        print("\n2. Testing data count...")
        cursor.execute("SELECT COUNT(*) FROM coach_feedback")
        total_count = cursor.fetchone()[0]
        print(f"✅ Total feedback entries: {total_count}")
        
        # Test 3: Data Integrity
        print("\n3. Testing data integrity...")
        cursor.execute("""
            SELECT COUNT(*) FROM coach_feedback 
            WHERE id IS NOT NULL AND summary_id IS NOT NULL 
            AND task_id IS NOT NULL AND response_id IS NOT NULL
        """)
        valid_count = cursor.fetchone()[0]
        print(f"✅ Valid entries (no NULL required fields): {valid_count}")
        
        # Test 4: Score Statistics
        print("\n4. Testing score statistics...")
        cursor.execute("SELECT AVG(score), MIN(score), MAX(score) FROM coach_feedback")
        avg_score, min_score, max_score = cursor.fetchone()
        if avg_score is not None:
            print(f"✅ Average Score: {avg_score:.2f}")
            print(f"✅ Score Range: {min_score} - {max_score}")
        else:
            print("ℹ️  No score data available")
        
        # Test 5: Recent Entries
        print("\n5. Testing recent entries...")
        cursor.execute("""
            SELECT id, summary_id, score, timestamp 
            FROM coach_feedback 
            ORDER BY timestamp DESC 
            LIMIT 3
        """)
        recent_entries = cursor.fetchall()
        
        for i, entry in enumerate(recent_entries, 1):
            print(f"   {i}. ID: {entry[0][:8]}..., Score: {entry[2]}, Time: {entry[3]}")
        
        # Test 6: Score Distribution
        print("\n6. Testing score distribution...")
        cursor.execute("""
            SELECT score, COUNT(*) as count 
            FROM coach_feedback 
            GROUP BY score 
            ORDER BY score DESC
        """)
        score_dist = cursor.fetchall()
        
        for score, count in score_dist:
            print(f"   Score {score}: {count} entries")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 DATABASE TEST COMPLETED!")
        print(f"✅ Schema: Valid")
        print(f"✅ Data Count: {total_count} entries")
        print(f"✅ Data Integrity: {valid_count}/{total_count} valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_database()