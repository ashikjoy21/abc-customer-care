# Deployment to Google Cloud Run

This document outlines the steps to deploy the ABC Angamaly Voice Bot to Google Cloud Run.

## Prerequisites

1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Initialize Google Cloud SDK and authenticate:
   ```
   gcloud init
   gcloud auth login
   ```
3. Create or select a Google Cloud project:
   ```
   gcloud projects create [PROJECT_ID] --name="ABC Angamaly Bot"
   # OR
   gcloud config set project [EXISTING_PROJECT_ID]
   ```
4. Enable required APIs:
   ```
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com
   ```

## Deployment Steps

### 1. Set up Google Cloud credentials

If you're using Google Cloud services like Speech-to-Text or Text-to-Speech:

1. Create a service account with appropriate permissions
2. Download the JSON key file
3. Store the path in your `.env.yaml` file as `GCP_CREDENTIALS_PATH`

### 2. Configure environment variables

1. Edit the `.env.yaml` file with your configuration values
2. For sensitive values like API keys, consider using Secret Manager:
   ```
   gcloud secrets create TELEGRAM_BOT_TOKEN --data-file=/path/to/token.txt
   ```

### 3. Deploy to Google Cloud Run

#### Option 1: Using the deployment script

Run the deployment script:

```bash
# On Linux/macOS
chmod +x deploy.sh
./deploy.sh

# On Windows PowerShell
.\deploy.ps1
```

#### Option 2: Manual deployment

1. Build the Docker image:
   ```
   gcloud builds submit --tag gcr.io/[PROJECT_ID]/abc-angamaly-voicebot
   ```

2. Deploy to Cloud Run:
   ```
   gcloud run deploy abc-angamaly-voicebot \
     --image gcr.io/[PROJECT_ID]/abc-angamaly-voicebot \
     --platform managed \
     --region asia-south1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --timeout 3600 \
     --env-vars-file .env.yaml
   ```

## Accessing Your Deployed Service

After deployment, you'll receive a URL where your service is accessible. This URL will look something like:
```
https://abc-angamaly-voicebot-[random]-[region].run.app
```

The application runs both an HTTP server (on port 8080) and a WebSocket server (on port 8765):
- HTTP server: Used for health checks and basic status monitoring
- WebSocket server: Used for the main voice bot functionality

## Troubleshooting

1. Check logs in Google Cloud Console:
   - Go to Cloud Run > Select your service > Logs

2. If Redis connection issues occur:
   - Verify Redis is running in the container
   - Check if the REDIS_HOST is set to "localhost"

3. For other issues:
   - Check the application logs in Cloud Run console
   - You can also view logs using the command:
     ```
     gcloud logs read --limit=10 --service=abc-angamaly-voicebot
     ```

4. Region format issues:
   - Make sure you're using the correct region format (e.g., "asia-south1" not "asia-south1-c")
   - Cloud Run regions don't include the zone suffix (like "-c")

5. Container startup issues:
   - Cloud Run expects your container to listen on the port specified by the PORT environment variable
   - The container must start successfully within the timeout period (default is 4 minutes)
   - Our setup uses an HTTP server on port 8080 to handle health checks 