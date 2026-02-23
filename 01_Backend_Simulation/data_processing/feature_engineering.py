import vitaldb
import pandas as pd
import numpy as np
import os

def prepare_training_data(case_id=3):
    print(f"⚙️ Starting Feature Engineering - Patient #{case_id}")
    track_names = ['Solar8000/HR', 'Orchestra/PPF20_CE']
    
    try:
        # 1. Download raw data
        vf = vitaldb.VitalFile(case_id, track_names)
        df = vf.to_pandas(track_names, 1.0).dropna()
        
        print(f"📥 Raw data downloaded: {len(df)} rows.")
        
        # 2. FEATURE ENGINEERING: Creating the RMSSD
        print("🧮 Calculating RMSSD (30-second moving window)...")
        
        # A. Convert BPM to RR intervals in milliseconds (60,000 ms in a minute)
        df['RR_ms'] = 60000.0 / df['Solar8000/HR']
        
        # B. Calculate the difference between a beat and the previous one
        df['RR_diff'] = df['RR_ms'].diff()
        
        # C. Square that difference
        df['RR_sq_diff'] = df['RR_diff'] ** 2
        
        # D. Calculate the mean of those squares in a 30-second window, and take the square root
        df['RMSSD'] = np.sqrt(df['RR_sq_diff'].rolling(window=30).mean())
        
        # 3. Final Cleanup
        # Remove the first 30 seconds because they don't have complete RMSSD (the window is filling up)
        df = df.dropna()
        
        # Rename columns for easy understanding by the AI
        df = df.rename(columns={
            'Solar8000/HR': 'BPM',
            'Orchestra/PPF20_CE': 'Propofol_Level'
        })
        
        # Keep only the columns that matter to the model
        final_df = df[['BPM', 'RMSSD', 'Propofol_Level']]
        
        # 4. Save the Training Dataset
        output_path = os.path.join(os.path.dirname(__file__), 'training_data.csv')
        final_df.to_csv(output_path, index=False)
        
        print(f"\n✅ Training dataset created successfully!")
        print(f"💾 Saved to: {output_path}")
        print("\n📊 Sample of the data that the AI will consume:")
        print(final_df.head())
        print("\n📊 And here's how the RMSSD drops in the middle of the surgery:")
        print(final_df.iloc[1000:1005])
        
    except Exception as e:
        print(f"❌ Error processing the data: {e}")

if __name__ == "__main__":
    prepare_training_data(3)