from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.database import SessionLocal
from api.models import HeartLog, SimulationState

router = APIRouter()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    #  .time 
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
