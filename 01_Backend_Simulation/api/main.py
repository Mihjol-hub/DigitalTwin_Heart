import threading
import time
import math
import random
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, init_db
from .models import HeartLog, SimulationState
from .routes import heart_routes

# Create tables on module load
Base.metadata.create_all(bind=engine)

def run_simulation():
    """Heart data generator (The DT engine)."""
    time.sleep(5) # Wait for the DB to be ready
    print("🚀 [Engine] Starting simulation...", flush=True)
    
    db = SessionLocal()
    current_bpm = 60.0
    
    while True:
        try:
            state = db.query(SimulationState).first()
            target_intensity = state.target_intensity if state else 0.5
            
            # Simple physics logic
            target_bpm = 60 + (target_intensity * 120)
            current_bpm += (target_bpm - current_bpm) * 0.1
            final_bpm = current_bpm + random.uniform(-1.0, 1.0)

            # Insert using 'timestamp' (matching models.py)
            new_log = HeartLog(
                time=datetime.utcnow(), 
                bpm=final_bpm,
                intensity=target_intensity,
                hrr=(final_bpm - 60) / 130,
                trimp=final_bpm / 60.0,
                zone="Zona " + str(min(5, int(final_bpm/40) + 1)),
                color="#EF4444"
            )
            
            db.add(new_log)
            db.commit()
            
            if int(final_bpm) % 5 == 0:
                print(f"💓 [DT Level 3] BPM: {final_bpm:.1f}", flush=True)
                
            time.sleep(1)
        except Exception as e:
            print(f"❌ [Engine Error] {e}", flush=True)
            db.rollback()
            time.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Centralized startup here (Level 4 style)
    print("🚀 Starting the Digital Twin Brain...")
    init_db()
    # Start the simulation thread
    sim_thread = threading.Thread(target=run_simulation, daemon=True)
    sim_thread.start()
    yield
    print("🛑 Shutting down systems...")

app = FastAPI(title="Heart Digital Twin", lifespan=lifespan)

@app.get("/")
def read_root():
    return {
        "status": "alive", 
        "level": 3.5,
        "service": "heart-digital-twin",
        "engine": "running"
    }

app.include_router(heart_routes.router)