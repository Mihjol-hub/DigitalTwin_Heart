from sqlalchemy import Column, Float, String, DateTime, Integer
from .database import Base
from datetime import datetime

class SimulationState(Base):
    __tablename__ = "simulation_state"
    id = Column(Integer, primary_key=True)
    target_intensity = Column(Float, nullable=False, default=0.0)

class HeartLog(Base):
    __tablename__ = "heart_metrics"
    
    # IMPORTANT: define the PK on time
    timestamp = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow)
    
    bpm = Column(Float, nullable=False)
    trimp = Column(Float, nullable=False)
    hrr = Column(Float, nullable=False)
    zone = Column(String(20), nullable=False)
    intensity = Column(Float, nullable=True)
    color = Column(String(20), nullable=True)
