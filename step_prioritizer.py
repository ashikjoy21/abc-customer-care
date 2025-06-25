import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TroubleshootingStepInfo:
    """Information about a troubleshooting step for prioritization"""
    step_id: str
    success_probability: float = 0.5  # Default probability of success
    complexity: int = 2  # 1-5 scale (1: very simple, 5: very complex)
    technical_level_required: int = 2  # 1-5 scale (1: non-technical, 5: expert)
    estimated_time: int = 60  # Estimated time in seconds
    dependencies: List[str] = field(default_factory=list)  # Steps that must be completed before this one
    priority_score: float = 0.0  # Calculated priority score

@dataclass
class CustomerTechnicalProfile:
    """Profile of customer's technical ability"""
    technical_level: int = 2  # 1-5 scale (1: non-technical, 5: expert)
    patience_level: int = 3  # 1-5 scale (1: impatient, 5: very patient)
    previous_calls: int = 0  # Number of previous support calls
    successful_resolutions: int = 0  # Number of successful resolutions
    average_time_per_step: int = 120  # Average time taken per step in seconds
    
    @property
    def success_ratio(self) -> float:
        """Calculate ratio of successful resolutions to total calls"""
        if self.previous_calls == 0:
            return 0.5  # Default ratio
        return self.successful_resolutions / self.previous_calls

