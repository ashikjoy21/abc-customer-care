import os
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta

from troubleshooting_engine import (
    TroubleshootingEngine, 
    TroubleshootingStep, 
    TroubleshootingFlow,
    StepStatus
)
from call_memory_enhanced import CallMemoryEnhanced

# Sample JSON data for mocking the knowledge base file
SAMPLE_KB_DATA = """
```json
{
  "common_patterns": {
    "escalation_triggers": ["multiple_devices", "business_customer", "recurring_issue"],
    "immediate_resolution": ["check_payment", "restart_modem"]
  },
  "decision_tree": {
    "root_question": {
      "malayalam": "എന്താണ് പ്രശ്നം?",
      "english": "What is the issue?"
    },
    "branches": [
      {
        "condition": "no internet",
        "route_to": "internet_down_scenario"
      },
      {
        "condition": "slow internet",
        "route_to": "slow_internet_scenario"
      }
    ]
  },
  "scenarios": [
    {
      "id": "internet_down_scenario",
      "description": "Internet not working at all",
      "solution": {
        "steps": [
          {
            "step": 1,
            "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക",
            "english": "Restart your modem",
            "technical_details": "Power cycle the modem to clear temporary issues"
          },
          {
            "step": 2,
            "malayalam": "കേബിൾ കണക്ഷനുകൾ പരിശോധിക്കുക",
            "english": "Check cable connections",
            "technical_details": "Ensure all cables are properly connected"
          }
        ],
        "escalation": {
          "condition": "If problem persists after all steps",
          "priority": "medium"
        }
      }
    }
  ]
}
```
"""

