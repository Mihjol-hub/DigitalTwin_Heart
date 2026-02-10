import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# look for the full URL first
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 2. If it doesn't exist (local environment without docker) build it in parts
if not SQLALCHEMY_DATABASE_URL:
    DB_USER = os.getenv("POSTGRES_USER", "user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    DB_NAME = os.getenv("POSTGRES_DB", "heart_twin")
    DB_HOST = os.getenv("DB_HOST", "heart_db") 
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Driver compatibility fix
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
