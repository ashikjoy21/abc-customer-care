# PowerShell deployment script for Google Cloud Run

# Configuration
$ProjectId = (gcloud config get-value project)
$ServiceName = "abc-angamaly-voicebot"
$Region = "asia-south1"
$ImageName = "gcr.io/$ProjectId/$ServiceName"

# Print configuration
Write-Host "Deploying to Google Cloud Run:" -ForegroundColor Green
Write-Host "- Project ID: $ProjectId"
Write-Host "- Service Name: $ServiceName"
Write-Host "- Region: $Region"
Write-Host "- Image: $ImageName"
Write-Host ""

# Check if .env file exists
if (-not (Test-Path -Path ".env")) {
    Write-Host "Error: .env file not found. Please create it before deploying." -ForegroundColor Red
    exit 1
}

# Check if .env.yaml file exists
if (-not (Test-Path -Path ".env.yaml")) {
    Write-Host "Error: .env.yaml file not found. Please create it before deploying." -ForegroundColor Red
    exit 1
}

# Build the Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag $ImageName

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --image $ImageName `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 3600 `
    --env-vars-file .env.yaml

Write-Host ""
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "Your service will be available at the URL shown above." 