FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y libpq-dev gcc --no-install-recommends && \
    pip install --no-cache-dir paho-mqtt pandas numpy vitaldb requests


COPY . .

# 
CMD ["python", "ingestor.py"]