import os
import logging
import jwt
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages Supabase operations for the customer care system"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with proper error handling"""
        try:
            if not SUPABASE_URL:
                logger.error("❌ Supabase URL not configured")
                return
                
            # Check which key we're using
            if not SUPABASE_KEY:
                logger.error("❌ SUPABASE_KEY not configured - this should be the service role key")
                return
                
            # Log key info for debugging (without exposing the actual key)
            key_preview = SUPABASE_KEY[:10] + "..." if SUPABASE_KEY else "None"
            logger.info(f"Using Supabase key: {key_preview}")
            
            # Check if we're using the service role key
            try:
                # Decode the JWT to check the role
                decoded = jwt.decode(SUPABASE_KEY, options={"verify_signature": False})
                role = decoded.get('role', 'unknown')
                logger.info(f"JWT role: {role}")
                
                if role == 'anon':
                    logger.warning("⚠️ You're using the ANON key! Please use the SERVICE ROLE key for full privileges.")
                    logger.warning("⚠️ Go to Supabase Dashboard → Settings → API → Copy Service Role Key")
                elif role == 'service_role':
                    logger.info("✅ Using service role key - this is correct!")
                else:
                    logger.warning(f"⚠️ Unknown role in JWT: {role}")
                # Do not return or block initialization, just log
            except Exception as jwt_error:
                logger.warning(f"⚠️ Could not decode JWT: {jwt_error}")
            
            # Use the service role key for admin access to bypass RLS
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Test the connection with a simple query
            try:
                # Test with a simple query to verify permissions
                response = self.client.table('escalations').select('id').limit(1).execute()
                logger.info("✅ Supabase client initialized successfully with admin access")
            except Exception as test_error:
                logger.warning(f"⚠️ Supabase connection test failed: {test_error}")
                # Still initialize the client, but log the warning
                logger.info("✅ Supabase client initialized (connection test failed)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self.client = None
    
    def check_connection(self) -> bool:
        """Check Supabase connection and health"""
        try:
            if not self.client:
                return False
                
            # Test connection by making a simple query
            response = self.client.table('incidents').select('id').limit(1).execute()
            logger.info("✅ Supabase connected and healthy")
            return True
            
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    def create_incident(self, incident_type: str, location: str, zones: str, services: str, areas: str = "") -> Optional[str]:
        """Create incident entry in Supabase"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return None
                
            incident_data = {
                "type": incident_type.lower(),
                "location": location.strip(),
                "status": "active",
                "affected_zones": zones,
                "affected_regions": location,
                "affected_areas": areas,
                "affected_services": services,
                "message_ml": f"{location} പ്രദേശത്ത് {incident_type.replace('_', ' ').title()} സംഭവിച്ചിട്ടുണ്ട്",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('incidents').insert(incident_data).execute()
            
            if response.data:
                incident_id = response.data[0]['id']
                logger.info(f"Created incident: {incident_id}")
                return incident_id
            else:
                logger.error("Failed to create incident: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            return None
    
    def get_active_incidents(self) -> List[Dict[str, Any]]:
        """Get all active incidents from Supabase"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return []
                
            response = self.client.table('incidents').select('*').eq('status', 'active').execute()
            
            active_incidents = []
            for incident in response.data:
                # Generate simple ID if not exists
                if "simple_id" not in incident:
                    simple_id = self._generate_incident_id(
                        incident.get("type", "unknown"),
                        incident.get("location", "unknown")
                    )
                    # Update the incident with simple_id
                    self.client.table('incidents').update({"simple_id": simple_id}).eq('id', incident['id']).execute()
                    incident["simple_id"] = simple_id
                else:
                    incident["simple_id"] = incident["simple_id"]
                
                active_incidents.append(incident)
            
            return active_incidents
            
        except Exception as e:
            logger.error(f"Error getting active incidents: {e}")
            return []
    
    def resolve_incident(self, incident_id: str) -> bool:
        """Resolve an incident by updating its status"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return False
                
            update_data = {
                "status": "resolved",
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('incidents').update(update_data).eq('id', incident_id).execute()
            
            if response.data:
                logger.info(f"Incident {incident_id} resolved successfully")
                return True
            else:
                logger.error(f"Failed to resolve incident {incident_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error resolving incident: {e}")
            return False
    
    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident details by ID"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return None
                
            response = self.client.table('incidents').select('*').eq('id', incident_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                logger.warning(f"No incident found with ID: {incident_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting incident: {e}")
            return None
    
    def update_incident(self, incident_id: str, update_data: Dict[str, Any]) -> bool:
        """Update incident with new data"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return False
                
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            response = self.client.table('incidents').update(update_data).eq('id', incident_id).execute()
            
            if response.data:
                logger.info(f"Incident {incident_id} updated successfully")
                return True
            else:
                logger.error(f"Failed to update incident {incident_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating incident: {e}")
            return False
    
    def create_escalation(
        self,
        issue_type: str,
        description: str,
        priority: str = "medium",
        customer_id: Optional[str] = None,
        escalated_by: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> Optional[str]:
        """Create escalation entry in Supabase"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return None
            
            # Validate priority
            valid_priorities = ["low", "medium", "high", "critical"]
            if priority not in valid_priorities:
                logger.warning(f"Invalid priority '{priority}', using 'medium'")
                priority = "medium"
            
            escalation_data = {
                "id": str(uuid.uuid4()),
                "issue_type": issue_type,
                "description": description,
                "priority": priority,
                "status": "open",
                "escalated_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                # Nullable fields
                "customer_id": customer_id if customer_id else None,
                "escalated_by": escalated_by if escalated_by else None,
                "assigned_to": assigned_to if assigned_to else None,
                "resolved_at": None,
                "resolution_notes": None
            }
            
            # Log the escalation data being sent
            logger.info(f"Creating escalation with data: {escalation_data}")
            
            response = self.client.table('escalations').insert(escalation_data).execute()
            
            if response.data:
                escalation_id = response.data[0]['id']
                logger.info(f"✅ Created escalation: {escalation_id} (Priority: {priority})")
                return escalation_id
            else:
                logger.error("❌ Failed to create escalation: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating escalation: {e}")
            
            # Check if it's an RLS policy issue
            if "row-level security policy" in str(e).lower():
                logger.error("❌ RLS Policy Error: The service role key may not have proper permissions")
                logger.error("❌ Please check Supabase RLS policies for the 'escalations' table")
                logger.error("❌ Ensure the service role has INSERT permissions")
            
            return None
    
    def get_open_escalations(self) -> List[Dict[str, Any]]:
        """Get all open escalations from Supabase"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return []
                
            response = self.client.table('escalations').select('*').in_('status', ['open', 'in_progress']).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting open escalations: {e}")
            return []
    
    def get_escalation_by_id(self, escalation_id: str) -> Optional[Dict[str, Any]]:
        """Get escalation details by ID"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return None
                
            response = self.client.table('escalations').select('*').eq('id', escalation_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                logger.warning(f"No escalation found with ID: {escalation_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting escalation: {e}")
            return None
    
    def update_escalation(self, escalation_id: str, update_data: Dict[str, Any]) -> bool:
        """Update escalation with new data"""
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return False
            
            # Validate status if provided
            if "status" in update_data:
                valid_statuses = ["open", "in_progress", "resolved", "closed"]
                if update_data["status"] not in valid_statuses:
                    logger.error(f"Invalid status: {update_data['status']}")
                    return False
            
            # Validate priority if provided
            if "priority" in update_data:
                valid_priorities = ["low", "medium", "high", "critical"]
                if update_data["priority"] not in valid_priorities:
                    logger.error(f"Invalid priority: {update_data['priority']}")
                    return False
            
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Add resolved_at timestamp if status is being set to resolved
            if update_data.get("status") == "resolved" and "resolved_at" not in update_data:
                update_data["resolved_at"] = datetime.now(timezone.utc).isoformat()
            
            response = self.client.table('escalations').update(update_data).eq('id', escalation_id).execute()
            
            if response.data:
                logger.info(f"Escalation {escalation_id} updated successfully")
                return True
            else:
                logger.error(f"Failed to update escalation {escalation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating escalation: {e}")
            return False
    
    def resolve_escalation(self, escalation_id: str, resolution_notes: Optional[str] = None) -> bool:
        """Resolve an escalation by updating its status"""
        try:
            update_data = {
                "status": "resolved",
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if resolution_notes:
                update_data["resolution_notes"] = resolution_notes
            
            return self.update_escalation(escalation_id, update_data)
                
        except Exception as e:
            logger.error(f"Error resolving escalation: {e}")
            return False
    
    def _generate_incident_id(self, incident_type: str, location: str) -> str:
        """Generate a simple incident ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
        type_prefix = incident_type[:3].upper()
        location_prefix = location[:3].upper()
        return f"INC-{type_prefix}-{location_prefix}-{timestamp}"
    
    def close(self):
        """Close Supabase connection"""
        # Supabase client doesn't need explicit closing, but we can clean up
        self.client = None
        logger.info("Supabase connection closed")
    
    def test_escalations_permissions(self) -> bool:
        """Test if we have proper permissions to insert into escalations table"""
        try:
            if not self.client:
                logger.error("❌ Supabase client not initialized")
                return False
                
            # Try to insert a test record
            test_data = {
                "issue_type": "test_issue",
                "description": "Test escalation for permission verification",
                "priority": "low",
                "status": "open",
                "escalated_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info("Testing escalations table permissions...")
            response = self.client.table('escalations').insert(test_data).execute()
            
            if response.data:
                test_id = response.data[0]['id']
                logger.info(f"✅ Successfully created test escalation: {test_id}")
                
                # Clean up the test record
                try:
                    self.client.table('escalations').delete().eq('id', test_id).execute()
                    logger.info(f"✅ Cleaned up test escalation: {test_id}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Could not clean up test escalation: {cleanup_error}")
                
                return True
            else:
                logger.error("❌ Failed to create test escalation: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing escalations permissions: {e}")
            
            # Check if it's an RLS policy issue
            if "row-level security policy" in str(e).lower():
                logger.error("❌ RLS Policy Error: The service role key does not have INSERT permissions")
                logger.error("❌ Please check Supabase RLS policies for the 'escalations' table")
                logger.error("❌ Ensure the service role has INSERT permissions or disable RLS for this table")
            
            return False
    
    def test_authentication(self) -> bool:
        """Test Supabase authentication and verify the key being used"""
        try:
            if not self.client:
                logger.error("❌ Supabase client not initialized")
                return False
                
            # Test authentication by making a simple query
            logger.info("Testing Supabase authentication...")
            
            # Try to access the auth schema to verify we have proper permissions
            try:
                # This will test if we can access the database at all
                response = self.client.table('escalations').select('count').execute()
                logger.info("✅ Authentication successful - can read from escalations table")
                return True
            except Exception as auth_error:
                logger.error(f"❌ Authentication failed: {auth_error}")
                
                # Check if it's a key issue
                if "401" in str(auth_error) or "unauthorized" in str(auth_error).lower():
                    logger.error("❌ 401 Unauthorized - This suggests the key is invalid or doesn't have proper permissions")
                    logger.error("❌ Please check:")
                    logger.error("   - You're using the SERVICE ROLE key (not the anon key)")
                    logger.error("   - The key is correct and not expired")
                    logger.error("   - The key has the necessary permissions")
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing authentication: {e}")
            return False

# Global Supabase manager instance
supabase_manager = SupabaseManager()

def check_supabase() -> bool:
    """Check Supabase connection and health
    
    Returns:
        bool: True if Supabase is healthy, False otherwise
    """
    return supabase_manager.check_connection()

def create_incident_entry(incident_type: str, location: str, zones: str, services: str, areas: str = "") -> Optional[str]:
    """Create incident entry in Supabase"""
    return supabase_manager.create_incident(incident_type, location, zones, services, areas)

def create_escalation_entry(
    issue_type: str,
    description: str,
    priority: str = "medium",
    customer_id: Optional[str] = None,
    escalated_by: Optional[str] = None,
    assigned_to: Optional[str] = None
) -> Optional[str]:
    """Create escalation entry in Supabase"""
    return supabase_manager.create_escalation(
        issue_type, description, priority, customer_id, escalated_by, assigned_to
    ) 