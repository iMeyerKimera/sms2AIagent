# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for audio processing and SQLite
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    alsa-utils \
    espeak \
    espeak-data \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Create directories for logs and databases
RUN mkdir -p /app/logs /app/templates/admin

# Set permissions for database files
RUN chmod 755 /app && chmod 666 /app/*.db 2>/dev/null || true

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Health check using the enhanced health endpoint
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run with gunicorn for production with increased timeout for AI processing
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers=3", "--timeout=180", "--worker-class=sync", "--max-requests=1000", "--preload"]