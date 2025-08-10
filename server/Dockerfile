FROM python:3.12-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
#    libsndfile1 \

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code directly to /app
COPY api/ ./server/api/
COPY core/ ./server/core/
COPY models/ ./server/models/
COPY utils/ ./server/utils/
COPY main.py ./server/

# Create directories for voices and models
RUN mkdir -p /app/voices

# Expose port
EXPOSE 8420

# Set environment variables
ENV PLOMTTS_HOST=0.0.0.0
ENV PLOMTTS_PORT=8420
ENV PLOMTTS_VOICES_DIR=/app/voices

# Run the application
CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8420"]
