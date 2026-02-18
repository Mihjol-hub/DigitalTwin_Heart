import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Try to get the individual pieces (more secure in Docker)
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = os.getenv("POSTGRES_DB", "heart_twin")
DB_HOST = os.getenv("DB_HOST", "heart_db")

# 2. Build the URL manually to avoid symbol errors ${}
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

print(f"📡 Intentando conectar a: postgresql://{DB_USER}:***@{DB_HOST}/{DB_NAME}")

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print(f"❌ Error crítico al crear el engine: {e}")
    raise e

def init_db():
    Base.metadata.create_all(bind=engine)