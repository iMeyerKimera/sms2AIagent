# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for PostgreSQL, audio processing, and build tools
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    libpq-dev \
    alsa-utils \
    espeak \
    espeak-data \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Create directories for logs, media, static files, and data
RUN mkdir -p /app/logs /app/media /app/staticfiles /app/data

# Set permissions for directories and files
RUN chmod 755 /app && \
    chmod 777 /app/data && \
    chmod 777 /app/logs && \
    chmod 777 /app/media && \
    chmod 777 /app/staticfiles

# Create volume mount points for persistent data
VOLUME ["/app/data", "/app/logs", "/app/media", "/app/staticfiles"]

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables
ENV DJANGO_SETTINGS_MODULE=sms_agent.settings
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Waiting for database..."\n\
while ! pg_isready -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER; do\n\
  sleep 1\n\
done\n\
echo "Database is ready!"\n\
\n\
echo "Running Django migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput --clear\n\
\n\
echo "Starting Django application..."\n\
exec gunicorn sms_agent.wsgi:application \\\n\
    --bind 0.0.0.0:8000 \\\n\
    --workers 3 \\\n\
    --timeout 180 \\\n\
    --worker-class sync \\\n\
    --max-requests 1000 \\\n\
    --preload\n\
' > /app/start.sh && chmod +x /app/start.sh

# Health check using the Django health endpoint
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the startup script
CMD ["/app/start.sh"]