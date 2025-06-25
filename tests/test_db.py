"""Test script to verify customer database loading"""

from db import CustomerDatabaseManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Test customer database loading"""
    print("Testing customer database loading...")
    
    # Create database manager
    db = CustomerDatabaseManager()
    
    # Print customer count
    print(f"Loaded {db.get_customer_count()} customers")
    
    # Print first 5 customers
    print("\nFirst 5 customers:")
    for i, customer in enumerate(db.customers[:5]):
        print(f"{i+1}. {customer.get('Customer Name')} - {customer.get('Mobile number')} - {customer.get('Current Plan')}")
    
    # Test phone lookup
    test_phone = "9946787718"  # Benny Sebastian's number from the data
    print(f"\nLooking up customer with phone: {test_phone}")
    customer = db.get_customer_by_phone(test_phone)
    if customer:
        print(f"Found: {customer.get('Customer Name')} - {customer.get('Address')}")
    else:
        print(f"No customer found with phone: {test_phone}")
    
    # Print active customers count
    active_customers = db.get_active_customers()
    print(f"\nActive customers: {len(active_customers)}")
    
if __name__ == "__main__":
    main() 