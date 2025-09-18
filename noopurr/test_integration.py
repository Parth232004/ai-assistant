import os
import sqlite3
import json
import time

import pytest
from fastapi.testclient import TestClient

import importlib.util
import sys
from pathlib import Path

_main_path = Path(__file__).resolve().parent / "main.py"
_spec = importlib.util.spec_from_file_location("assistant_live_demo_main_main", str(_main_path))
_module = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(_module)  # type: ignore
app = getattr(_module, "app")

# The DB is created at process CWD as 'assistant_demo.db'
DB_FILE = os.path.join(os.getcwd(), "assistant_demo.db")


def cleanup_db():
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass


@pytest.fixture(scope="session")
def client():
    # Ensure a fresh DB for the test session
    cleanup_db()
    c = TestClient(app)
    # Trigger startup event to initialize DB
    with c as cl:
        cl.get("/health")
    return c


def test_respond_writes_db(client):
    payload = {"task_id": "t_integration_1", "user_id": "u_test"}
    r = client.post("/api/respond", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert set(["response_id", "task_id", "response_text", "tone", "status", "timestamp"]).issubset(data.keys())

    # verify DB insert
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    row = cur.execute("SELECT response_id, task_id, user_id, status FROM responses WHERE response_id=?", (data["response_id"],)).fetchone()
    conn.close()
    assert row is not None
    assert row[1] == payload["task_id"]
    assert row[2] == payload["user_id"]


def test_store_embedding_and_search(client):
    # Seed two embeddings
    r1 = client.post("/api/store_embedding", params={"item_type": "summary", "item_id": "s_integ_1", "text": "hotel booking confirmation and itinerary"})
    assert r1.status_code == 200 and r1.json().get("stored") is True

    r2 = client.post("/api/store_embedding", params={"item_type": "task", "item_id": "t_integ_1", "text": "book a hotel near central park"})
    assert r2.status_code == 200 and r2.json().get("stored") is True

    # Search similar by message text
    r3 = client.post("/api/search_similar", json={"message_text": "need help booking a hotel", "top_k": 3})
    assert r3.status_code == 200
    data = r3.json()
    assert "related" in data
    assert isinstance(data["related"], list)
    assert len(data["related"]) >= 1


def test_coach_feedback_persist(client):
    # Create a response to reference
    resp = client.post("/api/respond", json={"task_id": "t_integration_2", "user_id": "u_test"})
    assert resp.status_code == 200
    response_id = resp.json()["response_id"]

    # Submit feedback
    fb_payload = {
        "summary_id": "s_integ_1",
        "task_id": "t_integration_2",
        "response_id": response_id,
        "scores": {"clarity": 4, "relevance": 5, "tone": 4},
        "comment": "good"
    }
    fb = client.post("/api/coach_feedback", json=fb_payload)
    assert fb.status_code == 200
    fb_data = fb.json()
    assert fb_data.get("stored") is True
    assert fb_data.get("score") == 13

    # verify DB
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cnt = cur.execute("SELECT COUNT(*) FROM coach_feedback").fetchone()[0]
    conn.close()
    assert cnt >= 1


def test_metrics_endpoint(client):
    # Generate some more calls to ensure metrics populated
    client.get("/health")
    client.get("/api/metrics")

    r = client.get("/api/metrics")
    assert r.status_code == 200
    data = r.json()

    assert "avg_latency_ms" in data
    assert "error_rate" in data
    assert "endpoint_stats" in data
    assert "api_metrics" in data
    assert data["api_metrics"].get("total_calls", 0) >= 1

    # Basic structure checks
    assert isinstance(data["endpoint_stats"], list)
