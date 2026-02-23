import sys
import os
import csv
import math
import matplotlib.pyplot as plt

# Add the root path to import the logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_logic.physio_model import HeartModel

def run_continuous_validation():
    print("🏃‍♂️ Starting Validation Marathon: Kaggle vs Digital Twin...")
    
    # Path to the giant dataset
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../05_Data_Ingestion/datasets/heartrate_seconds_merged.csv'))
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: Dataset not found at {csv_path}")
        print("Make sure the path is correct.")
        return

    print("🔍 Extracting training event (April 12, 13:40 - 13:55)...")
    real_hr_data = []
    
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        next(reader) # Skip headers
        for row in reader:
            if row[0] == "2022484408" and ("4/12/2016 1:4" in row[1] or "4/12/2016 1:5" in row[1]):
                real_hr_data.append(float(row[2]))
                
    if not real_hr_data:
        print("⚠️ No data found for this time range.")
        return

    n_samples = len(real_hr_data)
    print(f"✅ Extracted {n_samples} seconds of real data from Kaggle!")

    # Initialize Digital Twin
    twin = HeartModel(age=30, sex='male', resting_hr=62)
    twin.current_hr = real_hr_data[0] 
    
    predicted_hr_data = []
    
    print("⚙️  Executing simulation (Proportional Controller / State Observer)...")
    for real_hr in real_hr_data:
        
        # 1. Calculate the "Error" (Difference between reality and the Twin)
        error = real_hr - twin.current_hr
        
        # 2. Auto-Tuning Logic
        if error > 2.0:
            # The human is going faster. Accelerate proportionally to the error.
            # Multiply by 0.05 to smooth, and limit to 1.0 (maximum effort)
            intensity = min(1.0, error * 0.05)
        else:
            # The human is going slower, same, or resting. Total brake!
            intensity = 0.0
        
        # One step of simulation
        metrics = twin.simulate_step(intensity=intensity, 
        dt=1.0, 
        temperature=6.19, 
        slope_percent=0.0)

        predicted_hr_data.append(metrics['bpm'])

    # 📊 ERROR CALCULATION
    print("\n📊 CALCULATING SCIENTIFIC ACCURACY...")
    mse = 0.0
    for real, pred in zip(real_hr_data, predicted_hr_data):
        mse += (real - pred) ** 2
    
    mse = mse / n_samples
    rmse = math.sqrt(mse) 

    print(f"   📈 Mean Squared Error (MSE): {round(mse, 2)}")
    print(f"   🎯 RMSE (Average deviation): ±{round(rmse, 2)} BPM")

    print("\n⏱️  SAMPLE (Real vs Twin) - Last 10 seconds of the dataset:")
    print("---------------------------------------------------")
    print("Second | Human (Kaggle) | Digital Twin | Difference")
    for i in range(n_samples - 10, n_samples):
        real = round(real_hr_data[i], 1)
        pred = round(predicted_hr_data[i], 1)
        diff = round(abs(real - pred), 1)
        print(f"  {i}   |      {real} BPM   |    {pred} BPM   |  {diff} BPM")
    print("---------------------------------------------------")
    
    if rmse < 10.0:
        print("\n✅ FINAL VERDICT: Excellent. Your twin mimics the real physiology with commercial accuracy.")
    else:
        print("\n⚠️ FINAL VERDICT: There is room for improvement. Adjust the 'tau' or the intensity in the heuristic.")


    # 👇 THIS IS THE MISSING MAGIC 👇
    # Generate a list of seconds [0, 1, 2, ..., 133] for the X axis
    time_data = list(range(n_samples))
    
    # Call the function with the real names of your variables
    generate_validation_plot(time_data, real_hr_data, predicted_hr_data, filename="validation_plot.png")


# 📊 GENERATION OF THE VALIDATION PLOT
def generate_validation_plot(time_data, human_data, twin_data, filename="validation_plot.png"):
    # Configure the style and size of the canvas
    plt.figure(figsize=(10, 6))
    
    # Draw the two curves
    plt.plot(time_data, 
    human_data, 
    label='Real Human (Kaggle)', 
    color='#3B82F6', linewidth=2.5)

    plt.plot(time_data, 
    twin_data, 
    label='Digital Twin', 
    color='#EF4444', 
    linewidth=2.5, 
    linestyle='--')
    
    # Aesthetics, titles and labels
    plt.title('Physiological Validation: Heart Rate Recovery (HRR)', fontsize=16, fontweight='bold')
    plt.xlabel('Time (Seconds)', fontsize=12)
    plt.ylabel('Heart Rate (BPM)', fontsize=12)
    
    # Add a grid to make it look more scientific
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc='upper right', fontsize=12)
    
    # Adjust margins
    plt.tight_layout()
    
    # Save the image in the current folder
    plt.savefig(filename, dpi=300) # dpi=300 ensures print quality 
    plt.close()
    
    print(f"\n📸 Scientific grade graph generated successfully: {filename}!")




if __name__ == "__main__":
    run_continuous_validation()