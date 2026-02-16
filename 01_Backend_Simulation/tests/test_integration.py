import pytest
import requests
import time
import os
import threading
from datetime import datetime, timedelta
from sqlalchemy import text
from api.models import HeartLog 
from api.database import SessionLocal 

API_URL = os.getenv("API_URL", "http://backend_sim:8000")

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_01_health_check():
    response = requests.get(f"{API_URL}/")
    assert response.status_code == 200

def test_02_read_metrics():
    endpoint = f"{API_URL}/metrics"
    for i in range(10):
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                return
        except: pass
        time.sleep(1)
    pytest.fail("Timeout")

def test_03_physio_control_loop():
    """Test con limpieza de datos previos para evitar interferencias."""
    print("\n🔬 Starting stress test...")
    
    # LIMPIEZA: Borramos registros futuros que puedan estar 'envenenando' la métrica
    session = SessionLocal()
    try:
        session.execute(text("DELETE FROM heart_metrics WHERE time > NOW()"))
        session.commit()
    finally:
        session.close()

    # 1. Rest
    requests.post(f"{API_URL}/set_intensity/0.1")
    time.sleep(3) # Damos tiempo a que se genere un latido nuevo real
    bpm_rest = requests.get(f"{API_URL}/metrics").json().get("bpm", 0)
    print(f"   💓 Basal BPM: {bpm_rest}")

    # 2. Exercise
    requests.post(f"{API_URL}/set_intensity/1.0")
    print("🏃 Intensity -> 1.0 (Sprint).")
    
    success = False
    for _ in range(10):
        time.sleep(1.5)
        bpm_exercise = requests.get(f"{API_URL}/metrics").json().get("bpm", 0)
        print(f"   💓 Current BPM: {bpm_exercise}")
        if bpm_exercise > bpm_rest:
            success = True
            break
            
    assert success, f"Heart stuck at {bpm_exercise}. Basal was {bpm_rest}"
    print(f"✅ Incremento detectado!")

def test_timescale_hypertable_check(db_session):
    result = db_session.execute(text(
        "SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'heart_metrics'"
    )).fetchone()
    assert result is not None

def test_unity_contract_format():
    data = requests.get(f"{API_URL}/metrics").json()
    for key in ["bpm", "trimp", "hrr", "zone", "color"]:
        assert key in data

def test_api_latency_performance():
    start_time = time.time()
    requests.get(f"{API_URL}/metrics")
    assert (time.time() - start_time) * 1000 < 100

def test_concurrent_intensity_updates():
    def send_request(val): requests.post(f"{API_URL}/set_intensity/{val}")
    threads = [threading.Thread(target=send_request, args=(0.5,)) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert requests.get(f"{API_URL}/metrics").status_code == 200

def test_timescale_ordering_robustness():
    session = SessionLocal()
    try:
        future_time = datetime.utcnow() + timedelta(minutes=10)
        log_future = HeartLog(bpm=205.0, time=future_time, trimp=10.0, hrr=0.0, zone="Future", color="#FFFFFF")
        session.add(log_future)
        session.commit()
        data = requests.get(f"{API_URL}/metrics").json()
        assert data["bpm"] == 205.0
    finally:
        session.close()
