-- Habilitar la extensión de Timescale si no estuviera por defecto
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Tabla de métricas: Diseñada para alta frecuencia de escritura
CREATE TABLE IF NOT EXISTS heart_metrics (
    time        TIMESTAMPTZ       NOT NULL,
    bpm         DOUBLE PRECISION  NOT NULL,
    trimp       DOUBLE PRECISION  NOT NULL, -- Training Impulse
    hrr         DOUBLE PRECISION  NOT NULL, -- Heart Rate Reserve
    zone        INTEGER           NOT NULL,
    intensity   DOUBLE PRECISION  NOT NULL
);

-- Convertir en hypertable (fragmentación por tiempo de 1 día por defecto)
SELECT create_hypertable('heart_metrics', 'time', if_not_exists => TRUE);

-- Tabla de estado (Configuración del gemelo digital)
CREATE TABLE IF NOT EXISTS simulation_state (
    id                INT PRIMARY KEY,
    target_intensity  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Estado inicial (Singleton pattern en DB)
INSERT INTO simulation_state (id, target_intensity) 
VALUES (1, 0.0) 
ON CONFLICT (id) DO NOTHING;