class StepPrioritizer:
    """Prioritizes troubleshooting steps based on multiple factors"""
    
    def __init__(self):
        """Initialize the step prioritizer"""
        # Default weights for different factors
        self.weights = {
            "success_probability": 0.35,
            "complexity": 0.20,
            "technical_level_match": 0.15,
            "estimated_time": 0.15,
            "dependencies": 0.15
        }
        
        # Historical success rates for common steps
        self.historical_success_rates = {
            # Internet down scenarios
            "restart_modem": 0.75,
            "check_cables": 0.60,
            "power_cycle": 0.70,
            "check_wifi_password": 0.85,
            "reset_network_settings": 0.65,
            
            # TV issues
            "restart_stb": 0.80,
            "check_hdmi": 0.70,
            "rescan_channels": 0.60,
            "check_tv_input": 0.90,
            
            # Default for unknown steps
            "default": 0.50
        }
        
        # Step complexity ratings
        self.step_complexity = {
            # Simple steps
            "restart_modem": 1,
            "power_cycle": 1,
            "check_tv_input": 1,
            
            # Moderate steps
            "check_cables": 2,
            "check_wifi_password": 2,
            "restart_stb": 2,
            
            # Complex steps
            "reset_network_settings": 3,
            "rescan_channels": 3,
            "configure_dns": 4,
            "update_firmware": 4,
            
            # Default for unknown steps
            "default": 2
        }
    
    def _get_step_success_probability(self, step_id: str, issue_type: str, sub_issues: List[str]) -> float:
        """Get the probability of success for a step based on historical data and context"""
        # Start with base success rate from historical data
        base_rate = self.historical_success_rates.get(step_id, self.historical_success_rates["default"])
        
        # Adjust based on issue type
        if issue_type == "internet_down" and step_id == "restart_modem":
            base_rate += 0.1  # Restarting modem is very effective for internet down issues
        elif issue_type == "wifi_issues" and step_id == "check_wifi_password":
            base_rate += 0.15  # Password issues are common for WiFi problems
        
        # Adjust based on sub-issues
        if "modem_issue" in sub_issues and step_id in ["restart_modem", "power_cycle"]:
            base_rate += 0.15  # These steps are more effective for modem issues
        elif "cable_issue" in sub_issues and step_id == "check_cables":
            base_rate += 0.2  # Cable checking is very effective for cable issues
        
        # Ensure probability is between 0 and 1
        return max(0.0, min(1.0, base_rate))
    
    def _get_step_complexity(self, step_id: str) -> int:
        """Get the complexity rating for a step"""
        return self.step_complexity.get(step_id, self.step_complexity["default"])
    
    def _calculate_technical_level_match(self, step_complexity: int, customer_profile: CustomerTechnicalProfile) -> float:
        """Calculate how well the step complexity matches the customer's technical level"""
        # Perfect match if complexity equals technical level
        if step_complexity == customer_profile.technical_level:
            return 1.0
            
        # Calculate difference (0 to 4)
        difference = abs(step_complexity - customer_profile.technical_level)
        
        # Convert to a score (1.0 to 0.0)
        return max(0.0, 1.0 - (difference * 0.25))
    
    def _calculate_time_score(self, estimated_time: int, customer_profile: CustomerTechnicalProfile) -> float:
        """Calculate score based on estimated time vs customer patience"""
        # Base time score - lower is better
        base_time_score = 1.0 - min(1.0, estimated_time / 300)  # 5 minutes is baseline
        
        # Adjust for customer patience
        patience_factor = customer_profile.patience_level / 3.0  # Normalize around 1.0
        
        return base_time_score * patience_factor
    
    def _check_dependencies_met(self, step_id: str, completed_steps: List[str], step_info: Dict[str, TroubleshootingStepInfo]) -> bool:
        """Check if all dependencies for a step have been completed"""
        if step_id not in step_info:
            return True  # No info means no dependencies
            
        for dependency in step_info[step_id].dependencies:
            if dependency not in completed_steps:
                return False
                
        return True
    
    def _calculate_priority_score(self, step_info: TroubleshootingStepInfo, 
                                 customer_profile: CustomerTechnicalProfile,
                                 completed_steps: List[str],
                                 all_steps: Dict[str, TroubleshootingStepInfo]) -> float:
        """Calculate overall priority score for a step"""
        # Calculate technical level match
        technical_match = self._calculate_technical_level_match(
            step_info.complexity, customer_profile
        )
        
        # Calculate time score
        time_score = self._calculate_time_score(
            step_info.estimated_time, customer_profile
        )
        
        # Calculate dependency score (1.0 if all dependencies met, 0.0 otherwise)
        dependency_score = 1.0 if self._check_dependencies_met(
            step_info.step_id, completed_steps, all_steps
        ) else 0.0
        
        # Calculate weighted score
        weighted_score = (
            step_info.success_probability * self.weights["success_probability"] +
            (1.0 - (step_info.complexity / 5.0)) * self.weights["complexity"] +
            technical_match * self.weights["technical_level_match"] +
            time_score * self.weights["estimated_time"] +
            dependency_score * self.weights["dependencies"]
        )
        
        return weighted_score
    
    def prioritize_steps(self, 
                        steps: List[str], 
                        issue_type: str,
                        sub_issues: List[str],
                        customer_profile: CustomerTechnicalProfile,
                        completed_steps: List[str] = None) -> List[Tuple[str, float]]:
        """Prioritize troubleshooting steps based on multiple factors
        
        Args:
            steps: List of step IDs to prioritize
            issue_type: Type of issue being troubleshot
            sub_issues: List of detected sub-issues
            customer_profile: Customer's technical profile
            completed_steps: List of already completed step IDs
            
        Returns:
            List of (step_id, priority_score) tuples, sorted by priority (highest first)
        """
        if completed_steps is None:
            completed_steps = []
            
        # Create step info objects
        step_info = {}
        for step_id in steps:
            # Get success probability based on historical data and context
            success_prob = self._get_step_success_probability(step_id, issue_type, sub_issues)
            
            # Get complexity rating
            complexity = self._get_step_complexity(step_id)
            
            # Create step info object
            step_info[step_id] = TroubleshootingStepInfo(
                step_id=step_id,
                success_probability=success_prob,
                complexity=complexity,
                technical_level_required=complexity,  # For simplicity, use same value
                estimated_time=60 * complexity  # Simple formula: 60 seconds * complexity
            )
        
        # Calculate priority scores
        prioritized_steps = []
        for step_id in steps:
            # Skip already completed steps
            if step_id in completed_steps:
                continue
                
            # Calculate priority score
            priority_score = self._calculate_priority_score(
                step_info[step_id],
                customer_profile,
                completed_steps,
                step_info
            )
            
            # Store score
            step_info[step_id].priority_score = priority_score
            prioritized_steps.append((step_id, priority_score))
        
        # Sort by priority score (highest first)
        prioritized_steps.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Prioritized {len(prioritized_steps)} steps for issue type '{issue_type}'")
        for step_id, score in prioritized_steps[:3]:  # Log top 3
            logger.info(f"  - {step_id}: {score:.2f}")
        
        return prioritized_steps
    
    def update_success_rate(self, step_id: str, success: bool):
        """Update historical success rate for a step based on outcome"""
        if step_id not in self.historical_success_rates:
            self.historical_success_rates[step_id] = 0.5  # Start with default
            
        # Simple exponential moving average update
        current_rate = self.historical_success_rates[step_id]
        new_outcome = 1.0 if success else 0.0
        alpha = 0.1  # Learning rate
        
        updated_rate = (1 - alpha) * current_rate + alpha * new_outcome
        self.historical_success_rates[step_id] = updated_rate
        
        logger.info(f"Updated success rate for '{step_id}': {current_rate:.2f} -> {updated_rate:.2f}") 