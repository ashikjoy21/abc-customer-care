import os
import uvicorn
import asyncio
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", 8080))  # Use PORT env var for GCP compatibility

# Initialize FastAPI app
app = FastAPI(
    title="ABC Customer Care API",
    description="API for ABC Customer Care system with WebSocket support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"]  # Expose all headers
)

# Store active WebSocket connections
websocket_connections = {}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ABC Customer Care API",
        "endpoints": ["/health", "/exotel/passthru", "/ws"]
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = None
    try:
        logger.info(f"WebSocket connection attempt from {websocket.client.host}")
        await websocket.accept()
        connection_id = id(websocket)
        websocket_connections[connection_id] = websocket
        
        logger.info(f"WebSocket connection established: {connection_id} from {websocket.client.host}")
        
        # Forward the connection to the voicebot handler
        from call_flow import handle_client
        await handle_client(websocket)
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected normally: {connection_id}, code: {e.code}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        if connection_id and connection_id in websocket_connections:
            del websocket_connections[connection_id]
            logger.info(f"Removed connection {connection_id} from active connections")
        logger.info("WebSocket handler complete")

# Import and include the Exotel passthru router
from exotel_passthru import router as exotel_router
app.include_router(exotel_router, tags=["exotel"])

def start_api_server():
    """Start the FastAPI server."""
    try:
        websocket_url = os.getenv("WEBSOCKET_URL", f"ws://{API_HOST}:{API_PORT}/ws")
        logger.info(f"Starting API server on http://{API_HOST}:{API_PORT}")
        logger.info(f"WebSocket endpoint available at {websocket_url}")
        uvicorn.run(
            "api_server:app",
            host=API_HOST,
            port=API_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)

async def run_api_server():
    """Run the API server in a separate process."""
    # Create a subprocess for the API server
    import multiprocessing
    api_process = multiprocessing.Process(target=start_api_server)
    api_process.start()
    
    websocket_url = os.getenv("WEBSOCKET_URL", f"ws://{API_HOST}:{API_PORT}/ws")
    logger.info(f"API server started on http://{API_HOST}:{API_PORT}")
    logger.info(f"WebSocket endpoint available at {websocket_url}")
    
    try:
        # Keep the process running until the main process ends
        while api_process.is_alive():
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error monitoring API process: {e}")
    finally:
        # Ensure the process is terminated when the main process ends
        if api_process.is_alive():
            logger.info("Stopping API server...")
            api_process.terminate()
            api_process.join(timeout=5)
            if api_process.is_alive():
                logger.warning("API server did not terminate gracefully, forcing...")
                api_process.kill()
            logger.info("API server stopped")

if __name__ == "__main__":
    # Run the server directly when script is executed
    start_api_server() 