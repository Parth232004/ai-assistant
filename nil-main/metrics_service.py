#!/usr/bin/env python3
"""
Metrics Service - Nilesh's core metrics and logging implementation

This service handles:
1. API call logging to metrics table
2. Performance tracking and aggregation
3. Error rate monitoring
4. Service health metrics
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsService:
    """Service for handling metrics collection and aggregation - Nilesh's core work."""
    
    def __init__(self, db_path: str = "assistant_demo.db"):
        self.db_path = db_path
    
    def log_api_call(self, endpoint: str, status_code: int, latency_ms: float, 
                     timestamp: Optional[str] = None) -> bool:
        """Log an API call to the metrics table."""
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO metrics (endpoint, status_code, latency_ms, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (endpoint, status_code, latency_ms, timestamp))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Logged API call: {endpoint} [{status_code}] {latency_ms:.2f}ms")
            return True
            
        except Exception as e:
            logger.error(f"Error logging API call: {e}")
            return False
    
    @contextmanager
    def measure_time(self, endpoint: str):
        """Context manager to measure API call time and log metrics."""
        start_time = time.time()
        status_code = 200  # Default success
        
        try:
            yield
        except Exception as e:
            status_code = 500  # Server error
            logger.error(f"Error in {endpoint}: {e}")
            raise
        finally:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            self.log_api_call(endpoint, status_code, latency_ms)
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated metrics for the specified time period."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate time window
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Total calls
            cursor.execute('''
                SELECT COUNT(*) FROM metrics 
                WHERE timestamp >= ?
            ''', (start_time,))
            total_calls = cursor.fetchone()[0]
            
            # Average latency
            cursor.execute('''
                SELECT AVG(latency_ms) FROM metrics 
                WHERE timestamp >= ?
            ''', (start_time,))
            avg_latency = cursor.fetchone()[0] or 0
            
            # Error rate
            cursor.execute('''
                SELECT COUNT(*) FROM metrics 
                WHERE timestamp >= ? AND status_code >= 400
            ''', (start_time,))
            error_count = cursor.fetchone()[0]
            error_rate = (error_count / total_calls) if total_calls > 0 else 0
            
            # Calls by endpoint
            cursor.execute('''
                SELECT endpoint, COUNT(*) as count, AVG(latency_ms) as avg_latency
                FROM metrics 
                WHERE timestamp >= ?
                GROUP BY endpoint
                ORDER BY count DESC
            ''', (start_time,))
            endpoint_stats = cursor.fetchall()
            
            # Get counts from other tables for pipeline metrics
            cursor.execute('SELECT COUNT(*) FROM summaries')
            total_summaries = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM tasks')
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM responses')
            total_responses = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM embeddings')
            total_embeddings = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM coach_feedback')
            total_feedback = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "time_window_hours": hours,
                "api_metrics": {
                    "total_calls": total_calls,
                    "avg_latency_ms": round(avg_latency, 2),
                    "error_rate": round(error_rate, 4),
                    "error_count": error_count
                },
                "endpoint_stats": [
                    {
                        "endpoint": endpoint,
                        "calls": count,
                        "avg_latency_ms": round(avg_latency, 2)
                    }
                    for endpoint, count, avg_latency in endpoint_stats
                ],
                "pipeline_metrics": {
                    "total_messages": total_summaries,  # Assuming 1:1 message to summary
                    "total_summaries": total_summaries,
                    "total_tasks": total_tasks,
                    "total_responses": total_responses,
                    "total_embeddings": total_embeddings,
                    "total_feedback": total_feedback
                },
                "service_status": "active",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {
                "error": str(e),
                "service_status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_recent_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent API calls for detailed monitoring."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT endpoint, status_code, latency_ms, timestamp
                FROM metrics
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            calls = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "timestamp": timestamp
                }
                for endpoint, status_code, latency_ms, timestamp in calls
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent calls: {e}")
            return []
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Hourly performance breakdown
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                    COUNT(*) as calls,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
                FROM metrics
                WHERE timestamp >= ?
                GROUP BY strftime('%Y-%m-%d %H:00:00', timestamp)
                ORDER BY hour
            ''', (start_time,))
            
            trends = cursor.fetchall()
            conn.close()
            
            return {
                "time_window_hours": hours,
                "hourly_trends": [
                    {
                        "hour": hour,
                        "calls": calls,
                        "avg_latency_ms": round(avg_latency, 2),
                        "errors": errors,
                        "error_rate": round(errors / calls, 4) if calls > 0 else 0
                    }
                    for hour, calls, avg_latency, errors in trends
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {"error": str(e)}
    
    def clear_old_metrics(self, days: int = 7) -> int:
        """Clear metrics older than specified days."""
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_time,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleared {deleted_count} old metrics entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error clearing old metrics: {e}")
            return 0

# Global instance for use in API
metrics_service = MetricsService()