#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
import argparse
import websockets
from exotel_bot_enhanced import ExotelBotEnhanced

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs", "bot.log"), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

async def main(host: str = "localhost", port: int = 8765):
    """Start the WebSocket server and handle connections"""
    try:
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        async def handler(websocket, path):
            """Handle WebSocket connections"""
            bot = ExotelBotEnhanced()
            await bot.handle(websocket)
        
        # Create a health check endpoint
        async def health_handler(websocket, path):
            await websocket.send('{"status": "ok"}')
        
        # Create a router for different paths
        async def router(websocket, path):
            if path == "/health":
                await health_handler(websocket, path)
            else:
                await handler(websocket, path)
        
        server = await websockets.serve(router, host, port)
        logger.info(f"Server started successfully on {host}:{port}")
        
        # Keep the server running
        await asyncio.Future()
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Exotel Bot with Structured Troubleshooting")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the WebSocket server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8765)), help="Port to bind the WebSocket server")
    
    args = parser.parse_args()
    
    # Print startup banner
    print("\n" + "=" * 80)
    print(" " * 20 + "Enhanced Exotel Bot with Structured Troubleshooting")
    print("=" * 80)
    print(f"Starting server on {args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 80 + "\n")
    
    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)