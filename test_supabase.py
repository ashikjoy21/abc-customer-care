#!/usr/bin/env python3
"""
Test script to verify Supabase connection and permissions for escalations table
"""

import asyncio
import logging
from supabase_client import SupabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_supabase():
    """Test Supabase connection and permissions"""
    try:
        logger.info("🔍 Testing Supabase connection and permissions...")
        
        # Initialize Supabase manager
        supabase_manager = SupabaseManager()
        
        # Test authentication first
        auth_ok = supabase_manager.test_authentication()
        if not auth_ok:
            logger.error("❌ Supabase authentication failed")
            return False
        
        # Test basic connection
        connection_ok = supabase_manager.check_connection()
        if not connection_ok:
            logger.error("❌ Supabase connection failed")
            return False
        
        # Test escalations table permissions
        permissions_ok = supabase_manager.test_escalations_permissions()
        if not permissions_ok:
            logger.error("❌ Escalations table permissions test failed")
            return False
        
        logger.info("✅ All Supabase tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during Supabase testing: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_supabase()) 