#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from issue_classifier import IssueClassifier, IssueClassificationResult
from step_prioritizer import StepPrioritizer, CustomerTechnicalProfile, TroubleshootingStepInfo

class TestIssueClassifier(unittest.TestCase):
    """Test cases for the IssueClassifier"""
    
    def setUp(self):
        """Set up test environment"""
        self.classifier = IssueClassifier()
        
    def test_classify_internet_down(self):
        """Test classification of internet down issues"""
        # Test in Malayalam
        result = self.classifier.classify("നെറ്റ് കിട്ടുന്നില്ല")
        self.assertEqual(result.issue_type, "internet_down")
        self.assertGreaterEqual(result.confidence, 0.5)
        
        # Test in English
        result = self.classifier.classify("My internet is not working")
        self.assertEqual(result.issue_type, "internet_down")
        self.assertGreaterEqual(result.confidence, 0.5)
        
    def test_classify_slow_internet(self):
        """Test classification of slow internet issues"""
        # Test in Malayalam
        result = self.classifier.classify("ഇന്റർനെറ്റ് വളരെ പതുക്കെയാണ്")
        self.assertEqual(result.issue_type, "slow_internet")
        self.assertGreater(result.confidence, 0.5)
        
        # Test in English
        result = self.classifier.classify("My internet is very slow and keeps buffering")
        self.assertEqual(result.issue_type, "slow_internet")
        self.assertGreater(result.confidence, 0.5)
    
    def test_classify_wifi_issues(self):
        """Test classification of WiFi issues"""
        result = self.classifier.classify("My WiFi password is not working")
        self.assertEqual(result.issue_type, "wifi_issues")
        self.assertGreater(result.confidence, 0.5)
    
    def test_classify_tv_issues(self):
        """Test classification of TV issues"""
        result = self.classifier.classify("My TV channels are not working")
        self.assertEqual(result.issue_type, "tv_issues")
        self.assertGreater(result.confidence, 0.5)
    
    def test_sub_issue_detection(self):
        """Test detection of sub-issues"""
        # Test modem issue detection
        result = self.classifier.classify("My internet is not working, the modem light is blinking red")
        self.assertEqual(result.issue_type, "internet_down")
        self.assertIn("modem_issue", result.sub_issues)
        
        # Test cable issue detection
        result = self.classifier.classify("Internet not working, I think the cable might be damaged")
        self.assertEqual(result.issue_type, "internet_down")
        self.assertIn("cable_issue", result.sub_issues)
    
    def test_technical_context_extraction(self):
        """Test extraction of technical context"""
        result = self.classifier.classify("My internet speed is only 10 mbps")
        self.assertEqual(result.issue_type, "slow_internet")
        self.assertIn("mentioned_speed", result.metadata)
        self.assertEqual(result.metadata["mentioned_speed"]["value"], 10)
        self.assertEqual(result.metadata["mentioned_speed"]["unit"], "mbps")
    
    def test_conversation_history(self):
        """Test classification with conversation history"""
        conversation_history = [
            {"user": "I have a problem with my internet", "bot": "What kind of problem?"},
            {"user": "It's very slow", "bot": "I understand. Can you tell me more?"}
        ]
        
        result = self.classifier.classify("Videos keep buffering", conversation_history)
        self.assertEqual(result.issue_type, "slow_internet")
        self.assertGreater(result.confidence, 0.5)


