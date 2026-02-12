import time
import sys
import os
import json
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

sys.path.append(os.getcwd())

from api.database import SessionLocal, init_db
from api.models import HeartLog, SimulationState
from core_logic.physio_model import HeartModel

# CONFIGURACIÓN
patient = HeartModel(age=25, resting_hr=60)
MQTT_BROKER = os.getenv("MQTT_HOST", "mqtt_broker") 
MQTT_TOPIC = "heart/telemetry"
CLIENT_ID = "PhysioWorker_Primary"

def on_connect(client, userdata, flags, rc):
    print(f"✅ Conectado al Broker MQTT (Código: {rc})")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    db = SessionLocal()
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        bpm_real = data.get("bpm", 60)

        # CONSULTA V2P: Comunicación bidireccional desde Unity [cite: 11]
        state = db.query(SimulationState).first()
        user_intensity = state.target_intensity if state else 0.5

        # PROCESAMIENTO P2V [cite: 11]
        metrics = patient.simulate_step(intensity=user_intensity)
        metrics["bpm"] = bpm_real

        log = HeartLog(
            bpm=metrics["bpm"],
            trimp=metrics["trimp"],
            hrr=metrics["hrr"],
            zone=metrics["zone"],
            intensity=user_intensity,
            color=metrics["color"]
        )
        
        db.add(log)
        db.commit()
        print(f"💓 [Nivel 3] BPM: {bpm_real} | Intensidad Unity: {user_intensity:.2f} | Zona: {metrics['zone']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def run_engine():
    """Función principal para arrancar el motor de simulación."""
    init_db()
    
    # Mantenemos todo dentro para mejor encapsulación
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("🚀 Worker de Gemelo Digital (Nivel 3) esperando datos...")
    
    try:
        # Try to connect to the broker (using environment variables for Docker)
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_forever()
    except Exception as e:
        #
        print(f"🛑 Error crítico en el motor: {e}")
        client.disconnect()
        raise e  

if __name__ == "__main__":
    run_engine()