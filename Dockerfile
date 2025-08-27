# Use Python 3.8 slim image for smaller size
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for any packages)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# keep output unbuffered for real-time logs
ENV PYTHONUNBUFFERED=1

# Do NOT store secrets here; provide them at runtime
CMD ["python", "launcher.py"]
