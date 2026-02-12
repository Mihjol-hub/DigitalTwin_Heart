import datetime # Importamos el módulo completo
from sqlalchemy import Column, Float, DateTime, Integer, String
from .database import Base

class HeartLog(Base):
    __tablename__ = "heart_metrics"
    id = Column(Integer, primary_key=True, index=True)
    bpm = Column(Float)
    trimp = Column(Float)
    hrr = Column(Float)
    zone = Column(String)
    intensity = Column(Float)
    color = Column(String)
    time = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class SimulationState(Base):
    __tablename__ = "simulation_state"
    id = Column(Integer, primary_key=True, index=True)
    target_intensity = Column(Float, default=0.5)

class EnvironmentalMetric(Base):
    __tablename__ = "environmental_metrics"
    # Aquí estaba el error. Al usar 'import datetime', esto es lo correcto:
    time = Column(DateTime(timezone=True), primary_key=True, default=datetime.datetime.utcnow)
    temperature = Column(Float, nullable=False)