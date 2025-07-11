from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import logging

from troubleshooting_engine import TroubleshootingEngine, TroubleshootingStep as EngineStep
from step_prioritizer import CustomerTechnicalProfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CallStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    DROPPED = "dropped"
    SCHEDULED_CALLBACK = "scheduled_callback"

@dataclass
class TroubleshootingStep:
    step: str
    timestamp: datetime
    result: str
    step_id: Optional[str] = None  # Reference to the step ID in TroubleshootingEngine
    success: Optional[bool] = None  # Whether the step was successful
    priority_score: float = 0.0  # Priority score of the step

@dataclass
class CallMemoryEnhanced:
    """Enhanced version of CallMemory with improved troubleshooting capabilities"""
    call_id: str
    phone_number: Optional[str] = None
    caller_phone: Optional[str] = None  # Added field for caller's phone number
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    device_type: Optional[str] = "fiber_modem"  # Default device type
    start_time: datetime = field(default_factory=datetime.now)
    area_issue_status: Optional[str] = None
    troubleshooting_steps: List[TroubleshootingStep] = field(default_factory=list)
    status: CallStatus = CallStatus.ACTIVE
    resolution_notes: Optional[str] = None
    last_interaction: Optional[str] = None
    customer_info: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    
    # New fields for enhanced troubleshooting
    current_issue_type: Optional[str] = None
    troubleshooting_engine: Optional[TroubleshootingEngine] = None
    attempted_step_ids: Set[str] = field(default_factory=set)
    successful_step_ids: Set[str] = field(default_factory=set)
    failed_step_ids: Set[str] = field(default_factory=set)
    issue_context: Dict[str, Any] = field(default_factory=dict)
    escalation_reasons: List[str] = field(default_factory=list)
    
    # New fields for Phase 2
    customer_technical_profile: Optional[CustomerTechnicalProfile] = None
    sub_issues: List[str] = field(default_factory=list)
    issue_confidence: float = 0.5  # Confidence in issue classification
    
    def initialize_troubleshooting_engine(self, knowledge_base_path: str):
        """Initialize the troubleshooting engine with the knowledge base path"""
        self.troubleshooting_engine = TroubleshootingEngine(knowledge_base_path)
        
        # Initialize customer technical profile
        self.customer_technical_profile = CustomerTechnicalProfile()
        
        logger.info(f"Initialized troubleshooting engine for call {self.call_id}")
    
    def update_customer_technical_profile(self):
        """Update customer technical profile based on customer info"""
        if not self.customer_info:
            return
            
        # Initialize profile if not already done
        if not self.customer_technical_profile:
            self.customer_technical_profile = CustomerTechnicalProfile()
        
        # Extract technical level from customer info if available
        if "technical_level" in self.customer_info:
            self.customer_technical_profile.technical_level = self.customer_info["technical_level"]
        elif "tech_savvy" in self.customer_info:
            # Map tech_savvy boolean to technical level (1-5)
            self.customer_technical_profile.technical_level = 4 if self.customer_info["tech_savvy"] else 2
            
        # Extract call history from customer info if available
        if "previous_calls" in self.customer_info:
            self.customer_technical_profile.previous_calls = self.customer_info["previous_calls"]
            
        if "successful_resolutions" in self.customer_info:
            self.customer_technical_profile.successful_resolutions = self.customer_info["successful_resolutions"]
            
        # Update troubleshooting engine's customer profile
        if self.troubleshooting_engine:
            self.troubleshooting_engine.update_customer_profile({
                "technical_level": self.customer_technical_profile.technical_level,
                "patience_level": self.customer_technical_profile.patience_level,
                "previous_calls": self.customer_technical_profile.previous_calls,
                "successful_resolutions": self.customer_technical_profile.successful_resolutions
            })
            
        logger.info(f"Updated customer technical profile: technical level={self.customer_technical_profile.technical_level}, "
                   f"patience={self.customer_technical_profile.patience_level}")
    
    def classify_issue(self, transcript: str) -> str:
        """Classify the issue type based on transcript and conversation history"""
        if not self.troubleshooting_engine:
            logger.warning("Troubleshooting engine not initialized")
            return "internet_down"  # Default issue type
            
        classification_result = self.troubleshooting_engine.classify_issue(transcript, self.conversation_history)
        self.current_issue_type = classification_result.issue_type
        self.sub_issues = classification_result.sub_issues
        self.issue_confidence = classification_result.confidence
        
        # Update issue context with metadata from classification
        if classification_result.metadata:
            for key, value in classification_result.metadata.items():
                if key not in ["confidence", "scores"]:  # Skip these metadata keys
                    self.update_issue_context(key, value)
        
        logger.info(f"Classified issue as: {self.current_issue_type} with confidence {self.issue_confidence:.2f}")
        if self.sub_issues:
            logger.info(f"Detected sub-issues: {self.sub_issues}")
            
        return self.current_issue_type
    
    def start_troubleshooting(self) -> Optional[EngineStep]:
        """Start troubleshooting for the current issue type"""
        if not self.troubleshooting_engine or not self.current_issue_type:
            logger.warning("Cannot start troubleshooting: engine not initialized or issue not classified")
            return None
            
        # Ensure customer technical profile is updated
        self.update_customer_technical_profile()
            
        step = self.troubleshooting_engine.start_troubleshooting(self.current_issue_type)
        if step:
            logger.info(f"Started troubleshooting flow for {self.current_issue_type} with step {step.id}")
        return step
    
    def get_next_step(self, user_response: str) -> tuple[Optional[EngineStep], bool]:
        """Process user response and get the next troubleshooting step
        
        Returns:
            Tuple of (next_step, should_escalate)
        """
        if not self.troubleshooting_engine:
            logger.warning("Troubleshooting engine not initialized")
            return None, True
            
        next_step, should_escalate = self.troubleshooting_engine.process_response(user_response)
        
        if should_escalate:
            self.status = CallStatus.ESCALATED
            self.escalation_reasons.append("Troubleshooting flow exhausted or failed")
            logger.info(f"Call {self.call_id} escalated: troubleshooting flow exhausted")
            
        return next_step, should_escalate
    
    def add_troubleshooting_step(self, step: str, result: str, step_id: Optional[str] = None, success: Optional[bool] = None, priority_score: float = 0.0):
        """Add a troubleshooting step with timestamp and update context"""
        timestamp = datetime.now()
        
        # Add to local steps list
        self.troubleshooting_steps.append(
            TroubleshootingStep(
                step=step,
                timestamp=timestamp,
                result=result,
                step_id=step_id,
                success=success,
                priority_score=priority_score
            )
        )
        
        # Update sets for tracking
        if step_id:
            self.attempted_step_ids.add(step_id)
            if success is True:
                self.successful_step_ids.add(step_id)
            elif success is False:
                self.failed_step_ids.add(step_id)
        
        # Add to conversation history
        self.conversation_history.append({
            "user": step,
            "bot": result,
            "timestamp": timestamp.isoformat(),
            "step_id": step_id,
            "success": str(success) if success is not None else None
        })
        
        logger.info(f"Added troubleshooting step: {step} -> {result}")
    
    def update_issue_context(self, key: str, value: Any):
        """Update the issue context with new information"""
        self.issue_context[key] = value
        
        # Also update the troubleshooting engine context if available
        if self.troubleshooting_engine:
            self.troubleshooting_engine.update_issue_context(key, value)
            
        logger.info(f"Updated issue context: {key}={value}")
    
    def should_escalate(self) -> bool:
        """Check if the issue should be escalated based on troubleshooting progress"""
        if not self.troubleshooting_engine:
            return True
            
        return self.troubleshooting_engine.should_escalate()
    
    def get_call_duration(self) -> int:
        """Get call duration in seconds"""
        return int((datetime.now() - self.start_time).total_seconds())
    
    def get_troubleshooting_summary(self) -> Dict[str, Any]:
        """Get a summary of the troubleshooting session"""
        if self.troubleshooting_engine:
            return self.troubleshooting_engine.get_troubleshooting_summary()
        
        return {
            "issue_type": self.current_issue_type or "unknown",
            "sub_issues": self.sub_issues,
            "steps_attempted": len(self.attempted_step_ids),
            "steps_succeeded": len(self.successful_step_ids),
            "steps_failed": len(self.failed_step_ids),
            "should_escalate": True if not self.troubleshooting_engine else self.troubleshooting_engine.should_escalate()
        }
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate call summary for reporting"""
        troubleshooting_summary = self.get_troubleshooting_summary()
        
        return {
            "call_id": self.call_id,
            "phone_number": self.phone_number,
            "caller_phone": self.caller_phone,  # Include caller_phone in summary
            "customer_name": self.customer_name,
            "duration_seconds": self.get_call_duration(),
            "start_time": self.start_time.isoformat(),
            "status": self.status.value,
            "area_issue_status": self.area_issue_status,
            "troubleshooting_steps": [
                {
                    "step": step.step,
                    "timestamp": step.timestamp.isoformat(),
                    "result": step.result,
                    "step_id": step.step_id,
                    "success": step.success,
                    "priority_score": step.priority_score
                }
                for step in self.troubleshooting_steps
            ],
            "resolution_notes": self.resolution_notes,
            "customer_info": self.customer_info,
            "issue_type": self.current_issue_type,
            "sub_issues": self.sub_issues,
            "issue_confidence": self.issue_confidence,
            "troubleshooting_summary": troubleshooting_summary,
            "escalation_reasons": self.escalation_reasons,
            "customer_technical_level": self.customer_technical_profile.technical_level if self.customer_technical_profile else 2
        }
        
    def get_model_context(self) -> str:
        """Generate context string for the model"""
        context_parts = []
        
        # Add customer info
        if self.customer_info:
            context_parts.append("Customer Information:")
            context_parts.append(f"- Name: {self.customer_info.get('Customer Name', self.customer_info.get('name', 'Unknown'))}")
            context_parts.append(f"- Provider: {self.customer_info.get('Provider', self.customer_info.get('isp', 'Unknown'))}")
            context_parts.append(f"- Plan: {self.customer_info.get('Current Plan', self.customer_info.get('plan', 'Unknown'))}")
            context_parts.append(f"- Operator: {self.customer_info.get('Operator', self.customer_info.get('operator', 'Unknown'))}")
            context_parts.append(f"- Region: {self.customer_info.get('Region', 'Unknown')}")
            
            # Add technical level if available
            if self.customer_technical_profile:
                context_parts.append(f"- Technical Level: {self.customer_technical_profile.technical_level}/5")
        
        # Add issue context
        if self.issue_context:
            context_parts.append("\nIssue Context:")
            for key, value in self.issue_context.items():
                context_parts.append(f"- {key}: {value}")
        
        # Add issue classification
        if self.current_issue_type:
            context_parts.append("\nIssue Classification:")
            context_parts.append(f"- Main Issue: {self.current_issue_type}")
            if self.sub_issues:
                context_parts.append(f"- Sub-issues: {', '.join(self.sub_issues)}")
            context_parts.append(f"- Confidence: {self.issue_confidence:.2f}")
        
        # Add recent conversation history
        if self.conversation_history:
            context_parts.append("\nRecent Conversation:")
            for entry in self.conversation_history[-5:]:  # Last 5 exchanges
                context_parts.append(f"User: {entry['user']}")
                context_parts.append(f"Bot: {entry['bot']}")
        
        # Add troubleshooting steps
        if self.troubleshooting_steps:
            context_parts.append("\nTroubleshooting Steps:")
            for step in self.troubleshooting_steps[-3:]:  # Last 3 steps
                success_str = ""
                if step.success is not None:
                    success_str = " ✓" if step.success else " ✗"
                context_parts.append(f"- {step.step} -> {step.result}{success_str}")
        
        # Add troubleshooting summary
        if self.troubleshooting_engine:
            summary = self.get_troubleshooting_summary()
            context_parts.append("\nTroubleshooting Summary:")
            context_parts.append(f"- Issue Type: {summary.get('issue_type', 'Unknown')}")
            if summary.get('sub_issues'):
                context_parts.append(f"- Sub-issues: {', '.join(summary.get('sub_issues', []))}")
            context_parts.append(f"- Steps Attempted: {summary.get('steps_attempted', 0)}")
            context_parts.append(f"- Steps Succeeded: {summary.get('steps_succeeded', 0)}")
            context_parts.append(f"- Steps Failed: {summary.get('steps_failed', 0)}")
        
        return "\n".join(context_parts) 