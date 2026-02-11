import time
import sys
import os
import json
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

# Aseguramos que el worker encuentre la carpeta 'api' y 'core_logic'
sys.path.append(os.getcwd())

from api.database import SessionLocal, init_db
from api.models import HeartLog, SimulationState
from core_logic.physio_model import HeartModel

# 1. CONFIGURACIÓN DEL MODELO Y MQTT
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
        # A. Recibir el dato real del sensor (vía MQTT)
        payload = msg.payload.decode()
        data = json.loads(payload)
        bpm_real = data.get("bpm", 60)

        # B. CONSULTA V2P: Leer la intensidad que puso el usuario en Unity
        # Buscamos el estado actual en la tabla simulation_state
        state = db.query(SimulationState).first()
        # Si no hay nada en la tabla todavía, usamos 0.5 por defecto
        user_intensity = state.target_intensity if state else 0.5

        # C. PROCESAMIENTO FISIOLÓGICO:
        # Pasamos la intensidad de Unity al modelo de Python
        metrics = patient.simulate_step(intensity=user_intensity)
        
        # Sobreescribimos el BPM simulado con el BPM REAL que viene del sensor
        metrics["bpm"] = bpm_real

        # D. PERSISTENCIA: Guardamos el log completo en la DB
        log = HeartLog(
            bpm=metrics["bpm"],
            trimp=metrics["trimp"],
            hrr=metrics["hrr"],
            zone=metrics["zone"],
            intensity=user_intensity, # Guardamos la intensidad que se usó
            color=metrics["color"]
        )
        
        db.add(log)
        db.commit()
        
        print(f"💓 [Nivel 3] BPM: {bpm_real} | Intensidad Unity: {user_intensity:.2f} | Zona: {metrics['zone']}")

    except Exception as e:
        print(f"❌ Error en el procesamiento del mensaje: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Inicializar las tablas si no existen
    init_db()
    
    # Configurar el cliente MQTT con la versión de API requerida por Paho 2.0
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("🚀 Worker de Gemelo Digital (Nivel 3) esperando datos...")
    
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("🛑 Deteniendo el worker...")
        client.disconnect()
        