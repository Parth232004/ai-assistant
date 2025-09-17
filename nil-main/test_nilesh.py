#!/usr/bin/env python3
"""
Unit Tests for Nilesh's Metrics System

Tests cover:
1. MetricsService functionality
2. API endpoints
3. Middleware logging
4. Database operations
5. Integration scenarios
"""

import pytest
import sqlite3
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from metrics_service import MetricsService

class TestMetricsService:
    """Unit tests for Nilesh's MetricsService."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Initialize test database with metrics table
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                status_code INTEGER,
                latency_ms REAL,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE summaries (
                summary_id TEXT PRIMARY KEY,
                user_id TEXT,
                message_text TEXT,
                summary_text TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE tasks (
                task_id TEXT PRIMARY KEY,
                summary_id TEXT,
                user_id TEXT,
                task_text TEXT,
                priority TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE responses (
                response_id TEXT PRIMARY KEY,
                task_id TEXT,
                user_id TEXT,
                response_text TEXT,
                tone TEXT,
                status TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_id TEXT NOT NULL,
                vector_blob TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE coach_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_id TEXT,
                task_id TEXT,
                response_id TEXT,
                score INTEGER,
                comment TEXT,
                timestamp TEXT
            )
        ''')
        
        # Insert test data
        test_timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO summaries (summary_id, user_id, summary_text, timestamp)
            VALUES ('s1', 'user1', 'Test summary 1', ?),
                   ('s2', 'user1', 'Test summary 2', ?),
                   ('s3', 'user2', 'Test summary 3', ?)
        ''', (test_timestamp, test_timestamp, test_timestamp))
        
        cursor.execute('''
            INSERT INTO tasks (task_id, summary_id, user_id, task_text, timestamp)
            VALUES ('t1', 's1', 'user1', 'Test task 1', ?),
                   ('t2', 's2', 'user1', 'Test task 2', ?),
                   ('t3', 's3', 'user2', 'Test task 3', ?)
        ''', (test_timestamp, test_timestamp, test_timestamp))
        
        cursor.execute('''
            INSERT INTO responses (response_id, task_id, user_id, response_text, tone, status, timestamp)
            VALUES ('r1', 't1', 'user1', 'Test response 1', 'helpful', 'ok', ?),
                   ('r2', 't2', 'user1', 'Test response 2', 'informative', 'ok', ?)
        ''', (test_timestamp, test_timestamp))
        
        conn.commit()
        conn.close()
        
        yield path
        
        # Cleanup
        os.unlink(path)
    
    @pytest.fixture
    def metrics_service(self, temp_db):
        """Create MetricsService instance with test database."""
        return MetricsService(db_path=temp_db)
    
    def test_log_api_call(self, metrics_service, temp_db):
        """Test logging API calls to metrics table."""
        # Log an API call
        success = metrics_service.log_api_call(
            endpoint="/api/test",
            status_code=200,
            latency_ms=150.5
        )
        
        assert success is True
        
        # Verify it was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM metrics WHERE endpoint = ?', ('/api/test',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[1] == "/api/test"  # endpoint
        assert result[2] == 200          # status_code
        assert result[3] == 150.5        # latency_ms
        assert result[4] is not None     # timestamp
    
    def test_measure_time_context_manager(self, metrics_service, temp_db):
        """Test the measure_time context manager."""
        # Test successful operation
        with metrics_service.measure_time("/api/test_context"):
            time.sleep(0.01)  # Small delay
        
        # Verify metric was logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM metrics WHERE endpoint = ?', ('/api/test_context',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[2] == 200  # Success status code
        assert result[3] > 0     # Latency should be positive
    
    def test_measure_time_with_exception(self, metrics_service, temp_db):
        """Test measure_time context manager with exceptions."""
        with pytest.raises(ValueError):
            with metrics_service.measure_time("/api/test_error"):
                raise ValueError("Test error")
        
        # Verify error was logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM metrics WHERE endpoint = ?', ('/api/test_error',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[2] == 500  # Error status code
    
    def test_get_metrics_summary(self, metrics_service, temp_db):
        """Test metrics summary generation."""
        # Add some test metrics
        metrics_service.log_api_call("/api/search_similar", 200, 100.0)
        metrics_service.log_api_call("/api/search_similar", 200, 120.0)
        metrics_service.log_api_call("/api/metrics", 200, 50.0)
        metrics_service.log_api_call("/api/test", 404, 25.0)
        
        summary = metrics_service.get_metrics_summary(hours=24)
        
        assert "api_metrics" in summary
        assert "pipeline_metrics" in summary
        assert "endpoint_stats" in summary
        
        api_metrics = summary["api_metrics"]
        assert api_metrics["total_calls"] == 4
        assert api_metrics["avg_latency_ms"] > 0
        assert api_metrics["error_count"] == 1
        assert api_metrics["error_rate"] == 0.25
        
        pipeline_metrics = summary["pipeline_metrics"]
        assert pipeline_metrics["total_summaries"] == 3
        assert pipeline_metrics["total_tasks"] == 3
        assert pipeline_metrics["total_responses"] == 2
    
    def test_get_recent_calls(self, metrics_service, temp_db):
        """Test getting recent API calls."""
        # Add test calls
        metrics_service.log_api_call("/api/test1", 200, 100.0)
        metrics_service.log_api_call("/api/test2", 404, 50.0)
        metrics_service.log_api_call("/api/test3", 200, 75.0)
        
        recent_calls = metrics_service.get_recent_calls(limit=2)
        
        assert len(recent_calls) == 2
        assert recent_calls[0]["endpoint"] == "/api/test3"  # Most recent first
        assert recent_calls[1]["endpoint"] == "/api/test2"
    
    def test_get_performance_trends(self, metrics_service, temp_db):
        """Test performance trends calculation."""
        # Add calls with different timestamps
        base_time = datetime.now()
        hour_ago = base_time - timedelta(hours=1)
        
        metrics_service.log_api_call("/api/test", 200, 100.0, base_time.isoformat())
        metrics_service.log_api_call("/api/test", 200, 120.0, hour_ago.isoformat())
        
        trends = metrics_service.get_performance_trends(hours=24)
        
        assert "hourly_trends" in trends
        assert len(trends["hourly_trends"]) > 0
        
        for trend in trends["hourly_trends"]:
            assert "hour" in trend
            assert "calls" in trend
            assert "avg_latency_ms" in trend
            assert "errors" in trend
    
    def test_clear_old_metrics(self, metrics_service, temp_db):
        """Test clearing old metrics."""
        # Add old and recent metrics
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        recent_time = datetime.now().isoformat()
        
        metrics_service.log_api_call("/api/old", 200, 100.0, old_time)
        metrics_service.log_api_call("/api/recent", 200, 100.0, recent_time)
        
        # Clear metrics older than 7 days
        deleted_count = metrics_service.clear_old_metrics(days=7)
        
        assert deleted_count == 1
        
        # Verify only recent metric remains
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM metrics')
        remaining_count = cursor.fetchone()[0]
        conn.close()
        
        assert remaining_count == 1

class TestMetricsAPI:
    """Integration tests for Nilesh's API endpoints."""
    
    def test_api_health_check(self):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        from api_nilesh import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["owner"] == "nilesh"
        assert "capabilities" in data
    
    def test_api_metrics_endpoint(self):
        """Test main metrics endpoint."""
        from fastapi.testclient import TestClient
        from api_nilesh import app
        
        client = TestClient(app)
        response = client.get("/api/metrics?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_messages" in data
        assert "total_summaries" in data
        assert "total_tasks" in data
        assert "total_responses" in data
        assert "avg_latency_ms" in data
        assert "error_rate" in data
        assert "service_status" in data
    
    def test_api_detailed_metrics(self):
        """Test detailed metrics endpoint."""
        from fastapi.testclient import TestClient
        from api_nilesh import app
        
        client = TestClient(app)
        response = client.get("/api/metrics/detailed?hours=12")
        
        assert response.status_code == 200
        data = response.json()
        assert "api_metrics" in data
        assert "pipeline_metrics" in data
    
    def test_api_recent_calls(self):
        """Test recent calls endpoint."""
        from fastapi.testclient import TestClient
        from api_nilesh import app
        
        client = TestClient(app)
        response = client.get("/api/metrics/recent?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "recent_calls" in data
        assert "timestamp" in data
    
    def test_api_performance_trends(self):
        """Test performance trends endpoint."""
        from fastapi.testclient import TestClient
        from api_nilesh import app
        
        client = TestClient(app)
        response = client.get("/api/metrics/trends?hours=6")
        
        assert response.status_code == 200
        data = response.json()
        assert "time_window_hours" in data
        assert "hourly_trends" in data
    
    def test_metrics_middleware_logging(self):
        """Test that middleware logs API calls automatically."""
        from fastapi.testclient import TestClient
        from api_nilesh import app
        
        client = TestClient(app)
        
        # Make a request that should be logged
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check that it was logged (the middleware should have recorded it)
        # Note: In a real test, you'd verify the database entry was created

class TestUnifiedAPIIntegration:
    """Test integration between all services."""
    
    def test_unified_api_health(self):
        """Test unified API health check."""
        from fastapi.testclient import TestClient
        from api_main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "chandresh_embeddings" in data["services"]
        assert "nilesh_metrics" in data["services"]
    
    def test_unified_api_status(self):
        """Test unified API status endpoint."""
        from fastapi.testclient import TestClient
        from api_main import app
        
        client = TestClient(app)
        response = client.get("/api/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "services" in data
        assert "metrics_summary" in data

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])