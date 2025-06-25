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
RUN echo '#!/bin/bash\nredis-server --daemonize yes\npython http_server.py &\npython main_enhanced.py --host=0.0.0.0 --port=8765' > start.sh
RUN chmod +x start.sh

# Set environment variables
ENV PORT=8080

# Expose ports
EXPOSE 8080
EXPOSE 8765

# Start Redis and run the application
CMD ["./start.sh"] 