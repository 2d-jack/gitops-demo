import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_home_returns_json_structure(client):
    response = client.get("/")
    data = response.get_json()
    assert "status" in data
    assert "message" in data
    assert "version" in data
    assert "environment" in data
    assert "hostname" in data


def test_home_status_ok(client):
    response = client.get("/")
    data = response.get_json()
    assert data["status"] == "ok"


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_healthy(client):
    response = client.get("/health")
    data = response.get_json()
    assert data["status"] == "healthy"


def test_version_returns_200(client):
    response = client.get("/version")
    assert response.status_code == 200


def test_version_has_version_field(client):
    response = client.get("/version")
    data = response.get_json()
    assert "version" in data


def test_404_not_found(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
