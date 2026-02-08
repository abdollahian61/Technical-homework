import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)

class TestAPI:
    """Test suite for FastAPI application"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_write_to_redis(self, client):
        """Test writing to Redis"""
        response = client.post("/write/test_key?value=test_value")
        assert response.status_code == 200
        assert "test_key" in response.json()["message"]
    
    def test_read_from_redis(self, client):
        """Test reading from Redis"""
        # First write a value
        client.post("/write/example_key?value=test_value")
        
        # Then read it
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/invalid")
        assert response.status_code == 404
    
    def test_write_with_special_characters(self, client):
        """Test writing values with special characters"""
        response = client.post("/write/special_key?value=hello%20world")
        assert response.status_code == 200
    
    def test_concurrent_requests(self, client):
        """Test multiple concurrent requests"""
        responses = []
        for i in range(10):
            response = client.post(f"/write/key_{i}?value=value_{i}")
            responses.append(response)
        
        assert all(r.status_code == 200 for r in responses)
