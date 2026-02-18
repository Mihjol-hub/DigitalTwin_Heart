from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import engine, Base, init_db
from .routes import heart_routes

# Create tables on module load
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting the Digital Twin Brain (API Mode)...")
    init_db()
    yield
    print("🛑 Shutting down API...")

app = FastAPI(title="Heart Digital Twin", lifespan=lifespan)

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "level": 3,
        "mode": "production_data_monitoring"
    }

app.include_router(heart_routes.router)