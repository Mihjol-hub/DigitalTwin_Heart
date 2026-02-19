import pandas as pd
import matplotlib.pyplot as plt

def find_recovery_windows(file_path, user_id=None):
    print(f"📂 Loading data from: {file_path}")
    df = pd.read_csv(file_path)
    df['Time'] = pd.to_datetime(df['Time'])
    
    # If there is not an ID, take the first one with more data
    if not user_id:
        user_id = df['Id'].iloc[0]
    
    user_data = df[df['Id'] == user_id].sort_values('Time')
    
    # Search for sharp drops: The pulse drops more than 20 beats in 60 seconds
    user_data['diff_hr'] = user_data['Value'].diff(periods=-60) # Compare with 1 min later
    recoveries = user_data[user_data['diff_hr'] > 20]
    
    if recoveries.empty:
        print("❌ No clear recovery windows were found for this user.")
        return
    
    print(f"✅ Found {len(recoveries)} recovery events for user {user_id}")
    
    # Take the most drastic event to analyze
    best_event_time = recoveries.sort_values('diff_hr', ascending=False).iloc[0]['Time']
    window = user_data[(user_data['Time'] >= best_event_time - pd.Timedelta(seconds=10)) & 
                       (user_data['Time'] <= best_event_time + pd.Timedelta(seconds=120))]
    
    return window

if __name__ == "__main__":
    path = "datasets/heartrate_seconds_merged.csv"
    recovery_curve = find_recovery_windows(path)
    if recovery_curve is not None:
        print("📊 Recovery curve extracted successfully.")
        print(recovery_curve[['Time', 'Value']].head(10))