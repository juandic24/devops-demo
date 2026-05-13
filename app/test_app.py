import json
import os
from app import app


def test_home_status():
    client = app.test_client()
    res = client.get("/")
    assert res.status_code == 200


def test_home_json_structure():
    client = app.test_client()
    res = client.get("/")
    data = json.loads(res.data)
    assert "message" in data
    assert "version" in data
    assert data["message"] == "DevOps Demo App"


def test_health_status():
    client = app.test_client()
    res = client.get("/health")
    assert res.status_code == 200


def test_health_json_structure():
    client = app.test_client()
    res = client.get("/health")
    data = json.loads(res.data)
    assert data["status"] == "healthy"
    assert "env" in data


def test_health_env_default():
    client = app.test_client()
    res = client.get("/health")
    data = json.loads(res.data)
    assert data["env"] == "local"


def test_health_env_override(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    client = app.test_client()
    res = client.get("/health")
    data = json.loads(res.data)
    assert data["env"] == "production"
