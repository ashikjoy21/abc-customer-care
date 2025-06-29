import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from supabase_client import supabase_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EscalationReason(Enum):
    """Reasons for escalating a call"""
    CUSTOMER_REQUEST = "customer_request"
    MULTIPLE_FAILURES = "multiple_failures"
    STEPS_EXHAUSTED = "steps_exhausted"
    TECHNICAL_COMPLEXITY = "technical_complexity"
    AREA_OUTAGE = "area_outage"
    ACCOUNT_ISSUE = "account_issue"
    HARDWARE_ISSUE = "hardware_issue"
    REPEATED_ISSUE = "repeated_issue"
    LOW_CONFIDENCE = "low_confidence"
    TIMEOUT = "timeout"
    ESCALATION_KEYWORD = "escalation_keyword"
    BUSINESS_CUSTOMER = "business_customer"
    VIP_CUSTOMER = "vip_customer"

@dataclass
class EscalationCriteria:
    """Criteria for escalation decision"""
    # Step-based criteria
    max_failed_steps: int = 2
    max_total_steps: int = 5
    min_steps_before_escalation: int = 2
    
    # Time-based criteria
    max_troubleshooting_time_minutes: int = 10
    max_time_per_step_seconds: int = 180
    
    # Confidence criteria
    min_confidence_threshold: float = 0.6
    
    # Customer criteria
    business_customer_auto_escalate: bool = True
    vip_customer_auto_escalate: bool = True
    
    # Issue-specific criteria
    auto_escalate_issues: Set[str] = field(default_factory=lambda: {
        "account_suspended", 
        "area_outage", 
        "hardware_failure",
        "fiber_break"
    })
    
    # Escalation keywords
    escalation_keywords: Set[str] = field(default_factory=lambda: {
        "technician", "ടെക്നീഷ്യൻ", 
        "supervisor", "സൂപ്പർവൈസർ", 
        "manager", "മാനേജർ", 
        "escalate", "എസ്കലേറ്റ്",
        "human", "മനുഷ്യൻ",
        "person", "വ്യക്തി",
        "speak", "സംസാരിക്കാൻ"
    })
    
    # Repeated issue criteria
    repeated_issue_threshold_days: int = 7
    repeated_issue_count: int = 2

