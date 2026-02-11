import paho.mqtt.client as mqtt
import json
import time
import random
import os

# CONFIGURACIÓN PRO: Lee de variable de entorno o usa el nombre del servicio
BROKER = os.getenv("MQTT_HOST", "mqtt_broker") 
TOPIC = "heart/telemetry"

# Usamos la misma versión de API que el worker para ser consistentes
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "Mock_Chest_Sensor")
client.connect(BROKER, 1883, 60)

print(f"📡 Sensor conectado al broker: {BROKER}. Enviando...")

try:
    while True:
        current_bpm = round(random.uniform(70, 140), 2)
        payload = {"bpm": current_bpm}
        client.publish(TOPIC, json.dumps(payload))
        print(f"📤 Enviado al Gemelo: {current_bpm} BPM")
        time.sleep(1)
except KeyboardInterrupt:
    client.disconnect()