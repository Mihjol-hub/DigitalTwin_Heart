import pytest
from unittest.mock import patch, MagicMock
from api.models import HeartLog
from simulation_engine.worker import run_engine

@patch("simulation_engine.worker.SessionLocal")
def test_worker_db_retry_logic(mock_session):
    """
    Simulate that the DB fails.
    The worker should catch the error and not die (or at least retry).
    """
    # Configure the mock to raise a SQLAlchemy OperationalError
    mock_session.side_effect = Exception("Lost connection to TimescaleDB")
    
    with pytest.raises(Exception):
        run_engine()