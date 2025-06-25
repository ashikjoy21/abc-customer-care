#!/usr/bin/env python
"""Test script for silence detection in call_flow.py"""

import asyncio
from call_flow import ExotelBot

async def test_on_transcription():
    """Test the on_transcription method with various inputs"""
    bot = ExotelBot()
    
    # Test cases
    test_cases = [
        {"text": "", "description": "Empty string", "expected": True},
        {"text": "a", "description": "Single character", "expected": True},
        {"text": "സെക്സ്", "description": "Problematic word alone", "expected": True},
        {"text": "ഹലോ സെക്സ്", "description": "Short phrase with problematic word", "expected": True},
        {"text": "എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു", "description": "Normal text", "expected": False}
    ]
    
    # Run tests
    for case in test_cases:
        result = bot._is_silence(case["text"])
        status = "✅ PASS" if result == case["expected"] else "❌ FAIL"
        print(f"\nTest: {case['description']}")
        print(f"  Input: '{case['text']}'")
        print(f"  Result: {result}")
        print(f"  Expected: {case['expected']}")
        print(f"  Status: {status}")
    
    # Test on_transcription with a normal query
    print("\nTesting on_transcription with normal query...")
    try:
        # This shouldn't raise any exceptions
        await bot.on_transcription("എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു")
        print("  ✅ on_transcription executed without errors")
    except Exception as e:
        print(f"  ❌ Error in on_transcription: {e}")

if __name__ == "__main__":
    print("=== SILENCE DETECTION TEST ===")
    asyncio.run(test_on_transcription()) 