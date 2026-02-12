import time
import sys
import os
import json
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

# Asegurar que encuentre los módulos
sys.path.append(os.getcwd())

from api.database import SessionLocal, init_db
from api.models import HeartLog, SimulationState, EnvironmentalMetric
from core_logic.physio_model import HeartModel

# --- CONFIGURACIÓN ---
MQTT_BROKER = os.getenv("MQTT_HOST", "mqtt_broker")
CLIENT_ID = "HeartEngine_Worker_V3" # <--- VARIABLE DEFINIDA
patient = HeartModel(age=25, resting_hr=60)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Conectado al Broker MQTT")
        client.subscribe("heart/#") # Suscripción a TODO el ecosistema
    else:
        print(f"❌ Error de conexión: {rc}")

def on_message(client, userdata, msg):
    db = SessionLocal()
    try:
        payload = msg.payload.decode()
        
        # RUTA 1: Telemetría Cardíaca
        if msg.topic == "heart/telemetry":
            data = json.loads(payload)
            bpm_real = data.get("bpm", 60)
            state = db.query(SimulationState).first()
            user_intensity = state.target_intensity if state else 0.5
            metrics = patient.simulate_step(intensity=user_intensity)
            metrics["bpm"] = bpm_real
            log = HeartLog(
                bpm=metrics["bpm"], trimp=metrics["trimp"],
                hrr=metrics["hrr"], zone=metrics["zone"],
                intensity=user_intensity, color=metrics["color"]
            )
            db.add(log)
            print(f"💓 BPM: {bpm_real}")

        # RUTA 2: Datos Ambientales
        elif msg.topic == "heart/env/temperature":
            data = json.loads(payload)
            temp = data.get("temp_c")
            env_log = EnvironmentalMetric(temperature=temp)
            db.add(env_log)
            print(f"🌡️ Clima Guardado: {temp}°C")

        # RUTA 3: Intensidad desde Ingestor
        elif msg.topic == "heart/physio/intensity":
            new_intensity = float(payload)
            state = db.query(SimulationState).first()
            if not state:
                state = SimulationState(target_intensity=new_intensity)
            else:
                state.target_intensity = new_intensity
            db.add(state)
            print(f"🏃 Nueva Intensidad: {new_intensity}")

        db.commit()
    except Exception as e:
        print(f"❌ Error en tópico {msg.topic}: {e}")
        db.rollback()
    finally:
        db.close()


def run_engine():
    init_db()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("🚀 Motor del Gemelo Digital Nivel 3 arrancando...")
    
    # Bucle de reconexión robusto
    connected = False
    while not connected:
        try:
            print(f"📡 Intentando conectar al broker en {MQTT_BROKER}...")
            client.connect(MQTT_BROKER, 1883, 60)
            connected = True
        except Exception as e:
            print(f"⏳ El broker no está listo aún ({e}). Reintentando en 2s...")
            time.sleep(2)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("🛑 Deteniendo motor...")
        client.disconnect()


if __name__ == "__main__":
    run_engine()