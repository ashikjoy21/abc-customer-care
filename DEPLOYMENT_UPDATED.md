# Updated Deployment Guide for ABC Customer Care

This guide explains how to deploy the updated ABC Customer Care system to Google Cloud Platform (GCP). The system now uses a combined API server that handles both HTTP endpoints and WebSocket connections through a single port.

## Key Changes

1. **Single Port Architecture**: The system now uses a single port (8080) for both HTTP and WebSocket connections
2. **FastAPI Integration**: All endpoints are now handled by FastAPI
3. **Exotel Passthru Support**: Added support for Exotel IVR option notifications via HTTP
4. **WebSocket Path**: WebSocket connections are now available at the `/ws` path

## Deployment Steps

### 1. Prepare Environment Variables

Create a `.env.yaml` file for GCP deployment:

```yaml
REDIS_HOST: localhost
REDIS_PORT: 6379
REDIS_DB: 0
TELEGRAM_BOT_TOKEN: your_bot_token_here
TELEGRAM_OPERATOR_CHAT_ID: your_chat_id_here
GCP_CREDENTIALS_PATH: /app/gcp_key.json
GEMINI_API_KEY: your_gemini_api_key_here
SPEECH_LANGUAGE_CODE: ml-IN
SPEECH_VOICE_NAME: ml-IN-Standard-A
SPEECH_SAMPLE_RATE: 16000
MAX_PHONE_LENGTH: 10
CALL_TIMEOUT_SECONDS: 300
API_HOST: 0.0.0.0
PORT: 8080
LOG_LEVEL: INFO
```

### 2. Deploy to GCP

Use the provided deployment script:

```bash
./deploy.sh
```

This will:
- Build a Docker image
- Deploy to Google Cloud Run
- Configure the service with the environment variables

### 3. Update Exotel Configuration

Update your Exotel IVR configuration to point to the passthru endpoint:

```
https://your-gcp-service-url/exotel/passthru
```

### 4. Update WebSocket Clients

Update any WebSocket clients to use the new WebSocket URL format:

```
ws://your-gcp-service-url/ws
```

## Testing the Deployment

### Test HTTP Endpoints

```bash
# Test the health endpoint
curl https://your-gcp-service-url/health

# Test the root endpoint
curl https://your-gcp-service-url/
```

### Test Exotel Passthru

```bash
# Simulate an Exotel passthru request
curl "https://your-gcp-service-url/exotel/passthru?From=9876543210&CallSid=TEST-CALL-123&Digits=2"
```

### Test WebSocket Connection

Use a WebSocket client like wscat:

```bash
# Install wscat
npm install -g wscat

# Connect to the WebSocket endpoint
wscat -c wss://your-gcp-service-url/ws
```

## Troubleshooting

### Check Logs

View the logs in Google Cloud Console:

1. Go to Cloud Run
2. Select your service
3. Click on "Logs"

### Common Issues

1. **WebSocket Connection Failures**: Make sure your client is using the `/ws` path
2. **Telegram Bot Errors**: Check that your Telegram bot token and chat ID are correct
3. **Redis Connection Errors**: Redis runs in the same container, so check if the container is healthy

## Security Considerations

1. The Exotel passthru endpoint is publicly accessible without authentication
2. Consider adding API key authentication for production use
3. Use HTTPS for all connections

## Monitoring

Monitor your deployment using:

1. Google Cloud Monitoring
2. Cloud Run metrics
3. Application logs

## Scaling

The service is configured to scale automatically based on load. You can adjust the scaling parameters in the Cloud Run settings. 