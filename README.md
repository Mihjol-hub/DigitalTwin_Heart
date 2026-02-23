¡Aquí lo tienes! He redactado este `README.md` (o documento de Onboarding) estructurándolo para que Laurenz entienda de inmediato la magnitud del proyecto, la arquitectura de microservicios, el rigor científico que has aplicado y cómo arrancar su entorno local sin dolores de cabeza.

He utilizado un tono profesional, colaborativo y muy claro. Puedes copiar este texto directamente y guardarlo como `README.md` en la raíz de tu repositorio.

---

# 🫀 Heart Rate Digital Twin (Master's Project)

Welcome to the **Heart Rate Digital Twin** project, Laurenz! 🚀

This repository houses a highly decoupled, microservices-based Digital Twin designed to simulate physiological heart responses in real-time. It reacts to physical exertion, terrain inclination, and environmental factors (like temperature), while validating its accuracy against real-world Kaggle datasets.

As we discussed, I am currently focusing on the final architectural piece: a high-performance Machine Learning inference engine in Rust. Please review this document to get up to speed with our current state. **Note: This architecture is a living system. If you have ideas to improve the database, the UI, or the algorithms, your input is highly encouraged!**

---

## 🏗️ 1. System Architecture

The project is fully containerized using Docker and orchestrated via Docker Compose. The components communicate asynchronously using an Event-Driven Architecture.

* **Message Broker (`mqtt_broker`):** Eclipse Mosquitto. Acts as the central nervous system handling real-time data streaming between the environment, the engine, and the API.
* **Database (`heart_db`):** **TimescaleDB** (PostgreSQL 16). Optimized for time-series data using hypertables (`heart_metrics` and `environmental_metrics`).
* **Simulation Engine (`heart_engine`):** A Python-based worker that continuously listens to MQTT topics, processes the physiological mathematics, and logs the state to the database.
* **Digital Twin Brain (`heart_brain`):** A **FastAPI** backend that exposes REST endpoints and a **WebSocket** connection for real-time frontend streaming.
* **Data Ingestion (`heart_climate`, etc.):** Microservices dedicated to fetching real-world context (e.g., current temperature in Geneva) and injecting real athlete data.
* **ML Inference (`heart_inference`):** A high-performance **Rust** microservice using `tract-onnx` to run an Artificial Neural Network (predicting clinical states like Anesthesia Depth based on BPM and HRV).

---

## 🧬 2. The Physiological Model (Core Science)

The engine (`core_logic/physio_model.py`) doesn't just generate random numbers; it uses established sports science and clinical mathematics:

* **TRIMP (Training Impulse):** Uses Banister's (1991) exponential formula to calculate cumulative fatigue based on Heart Rate Reserve (HRR) and gender-specific blood lactate weighting factors.
* **Environmental Drift:** If the temperature exceeds 25°C, the model induces cardiovascular drift, mathematically simulating the body's effort to cool down.
* **Terrain Slope:** Inclination directly modifies the effective intensity using a polynomial impact factor, causing realistic HR spikes during uphill climbs.
* **HRV & RMSSD:** Maintains a short-term memory (30s deque window) of RR intervals to dynamically calculate the Root Mean Square of Successive Differences (RMSSD), a gold-standard stress metric.
* **Heart Rate Recovery (HRR):** Automatically detects resting phases after high intensity to calculate the 1-minute HRR drop.

---

## 🔬 3. Scientific Validation & Testing

This is not a toy model. The simulation is continuously tested against real human data:

* **Continuous Validation:** Scripts (`continuous_validation.py`) extract real events from Kaggle datasets and run the Digital Twin alongside them. We are currently achieving an **RMSE of ~5.27 BPM** compared to real human data.
* **Clinical Phase Transition:** We use Savitzky-Golay filters to mathematically detect Heart Rate Recovery Phase Transitions (HRRPT).
* **Automated Tests:** The project includes a robust Pytest suite (`docker-compose.test.yml`) with 20+ tests covering unit logic, API sanitization, and **System Resilience** (e.g., verifying the engine can recover if the MQTT broker drops offline).

---

## 🎮 4. Visualization (Unity)

The frontend is built in **Unity** (`03_Visualization_Unity`).
To ensure zero performance bottlenecks, Unity connects to the FastAPI backend via **WebSockets**. A C# script (`HeartConnector.cs`) continuously listens to the stream at 60 FPS, dynamically altering the color of the 3D representation based on the HR Zone and pulsing in perfect sync with the calculated BPM.

---

## 🚀 5. Getting Started (Onboarding)

To spin up the entire ecosystem on your local machine, you don't need to manually build each container. Just use the development script:

1. Clone the repository.
2. Ensure Docker and Docker Compose are installed.
3. Run the orchestration script:
```bash
bash run_dev.sh

```



This script will:

* Clean previous orphan containers.
* Build and start the Database and MQTT Broker.
* Wait for healthchecks to pass.
* Inject baseline environmental data (e.g., Geneva climate).
* Boot up the Engine, the FastAPI Brain, the Ingestors, and the Rust ML Microservice.

Once running, you can monitor the engine's heartbeat directly in the terminal logs.

---

