from core_logic.physio_model import HeartModel
import pytest


def test_heart_rate_increases_with_intensity():
    heart = HeartModel(age=20, resting_hr=60)
    initial_hr = heart.current_hr
    
    # applied maximum intensity
    heart.simulate_step(1.0)
    
    # The heartbeat should be higher than the initial one but not exceed the maximum.
    assert heart.current_hr > initial_hr
    assert heart.current_hr <= 200 # 220-20



def test_hr_zones_logic():
    """Verify that the zones change according to the percentage of MaxHR (220-age)"""
    # Age 20 -> MaxHR 200. 
    # 60% = 120 (Fat Burn), 90% = 180 (VO2 Max)
    model = HeartModel(age=20, resting_hr=60)
    
    model.current_hr = 110 # 55%
    assert model._get_zone() == "Rest"
    
    model.current_hr = 185 # 92.5%
    assert model._get_zone() == "VO2 Max"

def test_trimp_accumulation_is_monotonic():
    """TRIMP should be cumulative and never decrease"""
    model = HeartModel(age=30, resting_hr=60)
    
    # Simulate 5 seconds of exercise
    last_trimp = 0
    for _ in range(5):
        metrics = model.simulate_step(intensity=0.8)
        assert metrics["trimp"] >= last_trimp
        last_trimp = metrics["trimp"]

def test_recovery_score_calculation():
    """Verify that the recovery score is calculated exactly at one minute of rest"""
    model = HeartModel(age=20, resting_hr=60)
    
    # Force a high fatigue state
    model.current_hr = 160
    
    # Simulate 59 seconds of rest (intensity 0)
    for _ in range(59):
        model.simulate_step(intensity=0.0, dt=1.0)
    
    assert model.hrr_score == 0 # Should not be calculated yet
    
    # The 60th second (triggers the calculation)
    model.simulate_step(intensity=0.0, dt=1.0)
    assert model.hrr_score > 0
    print(f"✅ HRR detected: {model.hrr_score} BPM recovered in 1 min")