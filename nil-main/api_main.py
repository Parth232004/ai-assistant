#!/usr/bin/env python3
"""
Main API Integration - Combines all team members' endpoints with Nilesh's metrics

This integrates:
1. Chandresh's embedding and search endpoints
2. Nilesh's metrics and logging middleware
3. Placeholders for Noopur and Parth's endpoints
4. Unified API documentation
"""

from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Import existing services
from embedding_service import embedding_service
from metrics_service import metrics_service

# Import existing API models
from api_chandresh import (
    SearchSimilarRequest, 
    SearchSimilarResponse, 
    MessageRequest
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedMetricsMiddleware(BaseHTTPMiddleware):
    """Nilesh's unified middleware that logs all API calls."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip documentation endpoints
        skip_endpoints = ["/docs", "/openapi.json", "/favicon.ico", "/redoc"]
        if any(request.url.path.startswith(skip) for skip in skip_endpoints):
            return await call_next(request)
        
        start_time = time.time()
        status_code = 200
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except HTTPException as e:
            status_code = e.status_code
            raise
        except Exception as e:
            status_code = 500
            logger.error(f"Unhandled error in {request.url.path}: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        finally:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Log to Nilesh's metrics system
            metrics_service.log_api_call(
                endpoint=request.url.path,
                status_code=status_code,
                latency_ms=latency_ms
            )

# Create unified FastAPI app
app = FastAPI(
    title="AI Assistant Unified API",
    description="Complete API integrating all team members' work",
    version="1.0.0"
)

# Add Nilesh's metrics middleware
app.add_middleware(UnifiedMetricsMiddleware)

# ============================================================================
# CHANDRESH'S ENDPOINTS (EmbedCore & Recall)
# ============================================================================

@app.post("/api/search_similar", response_model=SearchSimilarResponse)
async def search_similar(request: SearchSimilarRequest):
    """Chandresh's search endpoint with Nilesh's metrics integration."""
    try:
        if not request.summary_id and not request.message_text:
            raise HTTPException(
                status_code=400, 
                detail="Either summary_id or message_text must be provided"
            )
        
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
        
        return SearchSimilarResponse(
            related=related_items,
            query_type=query_type,
            total_found=len(related_items)
        )
        
    except Exception as e:
        logger.error(f"Error in search_similar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/store_embedding")
async def store_embedding(item_type: str, item_id: str, text: str):
    """Chandresh's embedding storage with metrics."""
    try:
        success = embedding_service.store_embedding(item_type, item_id, text)
        
        if success:
            return {"status": "success", "message": f"Embedding stored for {item_type} {item_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to store embedding")
            
    except Exception as e:
        logger.error(f"Error storing embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/embeddings/stats")
async def get_embedding_stats():
    """Chandresh's embedding statistics."""
    try:
        import sqlite3
        
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute('SELECT item_type, COUNT(*) as count FROM embeddings GROUP BY item_type')
        type_counts = dict(cursor.fetchall())
        
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
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NILESH'S ENDPOINTS (Metrics, Logging, Execution Tracking)
# ============================================================================

@app.get("/api/metrics")
async def get_metrics(hours: int = 24):
    """Nilesh's main metrics endpoint."""
    try:
        summary = metrics_service.get_metrics_summary(hours=hours)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        # Format for sprint requirements
        pipeline_metrics = summary.get("pipeline_metrics", {})
        api_metrics = summary.get("api_metrics", {})
        
        return {
            "total_messages": pipeline_metrics.get("total_messages", 0),
            "total_summaries": pipeline_metrics.get("total_summaries", 0),
            "total_tasks": pipeline_metrics.get("total_tasks", 0),
            "total_responses": pipeline_metrics.get("total_responses", 0),
            "avg_latency_ms": api_metrics.get("avg_latency_ms", 0),
            "error_rate": api_metrics.get("error_rate", 0),
            "service_metrics": summary
        }
        
    except Exception as e:
        logger.error(f"Error in get_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/detailed")
async def get_detailed_metrics(hours: int = 24):
    """Nilesh's detailed metrics."""
    try:
        return metrics_service.get_metrics_summary(hours=hours)
    except Exception as e:
        logger.error(f"Error in detailed metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PLACEHOLDER ENDPOINTS FOR OTHER TEAM MEMBERS
# ============================================================================

@app.post("/api/respond")
async def respond_endpoint(task_id: str):
    """Placeholder for Noopur's response endpoint."""
    # This would be implemented by Noopur
    return {
        "message": "Noopur's /api/respond endpoint - To be implemented",
        "task_id": task_id,
        "owner": "noopur",
        "status": "placeholder"
    }

@app.post("/api/coach_feedback")
async def coach_feedback_endpoint(summary_id: str, task_id: str, response_id: str, scores: Dict[str, int], comment: str):
    """Placeholder for Parth's coach feedback endpoint."""
    # This would be implemented by Parth
    return {
        "message": "Parth's /api/coach_feedback endpoint - To be implemented",
        "summary_id": summary_id,
        "task_id": task_id,
        "response_id": response_id,
        "owner": "parth",
        "status": "placeholder"
    }

# ============================================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Unified health check."""
    return {
        "status": "healthy",
        "services": {
            "chandresh_embeddings": "active",
            "nilesh_metrics": "active",
            "noopur_responder": "placeholder",
            "parth_coach": "placeholder"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def service_status():
    """Detailed service status."""
    try:
        metrics_summary = metrics_service.get_metrics_summary(hours=1)
        
        return {
            "overall_status": "operational",
            "services": {
                "embedding_service": {
                    "status": "active",
                    "owner": "chandresh",
                    "endpoints": ["/api/search_similar", "/api/store_embedding"]
                },
                "metrics_service": {
                    "status": "active", 
                    "owner": "nilesh",
                    "endpoints": ["/api/metrics"]
                },
                "responder_service": {
                    "status": "placeholder",
                    "owner": "noopur",
                    "endpoints": ["/api/respond"]
                },
                "coach_service": {
                    "status": "placeholder",
                    "owner": "parth", 
                    "endpoints": ["/api/coach_feedback"]
                }
            },
            "metrics_summary": metrics_summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in service status: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)  # Main unified API port