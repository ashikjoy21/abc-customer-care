import json
import logging
from typing import Dict, List, Optional, Any
from config import CUSTOMERS_JSON_PATH
from utils import logger

class CustomerDatabaseManager:
    """Manages customer database operations"""
    
    def __init__(self):
        self.customers: List[Dict[str, Any]] = []
        self.customer_by_phone: Dict[str, Dict[str, Any]] = {}
        self.load_from_json()  # Load data immediately
        
    def load_from_json(self) -> bool:
        """Load customer data from JSON file"""
        try:
            with open(CUSTOMERS_JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Convert list to dictionary with phone numbers as keys
            self.customers = []
            self.customer_by_phone = {}
            
            for customer in data:
                if 'Mobile number' in customer:
                    phone = customer['Mobile number']
                    # Handle None or empty values
                    if phone is None or phone == '':
                        continue
                        
                    try:
                        # Convert to string and clean
                        phone = str(phone).strip()
                        # Remove any decimal points and convert to string
                        if '.' in phone:
                            phone = str(int(float(phone)))
                        # Ensure it's a valid 10-digit number
                        if not phone.isdigit() or len(phone) != 10:
                            logger.warning(f"Skipping invalid phone number: {phone}")
                            continue
                            
                        # Store in both lists
                        self.customers.append(customer)
                        self.customer_by_phone[phone] = customer
                        
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping invalid phone number format: {phone}, error: {e}")
                        continue
            
            logger.info(f"Loaded {len(self.customers)} customers")
            return True
        except Exception as e:
            logger.error(f"Error loading customer database: {e}")
            return False
            
    def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get customer details by phone number"""
        try:
            # Clean and validate phone number
            phone = str(phone).strip()
            if not phone.isdigit() or len(phone) != 10:
                logger.error(f"Invalid phone number format: {phone}")
                return None
                
            # Direct dictionary lookup
            customer = self.customer_by_phone.get(phone)
            if customer:
                logger.info(f"Found customer with phone: {phone}")
                return customer
                
            logger.warning(f"No customer found with phone: {phone}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for customer: {e}")
            return None
        
    def get_customers_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get all customers in a region"""
        return [
            customer for customer in self.customers
            if customer.get('Region', '').lower() == region.lower()
        ]
        
    def get_customers_by_zone(self, zone: str) -> List[Dict[str, Any]]:
        """Get all customers in a zone"""
        return [
            customer for customer in self.customers
            if customer.get('Zone', '').lower() == zone.lower()
        ]
        
    def get_customers_by_area(self, area: str) -> List[Dict[str, Any]]:
        """Get all customers in an area"""
        return [
            customer for customer in self.customers
            if customer.get('Area', '').lower() == area.lower()
        ]
        
    def get_customers_by_service(self, service: str) -> List[Dict[str, Any]]:
        """Get all customers with a specific service"""
        return [
            customer for customer in self.customers
            if service.lower() in (customer.get('Current Plan', '') or '').lower()
        ]
        
    def get_customer_count(self) -> int:
        """Get total number of customers"""
        return len(self.customers)
        
    def get_active_customers(self) -> List[Dict[str, Any]]:
        """Get all active customers"""
        return [
            customer for customer in self.customers
            if customer.get('Status', '').lower() == 'active'
        ]
        
    def get_customer_services(self, phone: str) -> List[str]:
        """Get services for a customer"""
        customer = self.get_customer_by_phone(phone)
        if customer and 'Current Plan' in customer:
            # Return Current Plan as a service
            return [customer['Current Plan']] if customer['Current Plan'] else []
        return []
        
    def get_customer_plan(self, phone: str) -> Optional[str]:
        """Get plan details for a customer"""
        customer = self.get_customer_by_phone(phone)
        return customer.get('Current Plan') if customer else None 