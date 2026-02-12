import threading
import requests
import random
import time

API_URL = "http://localhost:8000/set_intensity"

def bombardear():
    for _ in range(20):
        val = round(random.uniform(0, 1), 2)
        try:
            requests.post(f"{API_URL}/{val}")
            print(f"Impact: {val}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.1)

# Create 10 threads (10 "Unitys" attacking at the same time)
hilos = [threading.Thread(target=bombardear) for _ in range(10)]

for t in hilos: t.start()
for t in hilos: t.join()