import time
import os
import json
import threading
import paho.mqtt.client as mqtt
from api.database import SessionLocal, init_db
from api.models import HeartLog, SimulationState, EnvironmentalMetric
from core_logic.physio_model import HeartModel

class HeartEngineWorker:
    def __init__(self):
        # 1. Configure the Heart Model (Biological Parameters)
        # In an advanced version, these would come from the DB for each patient
        self.patient = HeartModel(age=25, sex='male', resting_hr=62)
        
        # 2. Internal State (Short-term Memory)
        self.current_intensity = 0.1  # Resting state [cite: 260]
        self.current_temperature = 20.0 # [cite: 1395]
        self.dt = 1.0 # Tick of 1 second for SNA resolution [cite: 1207]
        self.current_slope = 0.0
        
        # 3. Configure the MQTT Client
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "HeartEngine_Core_V5")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ Engine Connected to MQTT Broker")
            client.subscribe("heart/env/temperature")
            client.subscribe("heart/physio/intensity")
        else:
            print(f"❌ Error connecting to MQTT Broker: {rc}")

    def on_message(self, client, userdata, msg):
        """update internal state based on external sensors"""
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == "heart/env/terrain":
                self.current_slope = float(payload.get("slope_percent", 0.0))
                print(f"⛰️ Terrain updated: {self.current_slope}%")
            
            elif msg.topic == "heart/env/temperature":
                self.current_temperature = float(payload.get("temp_c", 20.0))
                print(f"🌡️ Climate updated: {self.current_temperature}°C")
                
            elif msg.topic == "heart/physio/intensity":
                self.current_intensity = float(payload.get("intensity", 0.1))
                print(f"🏃 Intensity updated: {self.current_intensity}")

        except Exception as e:
            print(f"⚠️ Error processing message: {e}")

    def simulation_loop(self):
        """Main loop: The heart beats independently of the network"""
        init_db()
        print("🚀 Starting physiological simulation loop...")
        
        while True:
            db = SessionLocal()
            try:
                # The Engine processes a time step based on the last received info
                # Applies the asymmetry of the SNA (SNP vs SNS) and Banister's formula [cite: 375, 1207]
                metrics = self.patient.simulate_step(
                    intensity=self.current_intensity,
                    dt=self.dt,
                    temperature=self.current_temperature,
                    slope_percent=self.current_slope
                )
                
                # Persist the metrics in TimescaleDB (Optimized for time series)
                log = HeartLog(
                    bpm=metrics["bpm"],
                    trimp=metrics["trimp"],
                    hrr=metrics["hrr_1min"],
                    zone=metrics["zone"],
                    intensity=self.current_intensity,
                    slope=self.current_slope,
                )
                db.add(log)
                db.commit()
                
                # Feedback in console (Optional for debug)
                print(f"[TIC] BPM: {metrics['bpm']} | TRIMP: {metrics['trimp']} | Zone: {metrics['zone']}")
                
            except Exception as e:
                print(f"❌ Error in the simulation loop: {e}")
                db.rollback()
            finally:
                db.close()
            
            # Wait exactly the dt for the next heartbeat/calculation
            time.sleep(self.dt)

    def run(self):
        # 1. start the simulation thread
        sim_thread = threading.Thread(target=self.simulation_loop, daemon=True)
        sim_thread.start()
    
        # 2. try to connect to the MQTT broker
        print("📡 Trying to connect to the MQTT broker...")
        connected = False
        while not connected:
            try:
                # This is where the resilience test will bite the hook
                self.client.connect(self.mqtt_host, 1883, 60)
                connected = True
                print("✅ MQTT connection established successfully.")
            except Exception as e:
                print(f"⚠️ Connection error: {e}. Retrying in 2 seconds...")
                time.sleep(2)  # This allows the test to see the second attempt

        # 3. Once connected, loop_forever takes care of maintaining the connection active
        # and automatically reconnecting if it fails after starting.
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user.")
        except BaseException as e:
            # This will catch the "DemoExit" from the test
            if "DemoExit" in str(e):
                raise e
            print(f"❌ Critical error in the simulation loop: {e}")


def run_engine():
    """Fonction bridge betwin worker and main"""
    worker = HeartEngineWorker()
    worker.run()

if __name__ == "__main__":
    run_engine()