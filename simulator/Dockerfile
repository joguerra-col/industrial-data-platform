FROM python:3.13-slim

WORKDIR /app
COPY src/ /app/
COPY config/ /app/config/
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    QUARRY_SIM_OUTPUT=/data

ENTRYPOINT ["python", "-m", "quarry_sim"]
