#!/usr/bin/env python3
"""
Debug script to check environment variables and JWT decoding
"""

import os
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Environment Variable Debug ===")

# Check SUPABASE_KEY
supabase_key = os.getenv("SUPABASE_KEY")
print(f"SUPABASE_KEY exists: {supabase_key is not None}")
print(f"SUPABASE_KEY length: {len(supabase_key) if supabase_key else 0}")
print(f"SUPABASE_KEY (first 50 chars): {supabase_key[:50] if supabase_key else 'None'}")

# Check SUPABASE_URL
supabase_url = os.getenv("SUPABASE_URL")
print(f"SUPABASE_URL: {supabase_url}")

# Decode JWT
if supabase_key:
    try:
        decoded = jwt.decode(supabase_key, options={"verify_signature": False})
        print(f"JWT decoded successfully")
        print(f"JWT role: {decoded.get('role', 'unknown')}")
        print(f"JWT issuer: {decoded.get('iss', 'unknown')}")
        print(f"JWT ref: {decoded.get('ref', 'unknown')}")
        print(f"JWT exp: {decoded.get('exp', 'unknown')}")
        
        # Check if it's actually a service role key
        if decoded.get('role') == 'service_role':
            print("✅ This IS a service role key!")
        elif decoded.get('role') == 'anon':
            print("❌ This is an anon key, not a service role key")
        else:
            print(f"⚠️ Unknown role: {decoded.get('role')}")
            
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
else:
    print("❌ SUPABASE_KEY is not set")

print("\n=== All Environment Variables ===")
for key, value in os.environ.items():
    if 'SUPABASE' in key:
        if 'KEY' in key:
            print(f"{key}: {value[:20]}..." if value else f"{key}: None")
        else:
            print(f"{key}: {value}") 