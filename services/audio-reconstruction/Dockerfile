FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-clean.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY audio_reconstructor.py .

# Create non-root user
RUN useradd -m -u 1001 audiorecon && \
    chown -R audiorecon:audiorecon /app

USER audiorecon

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f "python audio_reconstructor.py" || exit 1

# Run the service
CMD ["python", "audio_reconstructor.py"]
