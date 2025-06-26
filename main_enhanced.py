#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
import signal
import argparse
import websockets
import psutil
import time
import traceback
from datetime import datetime
from exotel_bot_enhanced import ExotelBotEnhanced

# Configure logging with rotation
import logging.handlers

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure rotating file handler
log_file = os.path.join(log_dir, "bot.log")
file_handler = logging.handlers.RotatingFileHandler(
    log_file, 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,
    mode='a'
)

# Configure stdout handler
stdout_handler = logging.StreamHandler(sys.stdout)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[stdout_handler, file_handler]
)
logger = logging.getLogger(__name__)

# Global variables for tracking
active_connections = set()
server_start_time = datetime.now()
connection_attempts = 0
connection_successes = 0
connection_failures = 0
last_health_check = time.time()

# Track memory usage
def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    logger.info(f"Memory usage: {memory_mb:.2f} MB")
    
    # Force garbage collection if memory usage is too high
    if memory_mb > 1000:  # 1GB threshold
        logger.warning(f"High memory usage detected: {memory_mb:.2f} MB, forcing garbage collection")
        import gc
        gc.collect()

# Health check function
async def health_check():
    global last_health_check
    while True:
        try:
            current_time = time.time()
            uptime = datetime.now() - server_start_time
            
            # Log health metrics every 5 minutes
            if current_time - last_health_check >= 300:  # 5 minutes
                logger.info(f"Health check: Server uptime: {uptime}, "
                           f"Active connections: {len(active_connections)}, "
                           f"Connection attempts: {connection_attempts}, "
                           f"Successful: {connection_successes}, "
                           f"Failed: {connection_failures}")
                log_memory_usage()
                last_health_check = current_time
                
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            await asyncio.sleep(60)  # Continue checking even after error

async def handle_client(websocket, path):
    """Handle a single client connection with robust error handling"""
    global connection_successes, connection_failures
    
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"New connection from {client_id}")
    
    # Add to active connections
    active_connections.add(websocket)
    
    bot = None
    try:
        bot = ExotelBotEnhanced()
        connection_successes += 1
        await bot.handle(websocket)
        
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"WebSocket connection closed: {client_id}, code: {e.code}, reason: {e.reason}")
        
    except Exception as e:
        connection_failures += 1
        logger.error(f"Error handling client {client_id}: {e}")
        logger.error(traceback.format_exc())
        
    finally:
        # Clean up resources
        if bot and hasattr(bot, 'transcriber') and bot.transcriber:
            bot.transcriber.stop()
            
        if websocket in active_connections:
            active_connections.remove(websocket)
        
        logger.info(f"Connection closed: {client_id}, active connections: {len(active_connections)}")

async def main(host: str = "0.0.0.0", port: int = 8080):
    """Start the WebSocket server with reconnection logic"""
    global connection_attempts
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig)))
    
    # Start health check task
    health_check_task = asyncio.create_task(health_check())
    
    max_retries = 5
    retry_count = 0
    retry_delay = 5  # seconds
    
    while retry_count < max_retries:
        try:
            logger.info(f"Starting WebSocket server on {host}:{port}")
            
            # Create server with increased max_size for audio data
            server = await websockets.serve(
                handle_client, 
                host, 
                port,
                max_size=10 * 1024 * 1024,  # 10MB max message size
                ping_interval=30,           # Send ping every 30 seconds
                ping_timeout=10,            # Wait 10 seconds for pong response
                close_timeout=10            # Wait 10 seconds for close handshake
            )
            
            logger.info(f"🚀 Server started successfully on {host}:{port}")
            
            # Keep server running
            await asyncio.Future()
            
        except OSError as e:
            retry_count += 1
            logger.error(f"Failed to start server (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff for retry delay
                retry_delay = min(retry_delay * 2, 60)  # Cap at 60 seconds
            else:
                logger.critical(f"Failed to start server after {max_retries} attempts")
                return 1
        except Exception as e:
            logger.critical(f"Unexpected error starting server: {e}")
            logger.critical(traceback.format_exc())
            return 1

async def shutdown(sig):
    """Gracefully shut down the server"""
    logger.info(f"Received signal {sig.name}, shutting down...")
    
    # Close all active connections
    if active_connections:
        logger.info(f"Closing {len(active_connections)} active connections")
        close_tasks = [ws.close(code=1001, reason="Server shutting down") for ws in active_connections]
        await asyncio.gather(*close_tasks, return_exceptions=True)
    
    # Cancel all tasks
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("Shutdown complete")
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Exotel Bot with Structured Troubleshooting")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the WebSocket server")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind the WebSocket server")
    
    args = parser.parse_args()
    
    # Print startup banner
    print("\n" + "=" * 80)
    print(" " * 20 + "Enhanced Exotel Bot with Structured Troubleshooting")
    print(" " * 25 + "PRODUCTION MODE")
    print("=" * 80)
    print(f"Starting server on {args.host}:{args.port}")
    print("=" * 80 + "\n")
    
    try:
        exit_code = asyncio.run(main(args.host, args.port))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)