class TestTroubleshootingEngine(unittest.TestCase):
    """Test cases for TroubleshootingEngine"""
    
    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_KB_DATA)
    @patch('os.path.exists', return_value=True)
    def setUp(self, mock_exists, mock_file):
        """Set up test environment"""
        self.engine = TroubleshootingEngine('/fake/path')
        
        # Manually create a flow for testing
        flow = TroubleshootingFlow(
            issue_type="internet_down",
            root_step_id="root"
        )
        
        # Add root step
        root_step = TroubleshootingStep(
            id="root",
            description="Initial issue identification",
            malayalam="എന്താണ് പ്രശ്നം?",
            english="What is the issue?"
        )
        root_step.next_steps = {
            "no internet": "internet_down_scenario_step_1",
            "slow internet": "slow_internet_scenario_step_1"
        }
        flow.steps["root"] = root_step
        
        # Add first step of internet down scenario
        step1 = TroubleshootingStep(
            id="internet_down_scenario_step_1",
            description="Step 1 for internet_down_scenario",
            malayalam="മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക",
            english="Restart your modem",
            technical_details="Power cycle the modem to clear temporary issues"
        )
        step1.next_steps = {"default": "internet_down_scenario_step_2"}
        flow.steps["internet_down_scenario_step_1"] = step1
        
        # Add second step of internet down scenario
        step2 = TroubleshootingStep(
            id="internet_down_scenario_step_2",
            description="Step 2 for internet_down_scenario",
            malayalam="കേബിൾ കണക്ഷനുകൾ പരിശോധിക്കുക",
            english="Check cable connections",
            technical_details="Ensure all cables are properly connected"
        )
        flow.steps["internet_down_scenario_step_2"] = step2
        
        # Set escalation triggers
        flow.escalation_triggers = ["multiple_devices", "business_customer", "recurring_issue"]
        
        # Add flow to engine
        self.engine.flows["internet_down"] = flow
        
    def test_classify_issue(self):
        """Test issue classification"""
        # Test internet down classification
        transcript = "നെറ്റ് കിട്ടുന്നില്ല"  # "Internet not working" in Malayalam
        conversation_history = [{"user": "ഇന്റർനെറ്റ് ഇല്ല", "bot": "ശരി"}]  # "No internet" in Malayalam
        issue_type = self.engine.classify_issue(transcript, conversation_history)
        self.assertEqual(issue_type, "internet_down")
        
        # Test slow internet classification
        transcript = "വേഗത കുറവ്"  # "Speed is slow" in Malayalam
        conversation_history = [{"user": "സ്ലോ ആണ്", "bot": "ശരി"}]  # "It's slow" in Malayalam
        issue_type = self.engine.classify_issue(transcript, conversation_history)
        self.assertEqual(issue_type, "slow_internet")
    
    def test_start_troubleshooting(self):
        """Test starting a troubleshooting flow"""
        step = self.engine.start_troubleshooting("internet_down")
        self.assertIsNotNone(step)
        self.assertEqual(step.id, "root")
        self.assertEqual(step.english, "What is the issue?")
    
    def test_process_response(self):
        """Test processing user response and moving to next step"""
        # Start troubleshooting
        self.engine.start_troubleshooting("internet_down")
        
        # Process first response
        next_step, should_escalate = self.engine.process_response("no internet")
        self.assertFalse(should_escalate)
        self.assertEqual(next_step.id, "internet_down_scenario_step_1")
        self.assertEqual(next_step.english, "Restart your modem")
        
        # Process second response
        next_step, should_escalate = self.engine.process_response("I restarted it and it worked")
        self.assertFalse(should_escalate)
        self.assertEqual(next_step.id, "internet_down_scenario_step_2")
        self.assertEqual(next_step.english, "Check cable connections")
        
        # Process final response (should lead to escalation as there are no more steps)
        next_step, should_escalate = self.engine.process_response("I checked the cables")
        self.assertTrue(should_escalate)
        self.assertIsNone(next_step)
    
    def test_normal_lights_no_internet_scenario(self):
        """Test the scenario where modem lights are normal but no internet"""
        # Manually add the normal lights scenario step to the flow
        flow = self.engine.flows["internet_down"]
        
        # Add step for checking WiFi name
        normal_lights_step = TroubleshootingStep(
            id="normal_lights_scenario_step_1",
            description="Check WiFi name",
            malayalam="ഫോണിലെ WiFi ലിസ്റ്റിൽ നിങ്ങളുടെ സാധാരണ WiFi പേര് പരിശോധിക്കുക",
            english="Check if your usual WiFi name appears in your phone's WiFi list",
            technical_details="Determine if modem configuration has been reset"
        )
        normal_lights_step.next_steps = {"same_name": "technician_visit", "different_name": "technician_visit"}
        flow.steps["normal_lights_scenario_step_1"] = normal_lights_step
        
        # Update root step to include path to normal lights scenario
        flow.steps["root"].next_steps["normal_lights_no_internet"] = "normal_lights_scenario_step_1"
        
        # Start troubleshooting
        self.engine.start_troubleshooting("internet_down")
        
        # Process response for normal lights scenario
        next_step, should_escalate = self.engine.process_response("normal_lights_no_internet")
        self.assertFalse(should_escalate)
        self.assertEqual(next_step.id, "normal_lights_scenario_step_1")
        self.assertEqual(next_step.english, "Check if your usual WiFi name appears in your phone's WiFi list")
        
        # Process response for same WiFi name (should lead to technician visit)
        next_step, should_escalate = self.engine.process_response("same_name")
        self.assertTrue(should_escalate)
        self.assertIsNone(next_step)
        
        # Reset and test different WiFi name path
        self.engine.start_troubleshooting("internet_down")
        self.engine.process_response("normal_lights_no_internet")
        
        # Process response for different WiFi name (should also lead to technician visit)
        next_step, should_escalate = self.engine.process_response("different_name")
        self.assertTrue(should_escalate)
        self.assertIsNone(next_step)
    
    def test_should_escalate(self):
        """Test escalation decision logic"""
        # Start with no escalation needed
        self.assertFalse(self.engine.should_escalate())
        
        # Add escalation trigger to context
        self.engine.update_issue_context("multiple_devices", True)
        self.assertTrue(self.engine.should_escalate())
    
    def test_get_troubleshooting_summary(self):
        """Test getting troubleshooting summary"""
        # Start troubleshooting
        self.engine.start_troubleshooting("internet_down")
        
        # Process responses
        self.engine.process_response("no internet")
        self.engine.process_response("I restarted it but it didn't work")
        
        # Get summary
        summary = self.engine.get_troubleshooting_summary()
        self.assertEqual(summary["issue_type"], "internet_down")
        self.assertEqual(summary["steps_attempted"], 2)
        self.assertEqual(summary["steps_failed"], 1)


