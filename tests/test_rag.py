#!/usr/bin/env python
"""Test script for RAG system"""

from data.knowledge_base import get_troubleshooting_response

def test_with_dict():
    """Test with dictionary customer info"""
    print("\nTest with dictionary customer info:")
    customer_info = {"name": "Rajesh", "device_type": "fiber_modem"}
    response = get_troubleshooting_response('എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു', customer_info)
    print(response['response'][:100] + "...")  # Print first 100 chars

def test_with_object():
    """Test with object customer info"""
    print("\nTest with object customer info:")
    
    class CallMemory:
        def __init__(self):
            self.name = "Test User"
        
        def __str__(self):
            return self.name
    
    call_memory = CallMemory()
    response = get_troubleshooting_response('എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു', call_memory)
    print(response['response'][:100] + "...")  # Print first 100 chars

def test_with_none():
    """Test with None customer info"""
    print("\nTest with None customer info:")
    response = get_troubleshooting_response('എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു', None)
    print(response['response'][:100] + "...")  # Print first 100 chars

if __name__ == "__main__":
    print("=== RAG SYSTEM TEST ===")
    test_with_dict()
    test_with_object()
    test_with_none()
    print("\nAll tests completed.") 