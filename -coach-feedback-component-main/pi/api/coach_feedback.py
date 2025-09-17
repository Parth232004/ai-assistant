#!/opt/anaconda3/bin/python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import uuid

router = APIRouter()

class FeedbackRequest(BaseModel):
    summary_id: str
    task_id: str
    response_id: str
    scores: dict  # Expected: {"clarity": int, "relevance": int, "tone": int}
    comment: str

class FeedbackResponse(BaseModel):
    feedback_id: str
    score: int
    stored: bool

def init_coach_feedback_table():
    """Initialize the coach_feedback table if it doesn't exist"""
    conn = sqlite3.connect("assistant_demo.db")
    cursor = conn.cursor()
    
    # Create coach_feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coach_feedback (
            id TEXT PRIMARY KEY,
            summary_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            response_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            comment TEXT,
            clarity_score INTEGER,
            relevance_score INTEGER,
            tone_score INTEGER,
            timestamp TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def calculate_aggregate_score(scores: dict) -> int:
    """Calculate aggregate score from individual scores"""
    # Expected scores: clarity, relevance, tone (each 1-5)
    clarity = scores.get("clarity", 0)
    relevance = scores.get("relevance", 0)
    tone = scores.get("tone", 0)
    
    # Simple aggregate: sum of all scores
    return clarity + relevance + tone

def auto_score_clarity(summary_id: str) -> int:
    """Auto-scoring logic for clarity based on summary length/key phrases"""
    try:
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        # Try to get summary text (assuming summaries table exists)
        cursor.execute("SELECT summary_text FROM summaries WHERE summary_id = ?", (summary_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            summary_text = result[0]
            # Simple clarity scoring based on length and structure
            word_count = len(summary_text.split())
            if word_count < 10:
                return 2  # Too short
            elif word_count > 200:
                return 3  # Too long
            else:
                return 4  # Good length
        return 3  # Default if no summary found
    except:
        return 3  # Default score if error

def auto_score_relevance(task_id: str, response_id: str) -> int:
    """Auto-scoring logic for relevance via similarity (placeholder for Chandresh integration)"""
    # Placeholder for similarity scoring with Chandresh's /api/search_similar
    # TODO: Integrate with Chandresh's similarity scoring
    return 4  # Default good relevance score

@router.post("/api/coach_feedback", response_model=FeedbackResponse)
def coach_feedback(req: FeedbackRequest):
    """Store coach feedback and return aggregated score"""
    try:
        # Initialize table if needed
        init_coach_feedback_table()
        
        # Generate feedback ID
        feedback_id = f"f{uuid.uuid4().hex[:7]}"
        
        # Calculate aggregate score
        aggregate_score = calculate_aggregate_score(req.scores)
        
        # Get timestamp
        timestamp = datetime.now().isoformat()
        
        # Store feedback in database
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO coach_feedback 
            (id, summary_id, task_id, response_id, score, comment, 
             clarity_score, relevance_score, tone_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_id,
            req.summary_id,
            req.task_id, 
            req.response_id,
            aggregate_score,
            req.comment,
            req.scores.get("clarity", 0),
            req.scores.get("relevance", 0),
            req.scores.get("tone", 0),
            timestamp
        ))
        
        conn.commit()
        conn.close()
        
        # Optional: Send reward update to Chandresh endpoint (RL integration)
        # TODO: Implement /api/rl_reward POST hook
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            score=aggregate_score,
            stored=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing feedback: {str(e)}")

@router.get("/api/coach_feedback/{feedback_id}")
def get_coach_feedback(feedback_id: str):
    """Retrieve specific coach feedback by ID"""
    try:
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, summary_id, task_id, response_id, score, comment,
                   clarity_score, relevance_score, tone_score, timestamp
            FROM coach_feedback WHERE id = ?
        """, (feedback_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        return {
            "feedback_id": result[0],
            "summary_id": result[1],
            "task_id": result[2],
            "response_id": result[3],
            "score": result[4],
            "comment": result[5],
            "scores": {
                "clarity": result[6],
                "relevance": result[7],
                "tone": result[8]
            },
            "timestamp": result[9]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving feedback: {str(e)}")

@router.get("/api/coach_feedback")
def list_coach_feedback(limit: int = 10):
    """List recent coach feedback entries"""
    try:
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, summary_id, task_id, response_id, score, comment,
                   clarity_score, relevance_score, tone_score, timestamp
            FROM coach_feedback 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for result in results:
            feedback_list.append({
                "feedback_id": result[0],
                "summary_id": result[1],
                "task_id": result[2],
                "response_id": result[3],
                "score": result[4],
                "comment": result[5],
                "scores": {
                    "clarity": result[6],
                    "relevance": result[7],
                    "tone": result[8]
                },
                "timestamp": result[9]
            })
        
        return {"feedback": feedback_list, "count": len(feedback_list)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing feedback: {str(e)}")

# Initialize table on import
init_coach_feedback_table()
