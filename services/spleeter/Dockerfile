FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
# Set the model directory to a host-mounted volume
ENV MODEL_PATH=/pipeline-data/models/spleeter

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gosu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY services/spleeter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/spleeter /app
COPY services/common /app/common

# Create an entrypoint script that sets the proper user
COPY services/spleeter/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "splitter.py"]
