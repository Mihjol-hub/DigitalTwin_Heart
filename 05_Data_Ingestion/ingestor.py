import time
import json
import random
import paho.mqtt.client as mqtt

# Settings the system nervous (MQTT)
MQTT_BROKER = "mqtt_broker"
MQTT_PORT = 1883
TOPIC_INTENSITY = "heart/physio/intensity"
TOPIC_ENV = "heart/env/temperature"

client = mqtt.Client()

def connect_mqtt():
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print("✅ Ingestor connected to MQTT Broker")
            break
        except:
            print("⏳ Waiting for Broker...")
            time.sleep(2)

def fetch_virtual_sensor_data():
    """
    Simulate the acquisition of data from a biomédical API (e.g. PhysioNet)
    and a climatic API for the Digital Twin.
    """
    # API 1: Physiological data (Real training load)
    virtual_intensity = random.uniform(0.1, 0.9) 
    
    # API 2: Climatic data (Temperature in Geneva)
    # The heat increases the stress on the heart
    ambient_temp = 25.0 + random.uniform(-2, 5) 
    
    return virtual_intensity, ambient_temp

if __name__ == "__main__":
    connect_mqtt()
    while True:
        intensity, temp = fetch_virtual_sensor_data()
        
        # Send as JSON for consistency
        client.publish(TOPIC_INTENSITY, json.dumps({"intensity": intensity}))
        client.publish(TOPIC_ENV, json.dumps({"temp_c": temp, "unit": "Celsius"}))
        
        print(f"📡 Sensor Virtual -> Intensity: {intensity:.2f} | Temp: {temp:.1f}°C")
        time.sleep(1)