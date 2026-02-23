import vitaldb
import pandas as pd
import matplotlib.pyplot as plt
import os

def find_and_explore_case():
    print("🔍 Starting Smart VitalDB Radar...")
    # Add the "20" to specify the syringe concentration
    track_names = ['Solar8000/HR', 'Orchestra/PPF20_CE']
    
    try:
        print("🌐 Consulting the VitalDB master index in South Korea...")
        case_ids = vitaldb.find_cases(track_names)
        
        if not case_ids:
            print("❌ No cases found with these signals in the entire database.")
            return
            
        print(f"✅ Found {len(case_ids)} patients with Propofol at 2%! Extracting the first one: Patient #{case_ids[0]}")
        
        # Take the first patient from the list of safe results
        case_id = case_ids[0]
        
        print(f"🏥 Downloading vital signs for patient #{case_id}...")
        vf = vitaldb.VitalFile(case_id, track_names)
        df = vf.to_pandas(track_names, 1.0)
        
        # Clean empty data (moments where the monitor was off)
        df = df.dropna()
        
        if not df.empty and len(df) > 100:
            print(f"\n✅ Patient #{case_id} downloaded with {len(df)} seconds of data ready.")
            print("📊 Sample of the surgery (First 5 seconds):")
            print(df.head())
            
            # Graphing
            fig, ax1 = plt.subplots(figsize=(12, 6))

            # Left Y axis: Heart (Red)
            ax1.set_xlabel('Time of Surgery (Seconds)')
            ax1.set_ylabel('Heart Rate (BPM)', color='#EF4444')
            ax1.plot(df.index, df['Solar8000/HR'], color='#EF4444', alpha=0.7, label='BPM (Heart)')
            ax1.tick_params(axis='y', labelcolor='#EF4444')

            # Right Y axis: Brain / Anesthesia (Blue)
            ax2 = ax1.twinx()  
            ax2.set_ylabel('Concentration of Propofol at 2% (Brain)', color='#3B82F6')  
            ax2.plot(df.index, df['Orchestra/PPF20_CE'], color='#3B82F6', linewidth=2, label='Propofol (Anesthesia)')
            ax2.tick_params(axis='y', labelcolor='#3B82F6')

            plt.title(f'VitalDB Exploration - Effect of Anesthesia on BPM (Case #{case_id})', fontsize=14, fontweight='bold')
            fig.tight_layout()  
            
            plot_path = os.path.join(os.path.dirname(__file__), f'vitaldb_case_{case_id}.png')
            plt.savefig(plot_path, dpi=300)
            print(f"\n📸 Graph saved successfully: {plot_path}")
            
    except Exception as e:
        print(f"❌ Error fetching data from VitalDB: {e}")

if __name__ == "__main__":
    find_and_explore_case()