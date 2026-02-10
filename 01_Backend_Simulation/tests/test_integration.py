import pytest
import requests
import time
import os
from sqlalchemy import text

# localhost Docker in WSL2 
API_URL = os.getenv("API_URL", "http://localhost:8000")

def test_01_health_check():
    """Verify that the API Gateway (Brain) is turned on."""
    print("\n🔍 Verifying system vital signs...")
    try:
        response = requests.get(f"{API_URL}/")
        assert response.status_code == 200, "The API should return 200 OK"
        print("✅ API Alive Check: Passed (The brain responds)")
    except requests.exceptions.ConnectionError:
        pytest.fail("❌ CRITICAL: Cannot connect to the API. Did you run 'docker compose up'?")

def test_02_read_metrics():
    """Verify that the engine is generating data."""
    endpoint = f"{API_URL}/metrics"
    print(f"📡 Attempting to read telemetry at: {endpoint}")
    
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                if "bpm" in data:
                    print(f"✅ Successful read: {data['bpm']} BPM")
                    assert data["bpm"] > 0
                    return
        except:
            pass
        print(f"⏳ Waiting for first heartbeat... ({i+1}/{max_retries})")
        time.sleep(2)
    pytest.fail("❌ The engine did not generate data in time.")

def test_03_physio_control_loop():
    """Test the Feedback loop: Rest vs Exercise."""
    print("\n🔬 Starting stress test...")
    
    # 1. Rest
    requests.post(f"{API_URL}/set_intensity/0.0")
    time.sleep(4) 
    resp_rest = requests.get(f"{API_URL}/metrics").json()
    bpm_rest = resp_rest.get("bpm", 0)
    print(f"   💓 Basal BPM: {bpm_rest}")

    # 2. Exercise
    requests.post(f"{API_URL}/set_intensity/1.0") 
    print("🏃 Intensity -> 1.0 (Sprint).")
    time.sleep(8)
    
    resp_exercise = requests.get(f"{API_URL}/metrics").json()
    bpm_exercise = resp_exercise.get("bpm", 0)
    print(f"   💓 Peak BPM: {bpm_exercise}")

    assert bpm_exercise > bpm_rest, "The heart did not accelerate."
    print(f"✅ TEST PASSED: Difference of +{bpm_exercise - bpm_rest:.1f} BPM.")


def test_timescale_hypertable_check(db_session):
    # Consult the TimescaleDB metadata
    result = db_session.execute(text(
        "SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'heart_metrics'"
    )).fetchone()
    
    assert result is not None, "Error! The heart_metrics table is not a TimescaleDB hypertable."
    print("✅ Confirmed: The time-series engine is active.")