import time
import sys
import os

sys.path.append(os.getcwd())

from api.database import SessionLocal, init_db
from api.models import HeartLog, SimulationState
from core_logic.physio_model import HeartModel

# initialize the model outside the loop to maintain its state (TRIMP, HRR)
patient = HeartModel(age=25, resting_hr=60)

def run_engine():
    print(">>> MEDICAL BRAIN: The heart is beating...", flush=True)
    
    init_db()
    db = SessionLocal()
    
    # Ensure initial state
    try:
        if not db.query(SimulationState).first():
            db.add(SimulationState(target_intensity=0.0))
            db.commit()
    except Exception as e:
        print(f"⚠️ Error initializing state: {e}")

    while True:
        try:
            # 1. Synchronization with the DB
            db.expire_all() 
            state = db.query(SimulationState).first()
            intensity = state.target_intensity if state else 0.0
            
            # 2. Simulation (Physiology)
            metrics = patient.simulate_step(intensity)
            
            # 3. Persistence
            log = HeartLog(
                bpm=metrics["bpm"],
                trimp=metrics["trimp"],
                hrr=metrics["hrr"],
                zone=metrics["zone"],
                color=metrics["color"]
            )
            db.add(log)
            db.commit()
            
            # Success log
            print(f"💓 BPM: {metrics['bpm']} | I: {intensity} | Zone: {metrics['zone']}", flush=True)
            
        except Exception as e:
            print(f"❌ Error in the cycle: {e}. Retrying in 5s...", flush=True)
            db.rollback() # Clear failed transactions
            db.close()    # Close old connection
            time.sleep(5)
            db = SessionLocal() # We created a new and fresh connection
            continue # skip to the next beat to avoid executing the code below.

        # The 1-second sleep goes outside the error catch
        # to maintain a consistent heart rate
        time.sleep(1)

if __name__ == "__main__":
    run_engine()
