#!/usr/bin/env python
"""Test script for natural conversation flow with a real customer scenario"""

import asyncio
from call_flow import ExotelBot, CallMemory, CallStatus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_conversation():
    """Test a real conversation flow from logs"""
    bot = ExotelBot()
    
    # Set up a test call environment
    bot.call_id = "test_real_call_123"
    bot.call_active = True
    bot.call_memory = CallMemory(call_id=bot.call_id)
    bot.call_memory.status = CallStatus.ACTIVE
    bot.call_memory.customer_name = "Sreejith"
    bot.call_memory.device_type = "fiber_modem"
    
    # Define a conversation flow from real logs
    conversation = [
        # Initial problem statement
        "എൻറെ വീട്ടിൽ നെറ്റ് കിട്ടുന്നില്ല",  # Internet not working at my house
        
        # Response to agent's question
        "എന്ത് ചെയ്യാനാ",  # What should I do?
        
        # Confirming red light
        "റെഡ് ലൈറ്റ് കളയുന്നില്ല",  # Red light is on
        
        # Clarifying current status
        "റെഡ് ലൈറ്റ് കാണുന്നില്ല എല്ലാം പച്ച കളർ പച്ച ലൈറ്റ് തെളിയുന്ന",  # Red light is not showing, all lights are green
        
        # Simple response
        "ഇല്ല",  # No
        
        # Asking for clarification
        "ഇങ്ങനെ പരിശോധിക്കാൻ തോറ",  # How to check this?
        
        # Asking what they see
        "എന്ത് കാണുന്നു ഇവിടെ കാണുന്നു",  # What do you see here?
        
        # Confirming router status
        "റൗട്ടർ പച്ച ലൈറ്റ് കാണുന്നത്",  # Router shows green light
        
        # Problem with WiFi name
        "വൈഫ് യുടെ പേര് വേറെ കാണുന്ന",  # WiFi name is showing differently
        
        # Asking where to check
        "വൈഫ് യുടെ പേര് എവിടെ നോക്കണ്ടേ മനസ്സിലായില്ല",  # Where should I check the WiFi name? I don't understand
        
        # Agreeing to technician visit
        "വിട്ടോളൂ",  # Let it go/OK
        
        # Confirming time preference
        "രാവിലെ സൗകര്യം"  # Morning is convenient
    ]
    
    print("\n=== REAL CONVERSATION TEST ===\n")
    print("Testing a natural conversation flow based on real customer logs\n")
    
    for i, message in enumerate(conversation, 1):
        print(f"\nExchange {i}: User says: \"{message}\"")
        print("-" * 60)
        
        # Process the message
        try:
            # Call the on_transcription method
            await bot.on_transcription(message)
            
            # Get the last response from conversation history
            if bot.conversation_history and len(bot.conversation_history) > 0:
                last_response = bot.conversation_history[-1].get("bot", "")
                print(f"Anjali responds: \"{last_response}\"\n")
                
                # Analyze response quality
                print("Response analysis:")
                
                # Check for natural flow (not starting with customer name)
                starts_with_name = last_response.startswith("Sreejith") or last_response.startswith("ശ്രീജിത്ത്")
                print(f"- Avoids starting with name: {'❌ No' if starts_with_name else '✅ Yes'}")
                
                # Check length - not too short, not too long
                good_length = 30 < len(last_response) < 150
                print(f"- Good response length: {'✅ Yes' if good_length else '❌ No'}")
                
                # Check if it sounds natural (no repetitive patterns)
                repetitive_markers = [
                    "ചിന്തിക്കേണ്ട, ", "ഒന്ന് നോക്കട്ടെ, ", "മനസ്സിലായി, ", "വിഷമിക്കേണ്ട, ",
                    "തീർച്ചയായും", "ശരി"
                ]
                
                # Count how many repetitive markers are used
                repetitive_count = sum(1 for marker in repetitive_markers if marker in last_response)
                natural_sounding = repetitive_count <= 1
                print(f"- Natural sounding (avoids repetitive phrases): {'✅ Yes' if natural_sounding else '❌ No'}")
                
                # Check if response is direct and to the point
                direct_response = len(last_response) < 100
                print(f"- Direct and to the point: {'✅ Yes' if direct_response else '❌ No'}")
                
            else:
                print("❌ No response generated")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
        
        # Add a small delay between exchanges
        await asyncio.sleep(1)
    
    print("\nReal conversation test completed!")
    
    # Print the entire conversation history
    print("\n=== FULL CONVERSATION TRANSCRIPT ===\n")
    for i, exchange in enumerate(bot.conversation_history, 1):
        print(f"User: {exchange.get('user', '')}")
        print(f"Anjali: {exchange.get('bot', '')}")
        print()

if __name__ == "__main__":
    asyncio.run(test_real_conversation()) 