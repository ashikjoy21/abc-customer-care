FROM python:3.9-slim

WORKDIR /app

# Install Redis
RUN apt-get update && apt-get install -y redis-server

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create startup script with proper port binding
RUN echo '#!/bin/bash\nredis-server --daemonize yes\npython api_server.py' > start.sh
RUN chmod +x start.sh

# Set environment variables
ENV PORT=8080

# Expose only a single port
EXPOSE 8080

# Start Redis and run the application
CMD ["./start.sh"] 