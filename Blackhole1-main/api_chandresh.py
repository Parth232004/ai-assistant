from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from embedding_service import embedding_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Assistant API - Chandresh's Endpoints", version="1.0.0")

class SearchSimilarRequest(BaseModel):
    """Request model for search_similar endpoint."""
    summary_id: Optional[str] = None
    message_text: Optional[str] = None
    top_k: Optional[int] = 3

class SearchSimilarResponse(BaseModel):
    """Response model for search_similar endpoint."""
    related: List[Dict[str, Any]]
    query_type: str
    total_found: int

class MessageRequest(BaseModel):
    """Request model for message-based search."""
    message_text: str
    user_id: Optional[str] = None

@app.post("/api/search_similar", response_model=SearchSimilarResponse)
async def search_similar(request: SearchSimilarRequest):
    """
    Chandresh's main endpoint: Search for similar summaries/tasks.
    
    Input: { "summary_id": "s123" } or { "message_text": "some text" }
    Output: { "related": [{ "item_type": "summary", "item_id": "s456", "score": 0.87, "text": "..." }] }
    """
    try:
        # Validate input
        if not request.summary_id and not request.message_text:
            raise HTTPException(
                status_code=400, 
                detail="Either summary_id or message_text must be provided"
            )
        
        # Search for similar items
        if request.summary_id:
            related_items = embedding_service.search_similar_items(
                summary_id=request.summary_id, 
                top_k=request.top_k
            )
            query_type = "summary_id"
        else:
            related_items = embedding_service.search_similar_items(
                query_text=request.message_text, 
                top_k=request.top_k
            )
            query_type = "message_text"
        
        logger.info(f"Found {len(related_items)} similar items for {query_type}")
        
        return SearchSimilarResponse(
            related=related_items,
            query_type=query_type,
            total_found=len(related_items)
        )
        
    except Exception as e:
        logger.error(f"Error in search_similar: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/store_embedding")
async def store_embedding(item_type: str, item_id: str, text: str):
    """
    Utility endpoint to manually store embeddings.
    Used for integration with Seeya's summarize endpoint.
    """
    try:
        success = embedding_service.store_embedding(item_type, item_id, text)
        
        if success:
            return {"status": "success", "message": f"Embedding stored for {item_type} {item_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to store embedding")
            
    except Exception as e:
        logger.error(f"Error storing embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/embeddings/stats")
async def get_embedding_stats():
    """Get statistics about stored embeddings."""
    try:
        import sqlite3
        
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        # Count embeddings by type
        cursor.execute('''
            SELECT item_type, COUNT(*) as count 
            FROM embeddings 
            GROUP BY item_type
        ''')
        
        type_counts = dict(cursor.fetchall())
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_embeddings": total_count,
            "by_type": type_counts,
            "service_status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/reindex")
async def trigger_reindex():
    """Trigger reindexing of all summaries and tasks."""
    try:
        summary_count = embedding_service.index_existing_summaries()
        task_count = embedding_service.index_existing_tasks()
        
        return {
            "status": "success",
            "summaries_indexed": summary_count,
            "tasks_indexed": task_count,
            "total_indexed": summary_count + task_count
        }
        
    except Exception as e:
        logger.error(f"Error during reindexing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "embedding_service", "owner": "chandresh"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)