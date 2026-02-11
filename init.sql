-- Enable the Timescale extension if not already enabled
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Table of metrics: Designed for high-frequency writing
CREATE TABLE IF NOT EXISTS heart_metrics (
    time        TIMESTAMPTZ       NOT NULL,
    bpm         DOUBLE PRECISION  NOT NULL,
    trimp       DOUBLE PRECISION  NOT NULL, -- Training Impulse
    hrr         DOUBLE PRECISION  NOT NULL, -- Heart Rate Reserve
    zone        VARCHAR(20)       NOT NULL,
    intensity   DOUBLE PRECISION,
    color       VARCHAR(20)
);

-- Convert in hypertable (fragmentation by time of 1 day by default)
SELECT create_hypertable('heart_metrics', 'time', if_not_exists => TRUE);

-- State (Configuration of the digital twin)
CREATE TABLE IF NOT EXISTS simulation_state (
    id                INT PRIMARY KEY,
    target_intensity  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Initial state (Singleton pattern in DB)
INSERT INTO simulation_state (id, target_intensity) 
VALUES (1, 0.0) 
ON CONFLICT (id) DO NOTHING;