class TestStepPrioritizer(unittest.TestCase):
    """Test cases for the StepPrioritizer"""
    
    def setUp(self):
        """Set up test environment"""
        self.prioritizer = StepPrioritizer()
        self.customer_profile = CustomerTechnicalProfile(
            technical_level=2,
            patience_level=3,
            previous_calls=2,
            successful_resolutions=1
        )
    
    def test_prioritize_steps(self):
        """Test basic step prioritization"""
        steps = ["restart_modem", "check_cables", "reset_network_settings"]
        issue_type = "internet_down"
        sub_issues = []
        
        prioritized_steps = self.prioritizer.prioritize_steps(
            steps, issue_type, sub_issues, self.customer_profile
        )
        
        # Check that we have the right number of steps
        self.assertEqual(len(prioritized_steps), 3)
        
        # Check that steps are sorted by priority score (highest first)
        self.assertGreaterEqual(prioritized_steps[0][1], prioritized_steps[1][1])
        self.assertGreaterEqual(prioritized_steps[1][1], prioritized_steps[2][1])
    
    def test_prioritize_with_sub_issues(self):
        """Test prioritization with sub-issues"""
        steps = ["restart_modem", "check_cables", "reset_network_settings"]
        issue_type = "internet_down"
        sub_issues = ["modem_issue"]
        
        prioritized_steps = self.prioritizer.prioritize_steps(
            steps, issue_type, sub_issues, self.customer_profile
        )
        
        # Restart modem should be highest priority for modem issues
        self.assertEqual(prioritized_steps[0][0], "restart_modem")
    
    def test_prioritize_with_completed_steps(self):
        """Test prioritization with completed steps"""
        steps = ["restart_modem", "check_cables", "reset_network_settings"]
        issue_type = "internet_down"
        sub_issues = []
        completed_steps = ["restart_modem"]
        
        prioritized_steps = self.prioritizer.prioritize_steps(
            steps, issue_type, sub_issues, self.customer_profile, completed_steps
        )
        
        # Check that we have only 2 steps (completed step is filtered out)
        self.assertEqual(len(prioritized_steps), 2)
        
        # Check that restart_modem is not in the prioritized steps
        step_ids = [step[0] for step in prioritized_steps]
        self.assertNotIn("restart_modem", step_ids)
    
    def test_technical_level_match(self):
        """Test technical level matching"""
        # Create two customer profiles with different technical levels
        beginner = CustomerTechnicalProfile(technical_level=1)
        expert = CustomerTechnicalProfile(technical_level=5)
        
        steps = ["restart_modem", "configure_dns"]
        issue_type = "internet_down"
        sub_issues = []
        
        # For beginner, simple steps should be prioritized
        beginner_priorities = self.prioritizer.prioritize_steps(
            steps, issue_type, sub_issues, beginner
        )
        self.assertEqual(beginner_priorities[0][0], "restart_modem")
        
        # For expert, more complex steps might be prioritized
        # (This depends on other factors too, so we're not asserting the exact order)
        expert_priorities = self.prioritizer.prioritize_steps(
            steps, issue_type, sub_issues, expert
        )
        
        # But the scores should be different
        beginner_scores = {step[0]: step[1] for step in beginner_priorities}
        expert_scores = {step[0]: step[1] for step in expert_priorities}
        
        self.assertNotEqual(beginner_scores["configure_dns"], expert_scores["configure_dns"])
    
    def test_update_success_rate(self):
        """Test updating success rates"""
        # Get initial success rate
        initial_rate = self.prioritizer.historical_success_rates["restart_modem"]
        
        # Update with success
        self.prioritizer.update_success_rate("restart_modem", True)
        
        # Success should increase the rate
        self.assertGreater(self.prioritizer.historical_success_rates["restart_modem"], initial_rate)
        
        # Update with failure
        current_rate = self.prioritizer.historical_success_rates["restart_modem"]
        self.prioritizer.update_success_rate("restart_modem", False)
        
        # Failure should decrease the rate
        self.assertLess(self.prioritizer.historical_success_rates["restart_modem"], current_rate)
    
    def test_new_step_success_rate(self):
        """Test updating success rate for a new step"""
        # Step doesn't exist initially
        self.assertNotIn("new_test_step", self.prioritizer.historical_success_rates)
        
        # Update with success
        self.prioritizer.update_success_rate("new_test_step", True)
        
        # Step should now exist with updated rate
        self.assertIn("new_test_step", self.prioritizer.historical_success_rates)
        self.assertGreater(self.prioritizer.historical_success_rates["new_test_step"], 0.5)


if __name__ == "__main__":
    unittest.main() 