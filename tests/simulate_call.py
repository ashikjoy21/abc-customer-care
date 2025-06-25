#!/usr/bin/env python3
"""
Script to simulate a customer call for testing purposes.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent))

from call_flow import ExotelBot

class CallSimulator:
    """Simulates a customer call for testing purposes."""
    
    def __init__(self, phone_number: str = None):
        """
        Initialize the call simulator.
        
        Args:
            phone_number: Optional phone number to use for the call.
        """
        self.phone_number = phone_number
        self.bot = ExotelBot()
        self.call_id = "sim_" + (phone_number or "unknown").replace("+", "")
        
    async def simulate_call(self):
        """Simulate a customer call with the bot."""
        logger.info(f"Starting simulated call with ID: {self.call_id}")
        
        # Initialize the bot for this call
        await self.bot.handle_message({
            "type": "start",
            "call_id": self.call_id,
            "data": {}
        })
        
        # If phone number is provided, simulate DTMF input
        if self.phone_number:
            logger.info(f"Simulating phone number input: {self.phone_number}")
            for digit in self.phone_number:
                await self.bot.handle_message({
                    "type": "dtmf",
                    "call_id": self.call_id,
                    "data": digit
                })
                await asyncio.sleep(0.5)
        
        # Simulate customer queries
        queries = [
            "എന്റെ ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല",  # My internet is not working
            "വൈഫൈ കണക്ഷൻ ഉണ്ടെങ്കിലും ഇന്റർനെറ്റ് ലഭിക്കുന്നില്ല",  # I have WiFi connection but no internet
            "എന്റെ റൂട്ടർ റീസ്റ്റാർട്ട് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല"  # I restarted my router but still no internet
        ]
        
        for query in queries:
            logger.info(f"Simulating customer query: {query}")
            await self.bot.handle_message({
                "type": "audio",
                "call_id": self.call_id,
                "data": {
                    "transcript": query,
                    "confidence": 0.95
                }
            })
            
            # Wait for response
            await asyncio.sleep(2)
        
        # End the call
        logger.info("Ending simulated call")
        await self.bot.handle_message({
            "type": "end",
            "call_id": self.call_id,
            "data": {}
        })
        
        logger.info("Call simulation completed")

async def main():
    parser = argparse.ArgumentParser(description="Simulate a customer call for testing purposes.")
    parser.add_argument("--phone", type=str, help="Phone number to use for the call")
    args = parser.parse_args()
    
    simulator = CallSimulator(phone_number=args.phone)
    await simulator.simulate_call()

if __name__ == "__main__":
    asyncio.run(main()) 