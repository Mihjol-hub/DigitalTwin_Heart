import sys
import os
# importr form core_logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_logic.physio_model import HeartModel

def validate_basal_trimp():
    # Using the model with the parameters
    # Female athlete (y_factor 1.67), resting 55
    model = HeartModel(age=30, sex="female", resting_hr=55)
    
    print("🔬 Validating TRIMP accumulation in absolute rest...")
    
    # Simulate 10 minutes (600 steps of 1s) with intensity 0.0
    for _ in range(600):
        model.simulate_step(intensity=0.0, dt=1.0)
    
    metrics = model.get_metrics(model.current_hr)
    trimp_final = metrics['trimp']
    
    print(f"📊 TRIMP after 10 min of rest: {trimp_final}")
    
    if trimp_final == 0:
        print("✅ SUCCESS: Basal metabolism does not generate phantom fatigue.")
    else:
        print(f"⚠️ WARNING: {trimp_final} TRIMP was accumulated. Check intensity offset.")

if __name__ == "__main__":
    validate_basal_trimp()