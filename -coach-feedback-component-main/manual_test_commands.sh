#!/bin/bash
# Manual Test Commands for Coach Feedback API
# Copy and paste these commands into your terminal

echo "🧪 Manual API Test Commands"
echo "=========================="

echo ""
echo "1. Health Check:"
echo "curl -s http://localhost:8001/health | python -m json.tool"

echo ""
echo "2. Submit Feedback:"
echo 'curl -X POST http://localhost:8001/api/coach_feedback \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "summary_id": "manual_test_123",
    "task_id": "task_456", 
    "response_id": "resp_789",
    "scores": {"clarity": 4, "relevance": 5, "tone": 3},
    "comment": "Manual test feedback"
  }'"'"' | python -m json.tool'

echo ""
echo "3. List All Feedback:"
echo 'curl -s "http://localhost:8001/api/coach_feedback?limit=5" | python -m json.tool'

echo ""
echo "4. Get Specific Feedback (replace FEEDBACK_ID):"
echo "curl -s http://localhost:8001/api/coach_feedback/FEEDBACK_ID | python -m json.tool"

echo ""
echo "5. Test Error Handling:"
echo 'curl -X POST http://localhost:8001/api/coach_feedback \
  -H "Content-Type: application/json" \
  -d '"'"'{"summary_id": "test"}'"'"' | python -m json.tool'

echo ""
echo "6. Test 404 Handling:"
echo "curl -s http://localhost:8001/api/coach_feedback/nonexistent | python -m json.tool"

echo ""
echo "7. Check Database:"
echo 'sqlite3 assistant_demo.db "SELECT COUNT(*) as total, AVG(score) as avg_score FROM coach_feedback;"'