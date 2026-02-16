import paho.mqtt.client as mqtt
import json
import time
import os
import math

BROKER = os.getenv("MQTT_HOST", "mqtt_broker") 
TOPIC = "heart/telemetry"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "Physiological_Mock_Sensor")
client.connect(BROKER, 1883, 60)

print(f"📡 Sensor connected to broker: {BROKER}. Scenario: Interval Training Simulation")

def simulate_heart_rate(t_seconds):
    """
    Simulate a physiological profile:
    0-30s: Rest (60-65 BPM)
    30-90s: Linear increase (Warm-up)
    90-150s: High intensity (Sprint)
    150s+: Recovery (HRR)
    """
    if t_seconds < 30:
        return 60 + math.sin(t_seconds) * 2  # Rest with slight variability
    elif t_seconds < 90:
        return 60 + (t_seconds - 30) * 1.5   # Constant increase
    elif t_seconds < 150:
        return 150 + math.sin(t_seconds) * 5 # Maximum effort
    else:
        # Exponential recovery model (Antonin will love this)
        t_rec = t_seconds - 150
        return 70 + (155 - 70) * math.exp(-0.03 * t_rec)

start_time = time.time()

try:
    while True:
        elapsed = time.time() - start_time
        current_bpm = round(simulate_heart_rate(elapsed), 2)
        
        payload = {
            "bpm": current_bpm,
            "timestamp": time.time(),
            "sensor_id": "MOCK_V2_PHYSIO"
        }
        
        client.publish(TOPIC, json.dumps(payload))
        print(f"📤 [SCENARIO] Time: {int(elapsed)}s | Sent: {current_bpm} BPM")
        time.sleep(1)
except KeyboardInterrupt:
    client.disconnect()