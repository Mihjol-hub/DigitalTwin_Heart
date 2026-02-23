from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from api.database import SessionLocal
from api.models import HeartLog, SimulationState
import asyncio

router = APIRouter()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# HTTP ROUTES
@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    last_log = db.query(HeartLog).order_by(HeartLog.time.desc()).first()
    if not last_log:
        raise HTTPException(status_code=404, detail="No heart data found")
    return last_log

@router.post("/set_intensity/{intensity}")
def set_intensity(intensity: float, db: Session = Depends(get_db)):
    if not (0 <= intensity <= 1.0):
        raise HTTPException(status_code=400, detail="0.0 to 1.0 only")
    
    state = db.query(SimulationState).first()
    if not state:
        state = SimulationState(id=1, target_intensity=intensity)
        db.add(state)
    else:
        state.target_intensity = intensity
    
    db.commit()
    return {"message": f"Intensity set to {intensity}"}

#  WEBSOCKET FOR UNITY
@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Unity connected to the Digital Twin!")
    try:
        while True:
            # Open a quick session to read the last beat
            db = SessionLocal()
            try:
                last_log = db.query(HeartLog).order_by(HeartLog.time.desc()).first()
                if last_log:
                    # sent the JSON directly through the tunnel
                    await websocket.send_json({
                        "bpm": last_log.bpm,
                        "zone": last_log.zone,
                        "color": last_log.color,
                        # If you have hrr or trimp in the DB, add them here. 
                        # If not, Unity will receive null but won't crash.
                    })
            finally:
                db.close()
            
            # Send data 10 times per second (0.1s) so the hologram is smooth
            await asyncio.sleep(0.1) 
            
    except WebSocketDisconnect:
        print("❌ Unity is disconnected.")