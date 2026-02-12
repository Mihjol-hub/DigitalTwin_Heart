import threading
import time
import math
import random
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.orm import Session

# Importaciones corregidas (relativas)
from .database import engine, Base, SessionLocal, init_db
from .models import HeartLog, SimulationState
from .routes import heart_routes

# Crear tablas al cargar el módulo
Base.metadata.create_all(bind=engine)

def run_simulation():
    """Generador de datos del corazón (El motor del DT)."""
    time.sleep(5) # Esperar a que la DB esté lista
    print("🚀 [Engine] Iniciando simulación cardíaca...", flush=True)
    
    db = SessionLocal()
    current_bpm = 60.0
    
    while True:
        try:
            state = db.query(SimulationState).first()
            target_intensity = state.target_intensity if state else 0.5
            
            # Lógica física simple
            target_bpm = 60 + (target_intensity * 120)
            current_bpm += (target_bpm - current_bpm) * 0.1
            final_bpm = current_bpm + random.uniform(-1.0, 1.0)

            # Insertar usando 'timestamp' (coincidiendo con models.py)
            new_log = HeartLog(
                timestamp=datetime.utcnow(), 
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
    # Todo el inicio centralizado aquí (Estilo Nivel 4)
    print("🚀 Iniciando el Cerebro del Gemelo Digital...")
    init_db()
    # Arrancamos el hilo de simulación
    sim_thread = threading.Thread(target=run_simulation, daemon=True)
    sim_thread.start()
    yield
    print("🛑 Apagando sistemas...")

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