import threading
import time
import math
import random
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.orm import Session

# Import DB and Models
from api.database import engine, Base, SessionLocal
from api.models import HeartLog, SimulationState
from api.routes import heart_routes

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (e.g., connect to DB, initialize models)
    print("🚀 Starting Digital Twin...")
    yield
    # Shutdown logic (e.g., close connections)
    print("🛑 Shutting down systems...")

app = FastAPI(lifespan=lifespan)



@app.get("/")
def read_root():
    return {
        "status": "alive",
        "message": "Digital Twin Heart API is running",
        "service": "heart-digital-twin",
        "engine": "running"  
    }


app.include_router(heart_routes.router)

# --- HEART SIMULATOR (THE ENGINE) ---
def run_simulation():
    """Generates heart data and saves it to the DB."""
    time.sleep(3) 
    print("🚀 [Engine] Starting heart simulation...", flush=True)
    
    db = SessionLocal()
    current_bpm = 60.0
    
    while True:
        try:
            state = db.query(SimulationState).first()
            target_intensity = state.target_intensity if state else 0.0
            
            # Basic physics
            target_bpm = 60 + (target_intensity * 120)
            gap = target_bpm - current_bpm
            current_bpm += gap * 0.1
            noise = random.uniform(-1.0, 1.0)
            final_bpm = current_bpm + noise

            # Derived metrics
            hrr = (final_bpm - 60) / 130
            trimp = final_bpm * (1.0 / 60.0)
            
            if final_bpm < 100: zone = 1
            elif final_bpm < 130: zone = 2
            elif final_bpm < 150: zone = 3
            elif final_bpm < 170: zone = 4
            else: zone = 5
            
            colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#881337"]
            color = colors[zone - 1]

            # Guardar
            new_log = HeartLog(
                time=datetime.utcnow(),
                bpm=final_bpm,
                intensity=target_intensity,
                hrr=hrr,
                trimp=trimp,
                zone=zone,
                color=color
            )
            
            db.add(new_log)
            db.commit()
            
            if int(final_bpm) % 10 == 0:
                print(f"💓 [Engine] BPM: {final_bpm:.1f} | Objetivo: {target_intensity:.1f}", flush=True)
                
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ [Engine Error] {e}", flush=True)
            db.rollback()
            time.sleep(1)

@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=run_simulation, daemon=True)
    t.start()
