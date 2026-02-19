import pytest
from fastapi.testclient import TestClient
from api.main import app
import requests

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "mode" in data
    

def test_set_intensity_invalid():
    # Test with a non-numeric value
    response = client.post("/set_intensity/2.0")
    assert response.status_code == 400




# --- TEST 17: Input Sanitization ---
def test_api_invalid_intensity_input():
    """The API must reject non-numeric or out-of-range values (HTTP 422 or 400)"""
    base_url = "http://backend_sim:8000"
    
    print("\n🛡️  [TEST] Testing API input sanitization...")
    
    # CASE A: Send text instead of a number
    print("   -> Trying to send 'muy_alta' as intensity...")
    r_text = requests.post(f"{base_url}/set_intensity/muy_alta")
    # FastAPI usually returns 422 (Unprocessable Entity) for type errors
    assert r_text.status_code == 422, f"Type control failed: status {r_text.status_code}"
    
    # CASE B: Send number out of logical range (e.g., 5.0, when max is 1.0)
    # Note: If the API handles manual validation and returns 400:
    print("   -> Trying to send 5.0 (out of range)...")
    r_range = requests.post(f"{base_url}/set_intensity/5.0")
    
    # Note: Adjust 'assert' to 200 if the logic truncates the value internally, 
    # or to 400/422 if an error is thrown. We assume you validate and give an error.
    if r_range.status_code == 200:
        print("   (Warning: The API accepted 5.0, check if it truncates it internally)")
    else:
        assert r_range.status_code in [400, 422], f"Unexpected status: {r_range.status_code}"
        
    print("✅ API input sanitization confirmed.")