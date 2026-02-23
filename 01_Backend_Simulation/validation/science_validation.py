import sys
import os
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_logic.physio_model import HeartModel


# 🧪 TEST 1: Validation Scientific Basic of Recovery (HRR)

def validate_basic_recovery_curve():
    print("\n" + "="*50)
    print("🧪 TEST 1: Validation Scientific Basic of Recovery (HRR)")
    print("="*50)
    
    real_start_hr = 115.0  
    real_end_hr = 87.0     
    
    print("🤖 Creating Digital Twin in isolated environment...")
    twin = HeartModel(age=30, sex='male', resting_hr=62)
    twin.current_hr = real_start_hr
    
    print(f"⏱️ Simulating 60 seconds of rest... (Start: {real_start_hr} BPM)")
    predicted_curve = []
    
    for second in range(1, 61):
        metrics = twin.simulate_step(intensity=0.0, dt=1.0, temperature=6.19, slope_percent=0.0)
        predicted_curve.append(metrics['bpm'])
    
    predicted_end_hr = predicted_curve[-1]
    
    print("\n📊 RESULTADOS (TEST 1):")
    print(f"   Human Kaggle (End): {real_end_hr} BPM")
    print(f"   Digital Twin (End): {predicted_end_hr} BPM")
    
    error = abs(real_end_hr - predicted_end_hr)
    print(f"   ⚠️ Absolute Error: {round(error, 2)} beats difference")
    
    if error < 5.0:
        print("✅ VEREDICTO 1: The Digital Twin is almost identical to the human.\n")
    elif error < 15.0:
        print("⚠️ VEREDICTO 1: Acceptable, but check 'tau'.\n")
    else:
        print("❌ VEREDICTO 1: High difference.\n")


# 🧬 TEST 2: Advanced HRRPT Validation (Data Science
def calculate_hrrpt(recovery_hr_data):
    """HRRPT algorithm based on Bartels et al., 2018."""
    window_length = min(15, len(recovery_hr_data))
    if window_length % 2 == 0: window_length -= 1  
    filtered_hr = savgol_filter(recovery_hr_data, window_length, 3)

    x = np.arange(len(filtered_hr))
    p1 = np.array([x[0], filtered_hr[0]])
    p2 = np.array([x[-1], filtered_hr[-1]])

    y1, y2 = p1[1], p2[1]
    x1, x2 = p1[0], p2[0]
    
    distances = np.abs((y2 - y1) * x - (x2 - x1) * filtered_hr + x2 * y1 - y2 * x1) / np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
    
    hrrpt_idx = np.argmax(distances)
    return hrrpt_idx, filtered_hr

def validate_hrrpt():
    print("="*50)
    print("🧬 TEST 2: Clinical Phase Transition Simulation (HRRPT)")
    print("="*50)
    
    twin = HeartModel(age=30, sex='male', resting_hr=60, max_hr=190)
    
    print("🏃♂️ Phase A: Subjecting the twin to effort (60s sprint)...")
    for _ in range(60):
        twin.simulate_step(intensity=0.9, dt=1.0)
    
    print("🛑 Phase B: Inactive recovery (180s)...")
    recovery_data = []
    for _ in range(180):
        metrics = twin.simulate_step(intensity=0.0, dt=1.0)
        recovery_data.append(metrics['bpm'])
        
    print("🧮 Phase C: Processing data with Savitzky-Golay filter...")
    hrrpt_segundo, filtered_hr = calculate_hrrpt(recovery_data)
    
    print("\n📊 SCIENTIFIC RESULTS (TEST 2):")
    print(f"✅ The point of transition from fast-to-slow (HRRPT) occurred at second: {hrrpt_segundo}")
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(recovery_data, color='#9CA3AF', label='Raw Signal (With HRV)', alpha=0.5)
    plt.plot(filtered_hr, color='#EF4444', linewidth=3, label='Filtered Signal (Savitzky-Golay)')
    plt.plot([0, len(filtered_hr)-1], [filtered_hr[0], filtered_hr[-1]], linestyle='--', color='#3B82F6', label='Base Line')
    plt.axvline(x=hrrpt_segundo, color='black', linestyle=':', linewidth=2)
    plt.plot(hrrpt_segundo, filtered_hr[hrrpt_segundo], 'ko', markersize=10, label=f'HRRPT ({hrrpt_segundo}s)')
    
    plt.title('Identification of Cardiac Recovery Transition (HRRPT)', fontsize=14, fontweight='bold')
    plt.xlabel('Time of Recovery (Seconds)')
    plt.ylabel('Heart Rate (BPM)')
    plt.legend(loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('hrrpt_plot.png', dpi=300)
    print("📸 Plot 'hrrpt_plot.png' saved successfully in the current directory.\n")

if __name__ == "__main__":
    validate_basic_recovery_curve()
    validate_hrrpt()