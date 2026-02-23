from core_logic.physio_model import HeartModel
import pytest

def test_heart_rate_increases_with_intensity():
    # Add sex="male"
    heart = HeartModel(age=20, resting_hr=60, sex="male")
    initial_hr = heart.current_hr
    
    # Apply maximum intensity
    heart.simulate_step(intensity=1.0)
    
    assert heart.current_hr > initial_hr
    assert heart.current_hr <= 200 # 220 - age

def test_hr_zones_logic():
    """Verify if the zones change according to the % of MaxHR"""
    model = HeartModel(age=20, resting_hr=60, sex="female")
    
    # receive (Name, Color)
    zone_name, _ = model._get_training_zone(110) 
    
    assert zone_name == "Zone 1 (Very Light)"
    

def test_trimp_accumulation_is_monotonic():
    """TRIMP must be accumulative and never decrease"""
    model = HeartModel(age=30, resting_hr=60, sex="male")
    
    last_trimp = 0
    for _ in range(5):
        metrics = model.simulate_step(intensity=0.8)
        assert metrics["trimp"] >= last_trimp
        last_trimp = metrics["trimp"]

def test_recovery_score_calculation():
    """Verify the calculation of HRR at the exact minute"""
    model = HeartModel(age=20, resting_hr=60, sex="female")
    
    # Force state of fatigue
    model.current_hr = 160
    
    # Simulate 59 seconds of rest
    for _ in range(59):
        model.simulate_step(intensity=0.0, dt=1.0)
    
    assert model.hrr_1min == 0
    
    # The second 60 triggers the calculation
    model.simulate_step(intensity=0.0, dt=1.0)
    assert model.hrr_1min > 0
    print(f"✅ HRR detected: {model.hrr_1min} BPM recovered in 1 min")

def test_variability_injection():
    """Verify that HRV (Variability) works (not a metronome)"""
    model = HeartModel(age=25, resting_hr=60, sex="male")
    
    m1 = model.simulate_step(intensity=0.5)
    m2 = model.simulate_step(intensity=0.5)
    
    # The model injects Gauss-Markov noise, so they cannot be equal
    assert m1["bpm"] != m2["bpm"]

def test_alert_thresholds():
    """Verify alerts if BPM exceeds the threshold"""
    model = HeartModel(age=40, resting_hr=60, sex="female")
    
    # Set HR high and request metrics
    metrics = model.get_metrics(195)
    
    assert metrics["bpm"] > 180
    assert metrics["zone"] == "Zone 5 (Maximum)"

def test_long_running_stability_sim():
    """Simulate 1,000 beats to verify stability"""
    model = HeartModel(age=25, resting_hr=60, sex="male")
    try:
        for _ in range(1000):
            model.simulate_step(intensity=0.7)
        print("✅ Stability confirmed: 1,000 cycles without errors.")
    except Exception as e:
        pytest.fail(f"❌ The model failed in long run: {e}")