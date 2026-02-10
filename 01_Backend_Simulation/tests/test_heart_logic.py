import pytest
from core_logic.physio_model import HeartModel

def test_heart_recovery_after_sprint():
    model = HeartModel(age=25, resting_hr=60)
    # Simulate a sprint (intensity 1.0)
    for _ in range(60): 
        model.simulate_step(1.0)
    
    hr_at_peak = model.current_hr
    assert hr_at_peak > 150  # The heart rate should have increased

    # Simulate rest (intensity 0.0)
    for _ in range(60):
        model.simulate_step(0.0)
        
    # The HRR value should have been calculated
    assert model.hrr_score > 0
    assert model.current_hr < hr_at_peak