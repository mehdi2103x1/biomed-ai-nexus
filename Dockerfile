# BioMed AI Nexus — container image
FROM python:3.11-slim

# System libs needed by OpenCV (headless) and matplotlib.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train models at build time if they are not already committed.
RUN python -c "from pathlib import Path; import sys; \
    sys.exit(0) if (Path('models/metrics.json').exists()) else None" \
    || python train.py --fast

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
