#!/usr/bin/env python
"""Test script for natural conversation flow in call_flow.py"""

import asyncio
from call_flow import ExotelBot, CallMemory, CallStatus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_conversation_flow():
    """Test a natural conversation flow with multiple exchanges"""
    bot = ExotelBot()
    
    # Set up a test call environment
    bot.call_id = "test_call_flow_123"
    bot.call_active = True
    bot.call_memory = CallMemory(call_id=bot.call_id)
    bot.call_memory.status = CallStatus.ACTIVE
    bot.call_memory.customer_name = "Rajesh"
    bot.call_memory.device_type = "fiber_modem"
    
    # Define a conversation flow - a series of user messages that build on each other
    conversation = [
        # Initial problem statement
        "എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു",  # Red light on modem
        
        # Response to agent's question about what they're seeing
        "അതെ, റെഡ് ലൈറ്റ് കാണുന്നുണ്ട്. മറ്റ് ലൈറ്റുകൾ ഒന്നും കത്തുന്നില്ല.",  # Yes, red light is showing. No other lights are on.
        
        # Response to troubleshooting suggestion
        "ഞാൻ മോഡം റീസ്റ്റാർട്ട് ചെയ്തു, പക്ഷേ ഇപ്പോഴും റെഡ് ലൈറ്റ് കാണുന്നു",  # I restarted the modem, but still see the red light
        
        # Response to further troubleshooting
        "കേബിൾ കണക്ഷൻ ശരിയാണ്, പക്ഷേ ഇപ്പോഴും പ്രശ്നം നിലനിൽക്കുന്നു",  # Cable connection is fine, but problem persists
        
        # Final response to technician visit suggestion
        "ശരി, ടെക്നീഷ്യനെ അയക്കാമോ? എപ്പോഴാണ് അവർ വരിക?"  # Okay, can you send a technician? When will they come?
    ]
    
    print("\n=== CONVERSATION FLOW TEST ===\n")
    print("Testing a natural conversation flow with multiple exchanges\n")
    
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
                
                # Check for conversational elements
                conversational_markers = [
                    "ചിന്തിക്കേണ്ട", "ഒന്ന് നോക്കട്ടെ", "മനസ്സിലായി", "സഹായിക്കാം",
                    "Rajesh", "രാജേഷ്", # Customer name usage
                    "?", # Questions
                ]
                
                has_conversational_elements = any(marker in last_response for marker in conversational_markers)
                print(f"- Contains conversational elements: {'✅ Yes' if has_conversational_elements else '❌ No'}")
                
                # Check length - not too short, not too long
                good_length = 50 < len(last_response) < 300
                print(f"- Good response length: {'✅ Yes' if good_length else '❌ No'}")
                
                # Check for context awareness (references to previous messages)
                context_aware = False
                if i > 1 and bot.conversation_history and len(bot.conversation_history) > 1:
                    # Look for words from previous exchanges
                    previous_exchanges = [entry["user"] for entry in bot.conversation_history[:-1]]
                    key_terms = ["റെഡ് ലൈറ്റ്", "മോഡം", "റീസ്റ്റാർട്ട്", "കേബിൾ"]
                    
                    # Check if response contains references to previous context
                    context_aware = any(term in last_response for term in key_terms)
                
                if i > 1:
                    print(f"- Context awareness: {'✅ Yes' if context_aware else '❌ No'}")
                
                # Check if response ends with a question (engagement)
                ends_with_question = "?" in last_response[-30:]
                print(f"- Ends with question: {'✅ Yes' if ends_with_question else '❌ No'}")
                
            else:
                print("❌ No response generated")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
        
        # Add a small delay between exchanges
        await asyncio.sleep(1)
    
    print("\nConversation flow test completed!")
    
    # Print the entire conversation history
    print("\n=== FULL CONVERSATION TRANSCRIPT ===\n")
    for i, exchange in enumerate(bot.conversation_history, 1):
        print(f"User: {exchange.get('user', '')}")
        print(f"Anjali: {exchange.get('bot', '')}")
        print()

if __name__ == "__main__":
    asyncio.run(test_conversation_flow()) 