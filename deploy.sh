#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="abc-angamaly-voicebot"
REGION="asia-south1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Print configuration
echo "Deploying to Google Cloud Run:"
echo "- Project ID: $PROJECT_ID"
echo "- Service Name: $SERVICE_NAME"
echo "- Region: $REGION"
echo "- Image: $IMAGE_NAME"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found. Please create it before deploying."
  exit 1
fi

# Build the Docker image
echo "Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --env-vars-file .env.yaml

echo ""
echo "Deployment completed!"
echo "Your service will be available at the URL shown above." 