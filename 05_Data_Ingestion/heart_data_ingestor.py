import os
import time
import json
import pandas as pd
import numpy as np
import vitaldb
import paho.mqtt.client as mqtt

# Setting from Docker
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt_broker")
MODE = os.getenv("DATA_MODE", "athlete") # 'athlete' o 'clinical'
CSV_PATH = "/app/datasets/heartrate_seconds_merged.csv"

client = mqtt.Client()

def connect_mqtt():
    while True:
        try:
            client.connect(MQTT_HOST, 1883, 60)
            print(f"✅ Connected to MQTT Broker in mode: {MODE}")
            break
        except:
            print("⏳ Waiting for Broker MQTT...")
            time.sleep(2)

def run_ingestor():
    connect_mqtt()
    
    if MODE == "athlete":
        print(f"🏃 Loading Kaggle data from {CSV_PATH}...")
        df = pd.read_csv(CSV_PATH)

        # take the first runner
        first_user_id = df['Id'].iloc[0]
        athlete_data = df[df['Id'] == first_user_id]

        print(f"👤 Reproducing data from Atleta ID: {first_user_id}")
        print(f"📊 Total beats to reproduce: {len(athlete_data)}")

        # Assuming the columns are 'Id', 'Time', 'Value'
        for _, row in athlete_data.iterrows():
            payload = {
                "bpm": float(row['Value']),
                "sensor_id": f"FITBIT_{first_user_id}",
                "timestamp": time.time(),
                "real_time_recorded": str(row['Time'])
            }

            client.publish("heart/sensor/data", json.dumps(payload))
            print(f"📡 [KAGGE-REAL] BPM: {row['Value']} | Hora original: {row['Time']}")

            time.sleep(1) # One beat per second

    elif MODE == "clinical":
        print("🏥  clinical mode connect with data from VitalDB (Case 1)...")
        # This does not download the 95GB, only case 1
        vals = vitaldb.load_case(1, ['Solar8000/HR'], interval=1)
        for hr in vals:
            if hr[0] and not np.isnan(hr[0]):
                payload = {
                    "bpm": float(hr[0]),
                    "sensor_id": "VITALDB_PATIENT_001",
                    "timestamp": time.time()
                }
                client.publish("heart/sensor/data", json.dumps(payload))
                time.sleep(1)


if __name__ == "__main__":
    run_ingestor()