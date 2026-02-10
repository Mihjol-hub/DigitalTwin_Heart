import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Database URL for testing
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    DB_USER = os.getenv("POSTGRES_USER", "user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    DB_NAME = os.getenv("POSTGRES_DB", "heart_twin")
    DB_HOST = os.getenv("DB_HOST", "heart_db") 
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

#Driver compatibility fix
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
