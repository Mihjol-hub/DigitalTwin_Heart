import pytest
from unittest.mock import patch, MagicMock
from simulation_engine.worker import HeartEngineWorker

@patch("simulation_engine.worker.mqtt.Client")
@patch("simulation_engine.worker.SessionLocal")
@patch("simulation_engine.worker.time.sleep", return_value=None)
def test_worker_full_resilience(mock_sleep, mock_session, mock_mqtt_class):
    # 1. Setup del Mock MQTT
    mock_client_instance = mock_mqtt_class.return_value
    
    # 2. Force the connection to fail in the first attempt and succeed in the second
    mock_client_instance.connect.side_effect = [Exception("MQTT Broker Offline"), None]
    
    # 3. When entering the main loop, exit with a controlled exception
    mock_client_instance.loop_forever.side_effect = BaseException("DemoExit")

    worker = HeartEngineWorker()

    # Execution: Capture any error to analyze it
    try:
        worker.run()
    except BaseException as e:
        # If the error was the Broker Offline and it didn't jump to the retry, 
        
        if "DemoExit" in str(e):
            print("\n✅ Resiliencia confirmed: The system overcame the failure and reached the loop.")
        else:
            pytest.fail(f"The worker died with the original error: {e}. No retry!")

    # 4. Verify that the connection was attempted twice
    assert mock_client_instance.connect.call_count == 2