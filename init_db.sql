-- 1. Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. Metrics table (Synchronized with Python)
CREATE TABLE IF NOT EXISTS heart_metrics (
    time        TIMESTAMPTZ       NOT NULL, 
    bpm         DOUBLE PRECISION  NOT NULL,
    trimp       DOUBLE PRECISION  NOT NULL,
    hrr         DOUBLE PRECISION  NOT NULL,
    zone        TEXT              NOT NULL, 
    intensity   DOUBLE PRECISION,
    color       TEXT
);

-- 3. Convert to Hypertable using the correct column
SELECT create_hypertable('heart_metrics', 'time', if_not_exists => TRUE);

-- 4. State table
CREATE TABLE IF NOT EXISTS simulation_state (
    id                INT PRIMARY KEY,
    target_intensity  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Initial seed
INSERT INTO simulation_state (id, target_intensity) 
VALUES (1, 0.0) 
ON CONFLICT (id) DO NOTHING;


-- Table for environmental metrics (Context for ML)
CREATE TABLE IF NOT EXISTS environmental_metrics (
    time TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    humidity DOUBLE PRECISION 
);

-- Convert to Hypertable for time series performance
SELECT create_hypertable('environmental_metrics', 'time', if_not_exists => TRUE);