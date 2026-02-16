import time
import sys
import os
import json
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
sys.path.append(os.getcwd())

from api.database import SessionLocal, init_db
from api.models import HeartLog, SimulationState, EnvironmentalMetric
from core_logic.physio_model import HeartModel

MQTT_BROKER = os.getenv("MQTT_HOST", "mqtt_broker")
CLIENT_ID = "HeartEngine_Worker_V4"

# starting physio model
patient = HeartModel(age=25, resting_hr=60)

# global variable for temperature
current_temperature = 20.0 

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to MQTT Broker")
        # wildcard subscription to listen to everything starting with 'heart/'
        client.subscribe("heart/#") 
    else:
        print(f"❌ Error connecting to MQTT Broker: {rc}")

def on_message(client, userdata, msg):
    # global variable for temperature
    global current_temperature
    
    db = SessionLocal()
    try:
        payload = msg.payload.decode()
        
        # 1. Heart Telemetry 
        if msg.topic == "heart/telemetry":
            data = json.loads(payload)
            bpm_real = data.get("bpm", 60)
            
            # request intensity state from database
            state = db.query(SimulationState).first()
            user_intensity = state.target_intensity if state else 0.5
            
            # send temperature to digital brain
            metrics = patient.simulate_step(
                intensity=user_intensity, 
                temperature=current_temperature  
            )
            

            log = HeartLog(
                bpm=bpm_real,             
                trimp=metrics["trimp"],   
                hrr=metrics["hrr"],       
                zone=metrics["zone"],
                intensity=user_intensity, 
                color=metrics["color"]
            )
            db.add(log)
            # print combined data to verify that it works
            print(f"💓 Real: {bpm_real} | Sim(T={current_temperature}°C): {metrics['bpm']}")

        # 2. Environment Data 
        elif msg.topic == "heart/env/temperature":
            data = json.loads(payload)
            temp = data.get("temp_c")
            
            if temp is not None:
                # Update global memory of the worker
                current_temperature = float(temp)
                
                # Save in database for history
                env_log = EnvironmentalMetric(temperature=current_temperature)
                db.add(env_log)
                print(f"🌡️ Climate Data Update: {current_temperature}°C")

        # 3. Intensity from Ingestor 
        elif msg.topic == "heart/physio/intensity":
            try:
                new_intensity = float(payload)
                state = db.query(SimulationState).first()
                if not state:
                    state = SimulationState(target_intensity=new_intensity)
                    db.add(state) 
                else:
                    state.target_intensity = new_intensity
                    
                print(f"🏃 New Intensity Target: {new_intensity}")
            except ValueError:
                print(f"⚠️ Invalid intensity value received: {payload}")

        db.commit()
    except Exception as e:
        print(f"❌ Error processing message on {msg.topic}: {e}")
        db.rollback()
    finally:
        db.close()

def run_engine():
    # Initialize tables if they don't exist
    init_db()
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("🚀 Heart Engine Worker V4 (Thermo-Sensitive) starting...")
    
    # Robust reconnection loop
    connected = False
    while not connected:
        try:
            print(f"📡 Attempting connection to broker {MQTT_BROKER}...")
            client.connect(MQTT_BROKER, 1883, 60)
            connected = True
        except Exception as e:
            print(f"⏳ Broker not ready ({e}). Retrying in 2s...")
            time.sleep(2)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("🛑 Stopping Heart Engine Worker...")
        client.disconnect()

if __name__ == "__main__":
    run_engine()