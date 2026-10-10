FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements-docker.txt ./requirements-docker.txt
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY app.py ./app.py
COPY .streamlit/config.toml ./.streamlit/config.toml
COPY models/kmeans_metadata_5min.json ./models/kmeans_metadata_5min.json
COPY data/processed/metropt_condition_monitoring_5min.csv ./data/processed/metropt_condition_monitoring_5min.csv
COPY data/processed/metropt_window_features_5min.csv ./data/processed/metropt_window_features_5min.csv
COPY data/processed/metropt_reported_event_summary_5min.csv ./data/processed/metropt_reported_event_summary_5min.csv
COPY data/processed/metropt_cluster_transitions_5min.csv ./data/processed/metropt_cluster_transitions_5min.csv

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
