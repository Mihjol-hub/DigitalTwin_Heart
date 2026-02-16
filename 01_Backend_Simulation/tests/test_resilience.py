import pytest
from unittest.mock import patch, MagicMock
from simulation_engine.worker import run_engine

@patch("simulation_engine.worker.mqtt.Client")
@patch("simulation_engine.worker.SessionLocal")
@patch("simulation_engine.worker.time.sleep", return_value=None)
def test_worker_full_resilience(mock_sleep, mock_session, mock_mqtt_class):
    """
    Validación de Resiliencia para la Demo BMST'26.
    Verifica que el motor de simulación no muere si los servicios externos fallan.
    """
    # 1. Setup del Mock MQTT
    mock_client_instance = mock_mqtt_class.return_value
    
    # 2. Forzamos fallo en el primer intento y éxito en el segundo
    mock_client_instance.connect.side_effect = [Exception("MQTT Broker Offline"), None]
    
    # 3. Al entrar en el loop principal, salimos con éxito para la demo
    mock_client_instance.loop_forever.side_effect = BaseException("DemoExit")

    # Ejecución
    with pytest.raises(BaseException, match="DemoExit"):
        run_engine()

    # 4. LA PRUEBA REINA: 
    # El método 'connect' debe haberse llamado 2 veces (Fallo + Reintento)
    assert mock_client_instance.connect.call_count == 2
    print("\n✅ [DEMO LOG] Resiliencia de red confirmada: El sistema se recuperó del fallo del Broker.")

