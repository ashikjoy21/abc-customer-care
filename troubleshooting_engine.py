import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from issue_classifier import IssueClassifier, IssueClassificationResult
from step_prioritizer import StepPrioritizer, CustomerTechnicalProfile
from escalation_manager import EscalationManager, EscalationCriteria

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StepStatus(Enum):
    """Status of a troubleshooting step"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED_SUCCESS = "completed_success"
    COMPLETED_FAILURE = "completed_failure"
    SKIPPED = "skipped"

@dataclass
class TroubleshootingStep:
    """Represents a single troubleshooting step"""
    id: str
    description: str
    malayalam: str
    english: str
    technical_details: Optional[str] = None
    next_steps: Dict[str, str] = field(default_factory=dict)
    status: StepStatus = StepStatus.NOT_STARTED
    attempted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_response: Optional[str] = None
    priority_score: float = 0.0  # Added priority score

@dataclass
class TroubleshootingFlow:
    """Represents a complete troubleshooting flow for an issue type"""
    issue_type: str
    root_step_id: str
    steps: Dict[str, TroubleshootingStep] = field(default_factory=dict)
    current_step_id: Optional[str] = None
    escalation_triggers: List[str] = field(default_factory=list)
    immediate_resolution_conditions: List[str] = field(default_factory=list)
    sub_issues: List[str] = field(default_factory=list)  # Added sub-issues field

class TroubleshootingEngine:
    """Engine to manage structured troubleshooting flows"""
    
    def __init__(self, knowledge_base_path: str):
        """Initialize the troubleshooting engine with knowledge base path"""
        self.knowledge_base_path = knowledge_base_path
        self.flows: Dict[str, TroubleshootingFlow] = {}
        self.current_flow: Optional[TroubleshootingFlow] = None
        self.attempted_steps: Set[str] = set()
        self.successful_steps: Set[str] = set()
        self.failed_steps: Set[str] = set()
        self.issue_context: Dict[str, Any] = {}
        
        # Initialize advanced issue classifier
        self.issue_classifier = IssueClassifier()
        
        # Initialize step prioritizer
        self.step_prioritizer = StepPrioritizer()
        
        # Initialize customer technical profile (default values)
        self.customer_profile = CustomerTechnicalProfile()
        
        # Initialize escalation manager
        self.escalation_manager = EscalationManager()
        
        # Store conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # Load troubleshooting flows from knowledge base
        self._load_flows()
    
    def _load_flows(self):
        """Load troubleshooting flows from knowledge base files"""
        try:
            # Load internet troubleshooting flow
            internet_flow_path = os.path.join(self.knowledge_base_path, "internet_down.md")
            if os.path.exists(internet_flow_path):
                self._parse_flow_from_markdown(internet_flow_path, "internet_down")
                
            # Add more flows for other issue types here
            
            logger.info(f"Loaded {len(self.flows)} troubleshooting flows")
        except Exception as e:
            logger.error(f"Error loading troubleshooting flows: {e}")
    
    def _parse_flow_from_markdown(self, file_path: str, issue_type: str):
        """Parse troubleshooting flow from markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find JSON section in markdown (between triple backticks)
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            
            if not json_match:
                logger.warning(f"No JSON content found in {file_path}")
                return
                
            json_content = json_match.group(1)
            data = json.loads(json_content)
            
            # Create flow
            flow = TroubleshootingFlow(
                issue_type=issue_type,
                root_step_id="root",
                escalation_triggers=data.get("common_patterns", {}).get("escalation_triggers", []),
                immediate_resolution_conditions=data.get("common_patterns", {}).get("immediate_resolution", [])
            )
            
            # Parse decision tree
            decision_tree = data.get("decision_tree", {})
            root_question = decision_tree.get("root_question", {})
            
            # Create root step
            root_step = TroubleshootingStep(
                id="root",
                description="Initial issue identification",
                malayalam=root_question.get("malayalam", ""),
                english=root_question.get("english", "")
            )
            
            # Add branches as next steps
            for branch in decision_tree.get("branches", []):
                condition = branch.get("condition", "")
                route_to = branch.get("route_to", "")
                if condition and route_to:
                    root_step.next_steps[condition] = route_to
            
            flow.steps["root"] = root_step
            flow.current_step_id = "root"
            
            # Parse scenarios
            for scenario in data.get("scenarios", []):
                scenario_id = scenario.get("id", "")
                if not scenario_id:
                    continue
                    
                # Create steps for each scenario
                solution = scenario.get("solution", {})
                steps = solution.get("steps", [])
                
                for step_data in steps:
                    step_id = f"{scenario_id}_step_{step_data.get('step', 0)}"
                    step = TroubleshootingStep(
                        id=step_id,
                        description=f"Step {step_data.get('step', 0)} for {scenario_id}",
                        malayalam=step_data.get("malayalam", ""),
                        english=step_data.get("english", ""),
                        technical_details=step_data.get("technical_details", "")
                    )
                    
                    # Set next step (if not the last step)
                    if step_data.get("step", 0) < len(steps):
                        next_step_id = f"{scenario_id}_step_{step_data.get('step', 0) + 1}"
                        step.next_steps["default"] = next_step_id
                    
                    flow.steps[step_id] = step
                
                # Add escalation info
                escalation = solution.get("escalation", {})
                if escalation:
                    escalation_step_id = f"{scenario_id}_escalation"
                    escalation_step = TroubleshootingStep(
                        id=escalation_step_id,
                        description=f"Escalation for {scenario_id}",
                        malayalam=escalation.get("condition", ""),
                        english=escalation.get("condition", ""),
                        technical_details=f"Priority: {escalation.get('priority', 'medium')}"
                    )
                    flow.steps[escalation_step_id] = escalation_step
            
            self.flows[issue_type] = flow
            logger.info(f"Successfully parsed flow for {issue_type} with {len(flow.steps)} steps")
            
        except Exception as e:
            logger.error(f"Error parsing flow from {file_path}: {e}")
    
    def classify_issue(self, transcript: str, conversation_history: List[Dict[str, str]]) -> IssueClassificationResult:
        """Classify the issue type based on transcript and conversation history using the advanced classifier"""
        try:
            classification_result = self.issue_classifier.classify(transcript, conversation_history)
            
            # Update sub-issues if any are detected
            if classification_result.sub_issues and self.current_flow:
                if not hasattr(self.current_flow, 'sub_issues'):
                    self.current_flow.sub_issues = []
                    
                # Add any new sub-issues that aren't already tracked
                for sub_issue in classification_result.sub_issues:
                    if sub_issue not in self.current_flow.sub_issues:
                        self.current_flow.sub_issues.append(sub_issue)
                
            # Update issue context with confidence and metadata
            self.issue_context["confidence"] = classification_result.confidence
            self.issue_context["detected_issue"] = classification_result.issue_type
            
            # Add all metadata from classification result to issue context
            for key, value in classification_result.metadata.items():
                if key not in ["scores"]:  # Skip scores, they're too verbose
                    self.issue_context[key] = value
            
            # Special handling for red light detection
            if "is_red_light" in classification_result.metadata:
                self.issue_context["is_red_light"] = classification_result.metadata["is_red_light"]
                self.issue_context["needs_technician"] = classification_result.metadata.get("needs_technician", True)
                self.issue_context["restart_first"] = classification_result.metadata.get("restart_first", True)
                
                # Add fiber_cut to sub-issues if detected
                if "fiber_cut" in classification_result.sub_issues:
                    if not hasattr(self.current_flow, 'sub_issues'):
                        self.current_flow.sub_issues = []
                    if "fiber_cut" not in self.current_flow.sub_issues:
                        self.current_flow.sub_issues.append("fiber_cut")
                
            logger.info(f"Classified issue as '{classification_result.issue_type}' with confidence {classification_result.confidence:.2f}")
            if classification_result.sub_issues:
                logger.info(f"Detected sub-issues: {classification_result.sub_issues}")
                
            return classification_result
        except Exception as e:
            logger.error(f"Error classifying issue: {e}")
            # Return a default classification on error
            return IssueClassificationResult(issue_type="internet_down", confidence=0.5)
    
    def update_customer_profile(self, customer_data: Dict[str, Any]):
        """Update the customer technical profile based on customer data"""
        if not customer_data:
            return
            
        # Extract technical level from customer data if available
        if "technical_level" in customer_data:
            self.customer_profile.technical_level = customer_data["technical_level"]
            
        # Extract patience level from customer data if available
        if "patience_level" in customer_data:
            self.customer_profile.patience_level = customer_data["patience_level"]
            
        # Extract call history from customer data if available
        if "previous_calls" in customer_data:
            self.customer_profile.previous_calls = customer_data["previous_calls"]
            
        if "successful_resolutions" in customer_data:
            self.customer_profile.successful_resolutions = customer_data["successful_resolutions"]
            
        logger.info(f"Updated customer profile: technical level={self.customer_profile.technical_level}, "
                   f"patience={self.customer_profile.patience_level}")
                   
        # Reset escalation manager for new customer
        self.escalation_manager.reset()
        
        # Update escalation criteria based on customer profile
        escalation_updates = {}
        
        # Adjust criteria based on technical level
        if self.customer_profile.technical_level == "high":
            escalation_updates["max_failed_steps"] = 3  # Allow more failures for tech-savvy customers
            escalation_updates["max_total_steps"] = 7   # Allow more steps for tech-savvy customers
        elif self.customer_profile.technical_level == "low":
            escalation_updates["max_failed_steps"] = 1  # Escalate sooner for less tech-savvy customers
            escalation_updates["max_total_steps"] = 3   # Fewer steps for less tech-savvy customers
            
        # Adjust criteria based on patience level
        if self.customer_profile.patience_level == "high":
            escalation_updates["max_troubleshooting_time_minutes"] = 15  # Allow more time
        elif self.customer_profile.patience_level == "low":
            escalation_updates["max_troubleshooting_time_minutes"] = 5   # Less time
            
        # Apply updates if any
        if escalation_updates:
            self.escalation_manager.update_criteria(escalation_updates)
    
    def start_troubleshooting(self, issue_type: str) -> TroubleshootingStep:
        """Start a troubleshooting flow for the given issue type"""
        if issue_type not in self.flows:
            logger.warning(f"No flow found for issue type: {issue_type}, defaulting to internet_down")
            issue_type = "internet_down" if "internet_down" in self.flows else list(self.flows.keys())[0]
        
        self.current_flow = self.flows[issue_type]
        
        # Check for fiber cut sub-issue - special handling
        if hasattr(self, 'issue_context') and self.issue_context.get('is_red_light') == True:
            logger.info("Red light detected - prioritizing fiber cut troubleshooting")
            # Add fiber_cut sub-issue if not already present
            if not hasattr(self.current_flow, 'sub_issues'):
                self.current_flow.sub_issues = []
            if 'fiber_cut' not in self.current_flow.sub_issues:
                self.current_flow.sub_issues.append('fiber_cut')
                
            # Create a custom step for immediate fiber cut handling
            fiber_cut_step = TroubleshootingStep(
                id="fiber_cut_detected",
                description="Red light detected - likely fiber cut issue",
                malayalam="ചുവന്ന ലൈറ്റ് കാണുന്നത് ഫൈബർ കട്ട് പ്രശ്നം സൂചിപ്പിക്കുന്നു. ആദ്യം മോഡം റീസ്റ്റാർട്ട് ചെയ്യുക (പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക). മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. ദയവായി 5 മിനിറ്റ് കാത്തിരിക്കുക. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ മാത്രം ഞങ്ങളെ വീണ്ടും വിളിക്കുക. അപ്പോൾ ഫൈബർ കട്ട് ശരിയാക്കാൻ ടെക്നീഷ്യനെ അയക്കുന്നതാണ്.",
                english="Red light indicates a fiber cut issue. First restart your modem (power off and on through the plug switch). The modem takes about 5 minutes to be fully online. Please wait for 5 minutes. ONLY call us back if the issue persists after 5 minutes. Then we will send a technician to fix the fiber cut.",
                technical_details="Fiber cable is likely cut or damaged. Customer should restart modem first, but technician visit will be needed if issue persists.",
                next_steps={"default": "schedule_technician"},
                priority_score=10.0  # Highest priority
            )
            
            # Add the custom step to the flow
            self.current_flow.steps["fiber_cut_detected"] = fiber_cut_step
            
            # Set the current step to this fiber cut step
            self.current_flow.current_step_id = "fiber_cut_detected"
            
            # Add a technician scheduling step if it doesn't exist
            if "schedule_technician" not in self.current_flow.steps:
                tech_step = TroubleshootingStep(
                    id="schedule_technician",
                    description="Schedule technician visit for fiber cut repair",
                    malayalam="ഫൈബർ കട്ട് പരിഹരിക്കാൻ ടെക്നീഷ്യനെ അയക്കുന്നതാണ്. സാധ്യമെങ്കിൽ ടെക്നീഷ്യൻ ഇന്നോ അല്ലെങ്കിൽ നാളെയോ എത്തും. കൃത്യമായ സമയം പറയാൻ കഴിയില്ല.",
                    english="We will send a technician to fix the fiber cut. The technician will reach today or tomorrow. We cannot provide an exact time.",
                    technical_details="Schedule technician visit for fiber cut repair."
                )
                self.current_flow.steps["schedule_technician"] = tech_step
        else:
            # Normal flow - start with the root step
            self.current_flow.current_step_id = self.current_flow.root_step_id
        
        return self.get_current_step()
    
    def get_current_step(self) -> Optional[TroubleshootingStep]:
        """Get the current troubleshooting step"""
        if not self.current_flow or not self.current_flow.current_step_id:
            return None
            
        return self.current_flow.steps.get(self.current_flow.current_step_id)
    
    def _prioritize_next_steps(self, current_step: TroubleshootingStep, user_response: str) -> Optional[str]:
        """Determine the next step based on prioritization"""
        if not self.current_flow:
            return None
            
        # First check if there's a specific next step based on response
        for condition, step_id in current_step.next_steps.items():
            if condition.lower() in user_response.lower():
                return step_id
        
        # If no specific match and we have a default, use it
        if "default" in current_step.next_steps:
            return current_step.next_steps["default"]
            
        # If no default, find all available steps we haven't tried yet
        available_steps = []
        for step_id, step in self.current_flow.steps.items():
            if step_id not in self.attempted_steps:
                available_steps.append(step_id)
        
        if not available_steps:
            return None  # No available steps left
            
        # Prioritize available steps
        prioritized_steps = self.step_prioritizer.prioritize_steps(
            steps=available_steps,
            issue_type=self.current_flow.issue_type,
            sub_issues=self.current_flow.sub_issues,
            customer_profile=self.customer_profile,
            completed_steps=list(self.attempted_steps)
        )
        
        if not prioritized_steps:
            return None
            
        # Return the highest priority step
        return prioritized_steps[0][0]
    
    def process_response(self, user_response: str) -> Tuple[Optional[TroubleshootingStep], bool]:
        """Process user response and move to next step
        Returns: (next_step, should_escalate)
        """
        if not self.current_flow or not self.current_flow.current_step_id:
            return None, False
            
        current_step = self.get_current_step()
        if not current_step:
            return None, False
            
        # Update step status
        current_step.user_response = user_response
        current_step.completed_at = datetime.now()
        self.attempted_steps.add(current_step.id)
        
        # Record step time in escalation manager
        self.escalation_manager.record_step_time(current_step.id)
        
        # Update conversation history
        self.conversation_history.append({"user": user_response})
        
        # Check if we should skip further troubleshooting (for red light/fiber cut)
        if self.issue_context.get("skip_further_troubleshooting", False):
            logger.info("Skipping further troubleshooting due to red light/fiber cut detection")
            return None, True
        
        # Determine if step was successful
        success_indicators = ["worked", "fixed", "resolved", "better", "good", "yes", "done", "completed", "ശരിയായി", "നന്നായി"]
        failure_indicators = ["not working", "still", "same problem", "no change", "didn't work", "failed", "ശരിയായില്ല", "ഇപ്പോഴും", "ഇല്ല"]
        
        success = any(indicator in user_response.lower() for indicator in success_indicators)
        failure = any(indicator in user_response.lower() for indicator in failure_indicators)
        
        if success:
            current_step.status = StepStatus.COMPLETED_SUCCESS
            self.successful_steps.add(current_step.id)
            # Update success rate in step prioritizer
            self.step_prioritizer.update_success_rate(current_step.id, True)
        elif failure:
            current_step.status = StepStatus.COMPLETED_FAILURE
            self.failed_steps.add(current_step.id)
            # Update success rate in step prioritizer
            self.step_prioritizer.update_success_rate(current_step.id, False)
        else:
            current_step.status = StepStatus.COMPLETED_SUCCESS  # Assume success if unclear
            self.successful_steps.add(current_step.id)
            # Update success rate in step prioritizer with assumption of success
            self.step_prioritizer.update_success_rate(current_step.id, True)
        
        # Check if we should escalate using the enhanced escalation manager
        should_escalate = self.should_escalate()
        if should_escalate:
            return None, True
            
        # Determine next step using prioritization
        next_step_id = self._prioritize_next_steps(current_step, user_response)
        
        # Update current step
        if next_step_id and self.current_flow:
            self.current_flow.current_step_id = next_step_id
            next_step = self.get_current_step()
            if next_step:
                next_step.attempted_at = datetime.now()
                next_step.status = StepStatus.IN_PROGRESS
            return next_step, False
        
        # If we've exhausted all steps, escalate
        return None, True
    
    def should_escalate(self) -> bool:
        """Determine if the issue should be escalated using the enhanced escalation manager"""
        if not self.current_flow:
            return True
            
        # Extract customer info from profile and context
        customer_info = {
            "technical_level": self.customer_profile.technical_level,
            "patience_level": self.customer_profile.patience_level,
            "business_customer": self.issue_context.get("business_customer", False),
            "vip": self.issue_context.get("vip_customer", False)
        }
        
        # Get previous issues if available
        previous_issues = []
        if "previous_issues" in self.issue_context:
            previous_issues = self.issue_context["previous_issues"]
        
        # Use the escalation manager to determine if we should escalate
        issue_type = self.current_flow.issue_type
        sub_issues = self.current_flow.sub_issues if hasattr(self.current_flow, 'sub_issues') else []
        
        # Calculate confidence based on issue classifier result or default to 0.8
        confidence = self.issue_context.get("confidence", 0.8)
        
        # Use the enhanced escalation manager to determine if we should escalate
        should_escalate = self.escalation_manager.should_escalate(
            failed_steps=len(self.failed_steps),
            total_steps=len(self.attempted_steps),
            issue_type=issue_type,
            sub_issues=sub_issues,
            confidence=confidence,
            customer_info=customer_info,
            conversation_history=self.conversation_history,
            previous_issues=previous_issues
        )
        
        if should_escalate:
            # Log the escalation reasons
            reasons = self.escalation_manager.get_escalation_reasons()
            logger.info(f"Escalating due to: {reasons}")
            
            # Store escalation reasons in issue context
            self.issue_context["escalation_reasons"] = reasons
            self.issue_context["escalation_priority"] = self.escalation_manager.get_escalation_priority()
            
        return should_escalate
    
    def get_troubleshooting_summary(self) -> Dict[str, Any]:
        """Get a summary of the troubleshooting session"""
        if not self.current_flow:
            return {
                "issue_type": "unknown",
                "steps_attempted": 0,
                "steps_succeeded": 0,
                "steps_failed": 0,
                "should_escalate": True
            }
            
        # Get sub-issues if available
        sub_issues = self.current_flow.sub_issues if hasattr(self.current_flow, 'sub_issues') else []
        
        # Get escalation summary if available
        escalation_summary = {}
        if self.should_escalate():
            escalation_summary = self.escalation_manager.generate_escalation_summary()
            
        return {
            "issue_type": self.current_flow.issue_type,
            "sub_issues": sub_issues,
            "steps_attempted": len(self.attempted_steps),
            "steps_succeeded": len(self.successful_steps),
            "steps_failed": len(self.failed_steps),
            "should_escalate": self.should_escalate(),
            "escalation_summary": escalation_summary,
            "steps_detail": [
                {
                    "id": step_id,
                    "description": self.current_flow.steps[step_id].description if step_id in self.current_flow.steps else "",
                    "status": self.current_flow.steps[step_id].status.value if step_id in self.current_flow.steps else "unknown"
                }
                for step_id in self.attempted_steps
            ]
        }
    
    def update_issue_context(self, key: str, value: Any):
        """Update the issue context with new information"""
        self.issue_context[key] = value 