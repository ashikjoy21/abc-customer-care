import asyncio
import logging
from typing import Optional
import redis
from loguru import logger

from config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    LOG_LEVEL,
    LOG_FORMAT
)
from db import CustomerDatabaseManager
from telegram_notifier import TelegramBotManager
from call_flow import main as start_voicebot
from utils import check_redis

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level=LOG_LEVEL,
    format=LOG_FORMAT
)
logger.add(lambda msg: print(msg), level=LOG_LEVEL, format=LOG_FORMAT)

class Application:
    """Main application class"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.db: Optional[CustomerDatabaseManager] = None
        self.telegram_bot: Optional[TelegramBotManager] = None
        
    async def initialize(self):
        """Initialize application components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            
            # Check Redis connection
            if not check_redis(self.redis_client):
                raise Exception("Failed to connect to Redis")
                
            # Initialize database
            self.db = CustomerDatabaseManager()
            self.db.load_from_json()
            
            # Initialize Telegram bot
            self.telegram_bot = TelegramBotManager()
            await self.telegram_bot.start()
            
            logger.info("✅ Application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
            
    async def shutdown(self):
        """Shutdown application components"""
        try:
            if self.telegram_bot:
                await self.telegram_bot.stop()
                
            if self.redis_client:
                self.redis_client.close()
                
            logger.info("👋 Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    async def run(self):
        """Run the application"""
        try:
            await self.initialize()
            
            # Start voicebot server
            await start_voicebot()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            await self.shutdown()

async def main():
    """Application entry point"""
    app = Application()
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise 