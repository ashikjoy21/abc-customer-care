import logging
from typing import Dict, List, Optional, Any
from supabase_client import SupabaseManager
from utils import logger

class CustomerDatabaseManager:
    """Manages customer database operations using Supabase"""
    def __init__(self):
        self.supabase = SupabaseManager()

    def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get customer details by phone number from Supabase"""
        try:
            phone = str(phone).strip()
            if not phone.isdigit() or len(phone) != 10:
                logger.error(f"Invalid phone number format: {phone}")
                return None
            if not self.supabase.client:
                logger.error("Supabase client not initialized")
                return None
            response = self.supabase.client.table('customers').select('*').eq('phone', phone).limit(1).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Found customer with phone: {phone}")
                return response.data[0]
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