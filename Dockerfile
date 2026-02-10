FROM python:3.11-slim

# Evita que el buffer se trague los logs (necesario para ver errores en tiempo real)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/01_Backend_Simulation

RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pytest requests uvicorn httpx

COPY . .


CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]