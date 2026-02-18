import pytest
from core_logic.physio_model import HeartModel

def test_heart_recovery_after_sprint():
    model = HeartModel(age=25, resting_hr=60, sex="male")
    # Simulate a sprint (intensity 1.0)
    for _ in range(60): 
        model.simulate_step(1.0)
    
    hr_at_peak = model.current_hr
    assert hr_at_peak > 150  # The heart rate should have increased

    # Simulate rest (intensity 0.0)
    for _ in range(60):
        model.simulate_step(intensity=0.0, dt=1.0, temperature=20.0, slope_percent=0.0)
        
    # The HRR value should have been calculated
    assert model.hrr_1min > 0
    print(f"✅  logic validated: {model.hrr_1min} BPM recovered.")