class TestCallMemoryEnhanced(unittest.TestCase):
    """Test cases for CallMemoryEnhanced"""
    
    def setUp(self):
        """Set up test environment"""
        self.call_memory = CallMemoryEnhanced(call_id="test_call_123")
        
        # Mock the TroubleshootingEngine
        self.mock_engine = MagicMock()
        self.call_memory.troubleshooting_engine = self.mock_engine
        
    def test_initialize_troubleshooting_engine(self):
        """Test initializing the troubleshooting engine"""
        with patch('troubleshooting_engine.TroubleshootingEngine') as mock_engine_class:
            mock_engine_instance = MagicMock()
            mock_engine_class.return_value = mock_engine_instance
            
            self.call_memory.initialize_troubleshooting_engine("/fake/path")
            
            mock_engine_class.assert_called_once_with("/fake/path")
            self.assertEqual(self.call_memory.troubleshooting_engine, mock_engine_instance)
    
    def test_classify_issue(self):
        """Test issue classification"""
        self.mock_engine.classify_issue.return_value = "internet_down"
        
        issue_type = self.call_memory.classify_issue("Internet not working")
        
        self.mock_engine.classify_issue.assert_called_once()
        self.assertEqual(issue_type, "internet_down")
        self.assertEqual(self.call_memory.current_issue_type, "internet_down")
    
    def test_start_troubleshooting(self):
        """Test starting troubleshooting"""
        mock_step = MagicMock()
        mock_step.id = "test_step"
        self.mock_engine.start_troubleshooting.return_value = mock_step
        self.call_memory.current_issue_type = "internet_down"
        
        step = self.call_memory.start_troubleshooting()
        
        self.mock_engine.start_troubleshooting.assert_called_once_with("internet_down")
        self.assertEqual(step, mock_step)
    
    def test_get_next_step(self):
        """Test getting next step"""
        mock_step = MagicMock()
        mock_step.id = "next_step"
        self.mock_engine.process_response.return_value = (mock_step, False)
        
        next_step, should_escalate = self.call_memory.get_next_step("It worked")
        
        self.mock_engine.process_response.assert_called_once_with("It worked")
        self.assertEqual(next_step, mock_step)
        self.assertFalse(should_escalate)
    
    def test_get_next_step_escalation(self):
        """Test escalation when getting next step"""
        self.mock_engine.process_response.return_value = (None, True)
        
        next_step, should_escalate = self.call_memory.get_next_step("Still not working")
        
        self.assertTrue(should_escalate)
        self.assertEqual(self.call_memory.status.value, "escalated")
        self.assertIn("Troubleshooting flow exhausted or failed", self.call_memory.escalation_reasons)
    
    def test_add_troubleshooting_step(self):
        """Test adding a troubleshooting step"""
        step = "Restart modem"
        result = "Modem restarted successfully"
        step_id = "step_1"
        success = True
        
        self.call_memory.add_troubleshooting_step(step, result, step_id, success)
        
        self.assertEqual(len(self.call_memory.troubleshooting_steps), 1)
        self.assertEqual(self.call_memory.troubleshooting_steps[0].step, step)
        self.assertEqual(self.call_memory.troubleshooting_steps[0].result, result)
        self.assertEqual(self.call_memory.troubleshooting_steps[0].step_id, step_id)
        self.assertEqual(self.call_memory.troubleshooting_steps[0].success, success)
        
        self.assertIn(step_id, self.call_memory.attempted_step_ids)
        self.assertIn(step_id, self.call_memory.successful_step_ids)
    
    def test_update_issue_context(self):
        """Test updating issue context"""
        key = "router_model"
        value = "TP-Link AC1750"
        
        self.call_memory.update_issue_context(key, value)
        
        self.assertEqual(self.call_memory.issue_context[key], value)
        self.mock_engine.update_issue_context.assert_called_once_with(key, value)
    
    def test_generate_summary(self):
        """Test generating call summary"""
        # Setup
        self.call_memory.phone_number = "1234567890"
        self.call_memory.customer_name = "Test User"
        self.call_memory.current_issue_type = "internet_down"
        
        # Add a troubleshooting step
        self.call_memory.add_troubleshooting_step("Restart modem", "Restarted", "step_1", True)
        
        # Mock the troubleshooting summary
        mock_summary = {
            "issue_type": "internet_down",
            "steps_attempted": 1,
            "steps_succeeded": 1,
            "steps_failed": 0,
            "should_escalate": False
        }
        self.mock_engine.get_troubleshooting_summary.return_value = mock_summary
        
        # Generate summary
        summary = self.call_memory.generate_summary()
        
        # Verify
        self.assertEqual(summary["call_id"], "test_call_123")
        self.assertEqual(summary["phone_number"], "1234567890")
        self.assertEqual(summary["customer_name"], "Test User")
        self.assertEqual(summary["issue_type"], "internet_down")
        self.assertEqual(summary["troubleshooting_summary"], mock_summary)
        self.assertEqual(len(summary["troubleshooting_steps"]), 1)
        self.assertEqual(summary["troubleshooting_steps"][0]["step"], "Restart modem")
        self.assertEqual(summary["troubleshooting_steps"][0]["result"], "Restarted")
        self.assertEqual(summary["troubleshooting_steps"][0]["step_id"], "step_1")
        self.assertEqual(summary["troubleshooting_steps"][0]["success"], True)


if __name__ == "__main__":
    unittest.main() 