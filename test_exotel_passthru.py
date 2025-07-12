#!/usr/bin/env python
"""
Test script for simulating Exotel passthru requests.
This script can be used to test the Exotel passthru endpoint without needing
an actual Exotel call.
"""
import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simulate_exotel_passthru(
    host: str, 
    port: int, 
    digits: str, 
    phone: str, 
    call_sid: str
):
    """Simulate an Exotel passthru request."""
    url = f"http://{host}:{port}/exotel/passthru"
    
    # Prepare query parameters as would be sent by Exotel
    params = {
        "From": phone,
        "CallSid": call_sid,
        "Digits": digits
    }
    
    # Send the request
    try:
        print(f"Sending request to {url} with params: {params}")
        response = requests.get(url, params=params)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test passed: Successfully sent passthru notification")
        else:
            print(f"❌ Test failed: Received status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error connecting to API server: {e}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Exotel passthru endpoint")
    
    parser.add_argument(
        "--host", 
        default=os.getenv("API_HOST", "localhost"),
        help="API server host"
    )
    
    parser.add_argument(
        "--port", 
        type=int,
        default=int(os.getenv("PORT", 8080)),
        help="API server port"
    )
    
    parser.add_argument(
        "--digits",
        choices=["2", "3", "1", "4"],
        default="2",
        help="IVR option selected (2 and 3 should trigger notifications)"
    )
    
    parser.add_argument(
        "--phone",
        default="9876543210",
        help="Caller phone number"
    )
    
    parser.add_argument(
        "--callsid",
        default="TEST-CALL-123",
        help="Call SID"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
        
    print(f"Testing Exotel passthru with IVR option {args.digits}...")
    simulate_exotel_passthru(
        host=args.host,
        port=args.port,
        digits=args.digits,
        phone=args.phone,
        call_sid=args.callsid
    ) 