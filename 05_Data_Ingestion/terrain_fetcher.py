import requests
import time
import json
import os
import paho.mqtt.client as mqtt

# Public API: "https://api.open-elevation.com/api/v1/lookup"
#  Docker: "http://localhost:8080/api/v1/lookup"
ELEVATION_URL = "http://heart_elevation_server:8080/api/v1/lookup"
MQTT_BROKER = os.getenv("MQTT_HOST", "mqtt_broker")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Terrain_Engine")

def get_elevation(lat, lon):
    try:
        payload = {"locations": [{"latitude": lat, "longitude": lon}]}
        response = requests.post(ELEVATION_URL, json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()['results'][0]['elevation']
    except Exception as e:
        print(f"⚠️ Error de Elevación: {e}")
    return 0

def run_terrain_service():
    client.connect(MQTT_BROKER, 1883, 60)
    
    # Test coordinates (Geneva - going up towards Salève)
    current_lat, current_lon = 46.2044, 6.1432
    prev_elevation = get_elevation(current_lat, current_lon)

    while True:
        # Simulate movement: advance a bit the latitude (going up)
        current_lat += 0.0001 
        current_elevation = get_elevation(current_lat, current_lon)
        
        # Calculate slope (simplified): height difference
        # In a real route, we would use the distance traveled
        slope = (current_elevation - prev_elevation) / 10.0 # assuming 10m of advance
        
        payload = {
            "elevation": current_elevation,
            "slope_percent": round(slope * 100, 2),
            "lat": current_lat,
            "lon": current_lon
        }
        
        client.publish("heart/env/terrain", json.dumps(payload))
        print(f"⛰️ Terreno: {current_elevation}m | Pendiente: {payload['slope_percent']}%")
        
        prev_elevation = current_elevation
        time.sleep(5) # Consultamos cada 5 seg para no saturar la API

if __name__ == "__main__":
    run_terrain_service()