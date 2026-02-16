from sqlalchemy import Column, Integer, Float, String, DateTime
from api.database import Base
import datetime

class HeartLog(Base):
    __tablename__ = "heart_metrics"

    time = Column(DateTime(timezone=True), primary_key=True, default=datetime.datetime.utcnow)
    bpm = Column(Float, nullable=False)
    trimp = Column(Float)
    hrr = Column(Float)
    zone = Column(String)
    intensity = Column(Float)
    color = Column(String)

class EnvironmentalMetric(Base):
    __tablename__ = "environmental_metrics"
    time = Column(DateTime(timezone=True), primary_key=True, default=datetime.datetime.utcnow)
    temperature = Column(Float)
    pressure = Column(Float)
    humidity = Column(Float)

class SimulationState(Base):
    __tablename__ = "simulation_state"
    id = Column(Integer, primary_key=True)
    target_intensity = Column(Float, default=0.0)