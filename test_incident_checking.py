#!/usr/bin/env python3
"""
Test script to verify incident checking functionality
"""

import asyncio
import logging
from supabase_client import SupabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_incident_checking():
    """Test incident checking functionality"""
    try:
        logger.info("🔍 Testing incident checking functionality...")
        
        # Initialize Supabase manager
        supabase_manager = SupabaseManager()
        
        # Test 1: Check for incidents with WiFi issue
        logger.info("\n--- Test 1: WiFi Issue ---")
        wifi_incidents = supabase_manager.check_relevant_incidents(
            user_query="എന്റെ വൈഫൈ കണക്ഷൻ വരുന്നില്ല",
            customer_area="Kochi",
            issue_type="wifi_issue"
        )
        
        logger.info(f"Found {len(wifi_incidents)} WiFi-related incidents")
        for incident in wifi_incidents:
            logger.info(f"  - {incident.get('issue_type')} in {incident.get('area')} (score: {incident.get('relevance_score')})")
        
        # Test 2: Check for incidents with internet issue
        logger.info("\n--- Test 2: Internet Issue ---")
        internet_incidents = supabase_manager.check_relevant_incidents(
            user_query="ഇന്റർനെറ്റ് വരുന്നില്ല",
            customer_area="Mannapuram",
            issue_type="internet_down"
        )
        
        logger.info(f"Found {len(internet_incidents)} internet-related incidents")
        for incident in internet_incidents:
            logger.info(f"  - {incident.get('issue_type')} in {incident.get('area')} (score: {incident.get('relevance_score')})")
        
        # Test 3: Check for incidents with speed issue
        logger.info("\n--- Test 3: Speed Issue ---")
        speed_incidents = supabase_manager.check_relevant_incidents(
            user_query="വേഗത വളരെ സ്ലോ ആണ്",
            customer_area="Angamaly",
            issue_type="speed_issue"
        )
        
        logger.info(f"Found {len(speed_incidents)} speed-related incidents")
        for incident in speed_incidents:
            logger.info(f"  - {incident.get('issue_type')} in {incident.get('area')} (score: {incident.get('relevance_score')})")
        
        # Test 4: Generate customer-friendly summaries
        logger.info("\n--- Test 4: Customer Summaries ---")
        
        all_incidents = wifi_incidents + internet_incidents + speed_incidents
        if all_incidents:
            summary = supabase_manager.get_incident_summary_for_customer(all_incidents)
            logger.info(f"Customer summary: {summary}")
        else:
            logger.info("No incidents found to generate summary")
        
        # Test 5: Test with no area specified
        logger.info("\n--- Test 5: No Area Specified ---")
        no_area_incidents = supabase_manager.check_relevant_incidents(
            user_query="എന്റെ നെറ്റ് പ്രശ്നം",
            customer_area=None,
            issue_type="internet_down"
        )
        
        logger.info(f"Found {len(no_area_incidents)} incidents without area specification")
        
        logger.info("\n✅ Incident checking tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during incident checking tests: {e}")
        return False

async def test_incident_creation():
    """Test creating test incidents"""
    try:
        logger.info("\n🔍 Testing incident creation...")
        
        supabase_manager = SupabaseManager()
        
        # Create a test incident
        test_incident_id = supabase_manager.create_incident(
            incident_type="wifi_issue",
            location="Test Area",
            zones="Test Zone",
            services="Internet, WiFi",
            areas="Test Area"
        )
        
        if test_incident_id:
            logger.info(f"✅ Created test incident: {test_incident_id}")
            
            # Clean up - resolve the test incident
            if supabase_manager.resolve_incident(test_incident_id):
                logger.info(f"✅ Resolved test incident: {test_incident_id}")
            else:
                logger.warning(f"⚠️ Could not resolve test incident: {test_incident_id}")
        else:
            logger.error("❌ Failed to create test incident")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during incident creation test: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting incident checking tests...")
    
    # Test incident creation first
    creation_ok = await test_incident_creation()
    
    # Test incident checking
    checking_ok = await test_incident_checking()
    
    if creation_ok and checking_ok:
        logger.info("🎉 All tests passed!")
    else:
        logger.error("❌ Some tests failed!")
    
    return creation_ok and checking_ok

if __name__ == "__main__":
    asyncio.run(main()) 