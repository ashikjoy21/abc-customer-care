#!/usr/bin/env python
"""Test script for conversational responses in call_flow.py"""

import asyncio
from call_flow import ExotelBot, CallMemory, CallStatus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_conversational_responses():
    """Test the conversational nature of responses"""
    bot = ExotelBot()
    
    # Set up a test call environment
    bot.call_id = "test_call_123"
    bot.call_active = True
    bot.call_memory = CallMemory(call_id=bot.call_id)
    bot.call_memory.status = CallStatus.ACTIVE
    bot.call_memory.customer_name = "Rajesh"
    bot.call_memory.device_type = "fiber_modem"
    
    # Test queries in Malayalam
    test_queries = [
        "എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു",  # Red light on modem
        "ഇന്റർനെറ്റ് വളരെ സ്ലോ ആണ്",  # Internet is very slow
        "എന്റെ വൈഫൈ പാസ്‌വേഡ് മാറ്റണം",  # Need to change WiFi password
    ]
    
    print("\n=== CONVERSATIONAL RESPONSE TEST ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 50)
        
        # Process the query
        try:
            # Call the on_transcription method
            await bot.on_transcription(query)
            
            # Get the last response from conversation history
            if bot.conversation_history and len(bot.conversation_history) > 0:
                last_response = bot.conversation_history[-1].get("bot", "")
                print(f"Response: {last_response}")
                
                # Check for conversational elements
                conversational_markers = [
                    "ചിന്തിക്കേണ്ട", "ഒന്ന് നോക്കട്ടെ", "മനസ്സിലായി", "സഹായിക്കാം",
                    "Rajesh", "രാജേഷ്", # Customer name usage
                    "?", # Questions
                ]
                
                has_conversational_elements = any(marker in last_response for marker in conversational_markers)
                print(f"\nContains conversational elements: {'✅ Yes' if has_conversational_elements else '❌ No'}")
                
                # Check length - not too short, not too long
                good_length = 50 < len(last_response) < 500
                print(f"Good response length: {'✅ Yes' if good_length else '❌ No'}")
                
            else:
                print("❌ No response generated")
                
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        # Add a small delay between tests
        await asyncio.sleep(1)
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_conversational_responses()) 