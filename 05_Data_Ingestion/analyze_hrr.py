import pandas as pd
import numpy as np

def analyze():
    file_path = "datasets/heartrate_seconds_merged.csv"
    print(f"🔍 Analysing {file_path}...")
    
    # Loading only a part of the file if it is giant, or all if you have RAM
    df = pd.read_csv(file_path)
    df['Time'] = pd.to_datetime(df['Time'])
    
    # Grouping by user ID
    users = df['Id'].unique()
    print(f"Users found: {len(users)}")

    for user in users[:3]:
        data = df[df['Id'] == user].sort_values('Time')
        
        # Calculate the BPM difference with a 60-second offset
        # (Fitabase usually has data every 5-10-15 seconds)
        data['hr_1min_later'] = data['Value'].shift(-6) # Assuming ~10s per record
        data['recovery_drop'] = data['Value'] - data['hr_1min_later']
        
        # Looking for drops of more than 25 BPM that started from an effort (>110 BPM)
        significant_recovery = data[(data['recovery_drop'] > 25) & (data['Value'] > 110)]
        
        if not significant_recovery.empty:
            event = significant_recovery.iloc[0]
            print(f"\n✅ Event found! User: {user}")
            print(f"   ⏱️ Time: {event['Time']}")
            print(f"   💓 Start BPM: {event['Value']}")
            print(f"   📉 Drop in 1 min: {event['recovery_drop']} BPM")
            return # Exit after finding the first good one
            
if __name__ == "__main__":
    analyze()