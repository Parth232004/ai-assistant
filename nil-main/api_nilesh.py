#!/usr/bin/env python3
"""
Nilesh's API Endpoints - Metrics, Logging, and Execution Tracking

This module provides:
1. GET /api/metrics - Main metrics endpoint
2. Middleware for automatic API call logging
3. Performance monitoring endpoints
4. Health and status reporting
"""

from fastapi import FastAPI, HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import logging
from datetime import datetime

from metrics_service import metrics_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log all API calls to metrics table."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for some endpoints to avoid recursion
        skip_endpoints = ["/docs", "/openapi.json", "/favicon.ico"]
        if any(request.url.path.startswith(skip) for skip in skip_endpoints):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error(f"Error processing request {request.url.path}: {e}")
            raise
        finally:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Log the API call
            metrics_service.log_api_call(
                endpoint=request.url.path,
                status_code=status_code,
                latency_ms=latency_ms
            )
        
        return response

# Create FastAPI app with metrics middleware
app = FastAPI(title="AI Assistant API - Nilesh's Metrics Endpoints", version="1.0.0")
app.add_middleware(MetricsMiddleware)

class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    total_messages: int
    total_summaries: int
    total_tasks: int
    total_responses: int
    total_embeddings: int
    total_feedback: int
    avg_latency_ms: float
    error_rate: float
    api_metrics: Dict[str, Any]
    endpoint_stats: List[Dict[str, Any]]
    service_status: str
    timestamp: str

class PerformanceTrendsResponse(BaseModel):
    """Response model for performance trends."""
    time_window_hours: int
    hourly_trends: List[Dict[str, Any]]

@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics(hours: int = 24):
    """
    Nilesh's main endpoint: Get comprehensive metrics summary.
    
    Returns:
    - total_messages, total_summaries, total_tasks, total_responses
    - avg_latency_ms, error_rate
    - API call statistics
    - Service status
    """
    try:
        summary = metrics_service.get_metrics_summary(hours=hours)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        # Format response according to sprint requirements
        pipeline_metrics = summary.get("pipeline_metrics", {})
        api_metrics = summary.get("api_metrics", {})
        
        return MetricsResponse(
            total_messages=pipeline_metrics.get("total_messages", 0),
            total_summaries=pipeline_metrics.get("total_summaries", 0),
            total_tasks=pipeline_metrics.get("total_tasks", 0),
            total_responses=pipeline_metrics.get("total_responses", 0),
            total_embeddings=pipeline_metrics.get("total_embeddings", 0),
            total_feedback=pipeline_metrics.get("total_feedback", 0),
            avg_latency_ms=api_metrics.get("avg_latency_ms", 0),
            error_rate=api_metrics.get("error_rate", 0),
            api_metrics=api_metrics,
            endpoint_stats=summary.get("endpoint_stats", []),
            service_status=summary.get("service_status", "unknown"),
            timestamp=summary.get("timestamp", datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Error in get_metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/metrics/detailed")
async def get_detailed_metrics(hours: int = 24):
    """Get detailed metrics with full breakdown."""
    try:
        return metrics_service.get_metrics_summary(hours=hours)
    except Exception as e:
        logger.error(f"Error in get_detailed_metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/metrics/recent")
async def get_recent_calls(limit: int = 50):
    """Get recent API calls for monitoring."""
    try:
        return {
            "recent_calls": metrics_service.get_recent_calls(limit=limit),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in get_recent_calls: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/metrics/trends", response_model=PerformanceTrendsResponse)
async def get_performance_trends(hours: int = 24):
    """Get performance trends over time."""
    try:
        trends = metrics_service.get_performance_trends(hours=hours)
        
        if "error" in trends:
            raise HTTPException(status_code=500, detail=trends["error"])
        
        return PerformanceTrendsResponse(**trends)
        
    except Exception as e:
        logger.error(f"Error in get_performance_trends: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/metrics/clear")
async def clear_old_metrics(days: int = 7):
    """Clear old metrics data."""
    try:
        deleted_count = metrics_service.clear_old_metrics(days=days)
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Cleared metrics older than {days} days"
        }
    except Exception as e:
        logger.error(f"Error clearing metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/status")
async def get_service_status():
    """Get overall service status and health."""
    try:
        summary = metrics_service.get_metrics_summary(hours=1)  # Last hour
        
        return {
            "service": "metrics_service",
            "owner": "nilesh",
            "status": "healthy",
            "uptime_check": "ok",
            "recent_activity": summary.get("api_metrics", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in service status: {e}")
        return {
            "service": "metrics_service",
            "owner": "nilesh", 
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Health check (same pattern as other services)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "metrics_service",
        "owner": "nilesh",
        "capabilities": ["metrics", "logging", "monitoring"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port from Chandresh