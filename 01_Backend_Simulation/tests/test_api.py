import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    #  validate that it at least contains the expected keys, without being too strict with the exact text.
    data = response.json()
    assert data["status"] == "alive"
    assert "service" in data
    assert "engine" in data  # Now validate that the engine field exists
    

def test_set_intensity_invalid():
    # Test with a non-numeric value
    response = client.post("/set_intensity/2.0")
    assert response.status_code == 400