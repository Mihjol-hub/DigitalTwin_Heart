import sys
import os
import math

# Add the root path to import the physio_model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_logic.physio_model import HeartModel

def validate_recovery_curve():
    print("Starting Scientific Validation of Recovery (HRR)...")
    
    # 1. Real data from Kaggle user (ID: 2022484408)
    real_start_hr = 115.0  # The pulse from which stopped
    real_end_hr = 87.0     # Drop of 28 BPM after 60 seconds
    
    # 2. Initialize the Digital Twin
    print("🤖 Creating Digital Twin in isolated environment...")
    twin = HeartModel(age=30, sex='male', resting_hr=62)
    
    # Data Science Trick: Inject the initial state directly into the variables
    twin.current_hr = real_start_hr
    
    # 3. Simulate 60 seconds of rest
    print(f"⏱️ Simulating 60 seconds of rest... (Start: {real_start_hr} BPM)")
    predicted_curve = []
    
    for second in range(1, 61):
        # Intensity 0, temperature of Geneva, no slope
        metrics = twin.simulate_step(intensity=0.0, dt=1.0, temperature=6.19, slope_percent=0.0)
        predicted_curve.append(metrics['bpm'])
    
    # 4. Results and Error Calculation
    predicted_end_hr = predicted_curve[-1]
    
    print("\n📊 RESULTS:")
    print(f"   Human Kaggle (End): {real_end_hr} BPM")
    print(f"   Digital Twin (End): {predicted_end_hr} BPM")
    
    # Error Absolute Calculation
    error = abs(real_end_hr - predicted_end_hr)
    print(f"   ⚠️ Error Absolute: {round(error, 2)} beats difference")
    
    if error < 5.0:
        print("\n✅ VEREDICTO: The Digital Twin is identical to the human.")
    elif error < 15.0:
        print("\n⚠️ VEREDICTO: Acceptable, but we could adjust the 'tau' value more.")
    else:
        print("\n❌ VEREDICTO: High difference. We need to review the exponential equation.")

if __name__ == "__main__":
    validate_recovery_curve()