#!/bin/bash

# Colors for LOGS
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting development environment: DigitalTwin_Heart${NC}"

# 1. Clean previous containers
echo -e "${YELLOW}🧹 Clean previous containers...${NC}"
docker compose down --remove-orphans

# 2. Build and start base infrastructure (DB and Broker)
echo -e "${YELLOW}🏗️  Build and start DB and MQTT...${NC}"
docker compose up --build -d heart_db mqtt_broker

# 3. Wait for MQTT broker to be ready (Healthcheck)
echo -ne "${YELLOW}⏳ Waiting for MQTT broker to respond...${NC}"
until docker exec mqtt_broker mosquitto_pub -t "test" -m "check" > /dev/null 2>&1; do
    echo -ne "."
    sleep 2
done
echo -e "${GREEN} ¡Broker ready!${NC}"


# 3.5 Wait for PostgreSQL database to be ready (Healthcheck)
echo -ne "${YELLOW}⏳ Waiting for Database to be ready...${NC}"
until docker exec heart_db pg_isready -U user -d heart_twin -h localhost > /dev/null 2>&1; do
    echo -ne "."
    sleep 4
done
# Add security margin for the TCP port to open completely
sleep 6
echo -e "${GREEN} ¡Database ready!${NC}"

# 4. Inject retained data immediately
# This ensures the engine never sees the default 20.0 degrees
echo -e "${BLUE}🌡️  Injecting initial climate of Geneva (6.19°C)...${NC}"
docker exec mqtt_broker mosquitto_pub -r -t "heart/env/temperature" -m '{"temp_c": 6.19}'
docker exec mqtt_broker mosquitto_pub -r -t "heart/env/terrain" -m '{"slope_percent": 0.0}'

# 5. Start the rest of the system
echo -e "${YELLOW}⚙️  Starting Engine, Brain, Climate Fetcher and Inference Engine...${NC}"
docker compose up -d simulation_engine heart_brain heart_climate heart_inference

# 6. Show final state
echo -e "${GREEN}✅ System running.${NC}"
docker compose ps

# 7. Follow the engine logs to verify
echo -e "${BLUE}📺 Following engine logs (Ctrl+C to exit)...${NC}"
docker logs -f heart_engine | grep "TIC"