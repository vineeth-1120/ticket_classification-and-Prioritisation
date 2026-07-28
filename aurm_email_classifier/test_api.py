import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import json

from app.main import app
from app.database import Base, engine, get_db
from app.config import settings

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}

def test_classify():
    data = {
        "email_id": "msg_test_123",
        "sender": "test@example.com",
        "title": "Broken locker",
        "body": "Hi, my locker is tampered with and someone broke into it.",
        "received_at": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post("/classify/", json=data)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["email_id"] == "msg_test_123"
    # Fallback or OpenAI should classify this as Damage/Loss and P0 because of "tampered", "broke into"
    assert res_data["category"] == "Damage/Loss"
    assert res_data["priority"] == "P0"
    
def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    res_data = response.json()
    assert "total_classified" in res_data
    assert res_data["total_classified"] >= 1
