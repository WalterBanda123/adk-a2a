# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for potential image processing and other requirements
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create necessary directories and files
RUN mkdir -p data/user_profiles reports logs
RUN touch .env

# Set environment variables
ENV PYTHONPATH=/app
ENV STORE_AGENTS_HOST=0.0.0.0
ENV STORE_AGENTS_PORT=8003

# Expose the port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python", "-m", "agents.assistant"]
