-- 1. Activamos la extensión de TimescaleDB (fundamental para series temporales)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. Tabla de métricas del corazón (Aquí añadimos SLOPE)
CREATE TABLE IF NOT EXISTS heart_metrics (
    time        TIMESTAMPTZ       NOT NULL,
    bpm         DOUBLE PRECISION  NOT NULL,
    trimp       DOUBLE PRECISION  NOT NULL, -- Esfuerzo acumulado (Banister)
    hrr         DOUBLE PRECISION,           -- Recuperación cardíaca (puede ser NULL si no está en fase de recovery)
    zone        VARCHAR(30)       NOT NULL, -- Zona de entrenamiento
    intensity   DOUBLE PRECISION,           -- Intensidad enviada por el sensor/GPX
    slope       DOUBLE PRECISION,           -- [NUEVO] Inclinación del terreno (%)
    color       VARCHAR(10)                 -- Color para Unity (#RRGGBB)
);

-- 3. Tabla para métricas ambientales (Clima/Contaminación/Presión)
-- ¡OJO! Tu Worker intenta guardar aquí, así que esta tabla es OBLIGATORIA
CREATE TABLE IF NOT EXISTS environmental_metrics (
    time        TIMESTAMPTZ       NOT NULL,
    temperature DOUBLE PRECISION,
    humidity    DOUBLE PRECISION,
    pressure    DOUBLE PRECISION
);

-- 4. Convertimos ambas en Hypertables (Optimización de TimescaleDB)
SELECT create_hypertable('heart_metrics', 'time', if_not_exists => TRUE);
SELECT create_hypertable('environmental_metrics', 'time', if_not_exists => TRUE);

-- 5. Estado de la simulación (Configuración en tiempo real)
CREATE TABLE IF NOT EXISTS simulation_state (
    id                INT PRIMARY KEY,
    target_intensity  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Estado inicial
INSERT INTO simulation_state (id, target_intensity) 
VALUES (1, 0.0) 
ON CONFLICT (id) DO NOTHING;