class EscalationManager:
    """Manages escalation decisions based on multiple criteria"""
    
    def __init__(self, criteria: Optional[EscalationCriteria] = None):
        """Initialize the escalation manager with criteria"""
        self.criteria = criteria or EscalationCriteria()
        self.escalation_reasons: List[EscalationReason] = []
        self.start_time = datetime.now()
        self.last_step_time = datetime.now()
        self.step_times: Dict[str, float] = {}  # Step ID to time taken in seconds
        
    def should_escalate(self, 
                       failed_steps: int,
                       total_steps: int,
                       issue_type: str,
                       sub_issues: List[str],
                       confidence: float,
                       customer_info: Dict[str, Any],
                       conversation_history: List[Dict[str, str]],
                       previous_issues: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Determine if the issue should be escalated based on multiple criteria"""
        self.escalation_reasons = []
        
        # Check step-based criteria
        if total_steps < self.criteria.min_steps_before_escalation:
            # Don't escalate if we haven't tried enough steps yet
            return False
            
        if failed_steps >= self.criteria.max_failed_steps:
            self.escalation_reasons.append(EscalationReason.MULTIPLE_FAILURES)
            logger.info(f"Escalating due to multiple failures: {failed_steps} failed steps")
            
        if total_steps >= self.criteria.max_total_steps:
            self.escalation_reasons.append(EscalationReason.STEPS_EXHAUSTED)
            logger.info(f"Escalating due to steps exhausted: {total_steps} total steps")
        
        # Check time-based criteria
        troubleshooting_time = (datetime.now() - self.start_time).total_seconds() / 60
        if troubleshooting_time >= self.criteria.max_troubleshooting_time_minutes:
            self.escalation_reasons.append(EscalationReason.TIMEOUT)
            logger.info(f"Escalating due to timeout: {troubleshooting_time:.1f} minutes")
        
        # Check confidence criteria
        if confidence < self.criteria.min_confidence_threshold:
            self.escalation_reasons.append(EscalationReason.LOW_CONFIDENCE)
            logger.info(f"Escalating due to low confidence: {confidence:.2f}")
        
        # Check customer criteria
        if customer_info.get("business_customer") and self.criteria.business_customer_auto_escalate:
            self.escalation_reasons.append(EscalationReason.BUSINESS_CUSTOMER)
            logger.info("Escalating due to business customer")
            
        if customer_info.get("vip") and self.criteria.vip_customer_auto_escalate:
            self.escalation_reasons.append(EscalationReason.VIP_CUSTOMER)
            logger.info("Escalating due to VIP customer")
        
        # Check issue-specific criteria
        if issue_type in self.criteria.auto_escalate_issues:
            self.escalation_reasons.append(EscalationReason.TECHNICAL_COMPLEXITY)
            logger.info(f"Escalating due to complex issue type: {issue_type}")
            
        for sub_issue in sub_issues:
            if sub_issue in self.criteria.auto_escalate_issues:
                if sub_issue == "area_outage":
                    self.escalation_reasons.append(EscalationReason.AREA_OUTAGE)
                    logger.info(f"Escalating due to area outage sub-issue")
                elif sub_issue == "account_suspended":
                    self.escalation_reasons.append(EscalationReason.ACCOUNT_ISSUE)
                    logger.info(f"Escalating due to account issue sub-issue")
                else:
                    self.escalation_reasons.append(EscalationReason.HARDWARE_ISSUE)
                    logger.info(f"Escalating due to hardware issue sub-issue: {sub_issue}")
        
        # Check for escalation keywords in recent conversation
        if conversation_history and len(conversation_history) > 0:
            recent_messages = conversation_history[-3:]  # Last 3 exchanges
            for message in recent_messages:
                if "user" in message and message["user"]:
                    user_text = message["user"]
                    # Debug log the user text
                    logger.debug(f"Checking user text for keywords: {user_text}")
                    
                    # Check each keyword
                    for keyword in self.criteria.escalation_keywords:
                        # For Malayalam text, we need exact matching rather than lowercasing
                        if keyword in user_text or keyword.lower() in user_text.lower():
                            self.escalation_reasons.append(EscalationReason.ESCALATION_KEYWORD)
                            logger.info(f"Escalating due to keyword: {keyword}")
                            break
        
        # Check for repeated issues
        if previous_issues and len(previous_issues) > 0:
            recent_issues = [
                issue for issue in previous_issues 
                if (datetime.now() - datetime.fromisoformat(issue["timestamp"])).days <= self.criteria.repeated_issue_threshold_days
                and issue["issue_type"] == issue_type
            ]
            
            if len(recent_issues) >= self.criteria.repeated_issue_count:
                self.escalation_reasons.append(EscalationReason.REPEATED_ISSUE)
                logger.info(f"Escalating due to repeated issue: {len(recent_issues)} occurrences in last {self.criteria.repeated_issue_threshold_days} days")
        
        # Escalate if any criteria met
        return len(self.escalation_reasons) > 0
    
    def record_step_time(self, step_id: str):
        """Record the time taken for a step"""
        now = datetime.now()
        time_taken = (now - self.last_step_time).total_seconds()
        self.step_times[step_id] = time_taken
        self.last_step_time = now
        
        # Check if this step took too long
        if time_taken > self.criteria.max_time_per_step_seconds:
            logger.warning(f"Step {step_id} took {time_taken:.1f} seconds, exceeding limit of {self.criteria.max_time_per_step_seconds} seconds")
    
    def get_escalation_reasons(self) -> List[str]:
        """Get list of escalation reasons as strings"""
        return [reason.value for reason in self.escalation_reasons]
    
    def get_escalation_priority(self) -> str:
        """Get the priority level for escalation"""
        if any(reason in [EscalationReason.AREA_OUTAGE, EscalationReason.VIP_CUSTOMER, 
                         EscalationReason.BUSINESS_CUSTOMER] for reason in self.escalation_reasons):
            return "high"
        elif any(reason in [EscalationReason.MULTIPLE_FAILURES, EscalationReason.HARDWARE_ISSUE, 
                           EscalationReason.REPEATED_ISSUE] for reason in self.escalation_reasons):
            return "medium"
        else:
            return "low"
    
    def create_escalation_in_database(
        self,
        issue_type: str,
        customer_phone: str,
        customer_info: Dict[str, Any],
        conversation_summary: str,
        troubleshooting_steps: List[str],
        escalation_reasons: List[str]
    ) -> Optional[str]:
        """Create an escalation entry in the Supabase database"""
        try:
            # Build description with comprehensive details
            description_parts = [
                f"Issue Type: {issue_type}",
                f"Customer Phone: {customer_phone}",
                f"Escalation Reasons: {', '.join(escalation_reasons)}",
                f"Troubleshooting Time: {(datetime.now() - self.start_time).total_seconds() / 60:.1f} minutes",
                f"Steps Attempted: {len(troubleshooting_steps)}",
                "",
                "Customer Information:",
                f"- Name: {customer_info.get('name', 'Unknown')}",
                f"- Provider: {customer_info.get('isp', 'Unknown')}",
                f"- Region: {customer_info.get('region', 'Unknown')}",
                f"- Plan: {customer_info.get('plan', 'Unknown')}",
                "",
                "Troubleshooting Steps:",
            ]
            
            # Add troubleshooting steps
            for i, step in enumerate(troubleshooting_steps, 1):
                description_parts.append(f"{i}. {step}")
            
            description_parts.extend([
                "",
                "Conversation Summary:",
                conversation_summary
            ])
            
            description = "\n".join(description_parts)
            
            # Determine priority
            priority = self.get_escalation_priority()
            
            # Create escalation in database
            escalation_id = supabase_manager.create_escalation(
                issue_type=issue_type,
                description=description,
                priority=priority,
                customer_id=customer_info.get('customer_id'),  # If available
                escalated_by=None,  # Could be set to bot user ID if available
                assigned_to=None  # Will be assigned by human operator
            )
            
            if escalation_id:
                logger.info(f"✅ Escalation created in database: {escalation_id} (Priority: {priority})")
                return escalation_id
            else:
                logger.error("❌ Failed to create escalation in database")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating escalation in database: {e}")
            return None
    
    def reset(self):
        """Reset the escalation manager for a new session"""
        self.escalation_reasons = []
        self.start_time = datetime.now()
        self.last_step_time = datetime.now()
        self.step_times = {}
        
    def update_criteria(self, new_criteria: Dict[str, Any]):
        """Update escalation criteria with new values"""
        for key, value in new_criteria.items():
            if hasattr(self.criteria, key):
                setattr(self.criteria, key, value)
                logger.info(f"Updated escalation criteria: {key} = {value}")
            else:
                logger.warning(f"Unknown escalation criteria: {key}")
    
    def generate_escalation_summary(self) -> Dict[str, Any]:
        """Generate a summary of the escalation decision"""
        return {
            "escalated": len(self.escalation_reasons) > 0,
            "reasons": self.get_escalation_reasons(),
            "priority": self.get_escalation_priority(),
            "troubleshooting_time_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "step_times": self.step_times
        } 