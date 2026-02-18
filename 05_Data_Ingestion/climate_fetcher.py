import paho.mqtt.client as mqtt
import requests
import time
import json
import os

# Configuration from environment variables
# Get your free key at: https://openweathermap.org/api
API_KEY = os.getenv("API_KEY", "TU_API_KEY_AQUI") 
CITY = "Geneva,CH"
MQTT_BROKER = os.getenv("MQTT_HOST", "mqtt_broker")
TOPIC_ENV = "heart/env/temperature"

# setting up the MQTT client 
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Climate_Fetcher_RealTime")

def get_real_weather():
    """
    Request the real temperature of Geneva using OpenWeatherMap.
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        data = response.json()
        return data['main']['temp']
    except Exception as e:
        print(f"❌ Error connecting to the weather API: {e}")
        return None

def run_scheduler():
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        print(f"🚀 [LEVEL 3] Climate Fetcher started for {CITY}.")
    except Exception as e:
        print(f"📡 Error connecting to MQTT broker: {e}")
        return

    while True:
        print(f"📡 Consultando clima real para {CITY}...")
        temp = get_real_weather()
        
        if temp is not None:
            payload = {
                "temp_c": float(temp),
                "city": CITY,
                "timestamp": time.time(),
                "provider": "OpenWeatherMap_RealTime"
            }
            client.publish(TOPIC_ENV, json.dumps(payload))
            print(f"🌡️  REAL DATA SENT: {temp}°C (Geneva)")
        else:
            print("⚠️ Could not get the weather. Retrying...")

        
        time.sleep(300) 

if __name__ == "__main__":
    run_scheduler()