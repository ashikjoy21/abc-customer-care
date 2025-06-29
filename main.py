import asyncio
import logging
from typing import Optional
from loguru import logger

from config import (
    LOG_LEVEL,
    LOG_FORMAT
)
from db import CustomerDatabaseManager
from call_flow import main as start_voicebot
from supabase_client import SupabaseManager

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
        self.supabase_manager = SupabaseManager()
        self.db: Optional[CustomerDatabaseManager] = None
        
    async def initialize(self):
        """Initialize all components"""
        try:
            # Check Supabase connection
            if not self.supabase_manager.check_connection():
                logger.error("❌ Failed to connect to Supabase")
                return False
            
            # Initialize database
            self.db = CustomerDatabaseManager()
            self.db.load_from_json()
            
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            return False
            
    async def shutdown(self):
        """Shutdown application components"""
        try:
            if self.supabase_manager:
                self.supabase_manager.close()
                
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