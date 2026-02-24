-- 1. Enable TimescaleDB extension (fundamental for time series)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. Table of heart metrics (Here we add SLOPE)
CREATE TABLE IF NOT EXISTS heart_metrics (
    time            TIMESTAMPTZ       NOT NULL, 
    bpm             DOUBLE PRECISION  NOT NULL,
    trimp           DOUBLE PRECISION  NOT NULL,
    eccentric_load  DOUBLE PRECISION,
    hrr             DOUBLE PRECISION, 
    hrrpt           DOUBLE PRECISION, -- HRRPT Transition
    sd1             DOUBLE PRECISION, -- SD1 (Short-term variability)
    sd2             DOUBLE PRECISION, -- SD2 (Long-term variability)
    zone            VARCHAR(30)       NOT NULL, 
    intensity       DOUBLE PRECISION,
    slope           DOUBLE PRECISION,
    color           VARCHAR(10)               
);

-- 3. Table for environmental metrics (Clima/Contaminación/Presión)
-- NOTE! Worker tries to save here, so this table is MANDATORY
CREATE TABLE IF NOT EXISTS environmental_metrics (
    time        TIMESTAMPTZ       NOT NULL,
    temperature DOUBLE PRECISION,
    humidity    DOUBLE PRECISION,
    pressure    DOUBLE PRECISION
);

-- 4. Convert both to Hypertables (TimescaleDB Optimization)
SELECT create_hypertable('heart_metrics', 'time', if_not_exists => TRUE);
SELECT create_hypertable('environmental_metrics', 'time', if_not_exists => TRUE);

-- 5. State of the simulation (Real-time configuration)
CREATE TABLE IF NOT EXISTS simulation_state (
    id                INT PRIMARY KEY,
    target_intensity  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Initial state
INSERT INTO simulation_state (id, target_intensity) 
VALUES (1, 0.0) 
ON CONFLICT (id) DO NOTHING;