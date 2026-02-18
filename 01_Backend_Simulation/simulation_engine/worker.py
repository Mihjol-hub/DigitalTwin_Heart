import time
import os
import json
import threading
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from api.database import SessionLocal, init_db
from api.models import HeartLog
from core_logic.physio_model import HeartModel

class HeartEngineWorker:
    def __init__(self):
        self.patient = HeartModel(age=25, sex='male', resting_hr=62)
        
        self.current_intensity = 0.1
        self.current_temperature = 20.0
        self.current_slope = 0.0
        self.dt = 1.0 
        
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "HeartEngine_Core_V5")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ Engine Conectado. Escuchando realidad...")
        
            client.subscribe("heart/sensor/data")      
            client.subscribe("heart/env/terrain")      
            client.subscribe("heart/env/temperature")  
            client.subscribe("heart/physio/intensity") 
        else:
            print(f"❌ Error MQTT: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            raw = msg.payload.decode()
            topic = msg.topic
            
            try:
                data = json.loads(raw)
            except:
                data = raw

            
            if topic == "heart/sensor/data":
                # search 'bpm' in the JSON that sends your heart_data_ingestor.py
                bpm_val = data.get("bpm") if isinstance(data, dict) else float(data)
                if bpm_val:
                    self.patient.current_hr = float(bpm_val) # Anchor Nivel 3
                    print(f"🔄 [REAL SYNC] BPM Actualizado: {bpm_val}")

            elif topic == "heart/env/temperature":
                self.current_temperature = float(data.get("temp_c", 20.0))

            # C. Agent the Esfuerzo
            elif topic == "heart/env/terrain":
                self.current_slope = float(data.get("slope_percent", 0.0))
            elif topic == "heart/physio/intensity":
                self.current_intensity = float(data.get("intensity")) if isinstance(data, dict) else float(data)

        except Exception as e:
            print(f"⚠️ Error en mensaje: {e}")

    def simulation_loop(self):
        init_db()
        while True:
            db = SessionLocal()
            try:
                # The model processes the impact of temperature, slope and intensity
                metrics = self.patient.simulate_step(
                    intensity=self.current_intensity,
                    dt=self.dt,
                    temperature=self.current_temperature,
                    slope_percent=self.current_slope
                )
                
                # PERSISTENCE: Color and Data for Unity
                log = HeartLog(
                    bpm=metrics["bpm"],
                    trimp=metrics["trimp"],
                    zone=metrics["zone"],
                    color=metrics["color"], # Hexadecimal functional
                    intensity=self.current_intensity,
                    slope=self.current_slope,
                    time=datetime.now(timezone.utc)
                )
                db.add(log)
                db.commit()
                
                # Log de control
                print(f"[TIC] BPM: {log.bpm:.1f} | {log.zone} | Color: {log.color} | Temp: {self.current_temperature}°C")
                
            except Exception as e:
                db.rollback()
                print(f"❌ Error Loop: {e}")
            finally:
                db.close()
            time.sleep(self.dt)

    def run(self):
        sim_thread = threading.Thread(target=self.simulation_loop, daemon=True)
        sim_thread.start()
        self.client.connect(self.mqtt_host, 1883, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    worker = HeartEngineWorker()
    worker.run()