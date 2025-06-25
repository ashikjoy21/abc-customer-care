#!/usr/bin/env python3
"""
Test script for the escalation criteria implementation.
This script tests various scenarios to validate the escalation manager's decision-making.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from escalation_manager import EscalationManager, EscalationReason, EscalationCriteria

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_escalation_criteria():
    """Test the escalation criteria under various scenarios"""
    print("\n===== TESTING ESCALATION CRITERIA =====")
    
    # Create test cases
    test_cases = [
        {
            "name": "Basic no-escalation",
            "params": {
                "failed_steps": 0,
                "total_steps": 2,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.9,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": False
        },
        {
            "name": "Multiple failures",
            "params": {
                "failed_steps": 3,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.MULTIPLE_FAILURES.value
        },
        {
            "name": "Steps exhausted",
            "params": {
                "failed_steps": 1,
                "total_steps": 6,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.STEPS_EXHAUSTED.value
        },
        {
            "name": "Low confidence",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.4,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.LOW_CONFIDENCE.value
        },
        {
            "name": "Business customer",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium", "business_customer": True},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.BUSINESS_CUSTOMER.value
        },
        {
            "name": "VIP customer",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium", "vip": True},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.VIP_CUSTOMER.value
        },
        {
            "name": "Area outage",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": ["area_outage"],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.AREA_OUTAGE.value
        },
        {
            "name": "Account issue",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": ["account_suspended"],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.ACCOUNT_ISSUE.value
        },
        {
            "name": "Hardware issue",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": ["hardware_failure"],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.HARDWARE_ISSUE.value
        },
        {
            "name": "Escalation keyword",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "I want to speak to a technician"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.ESCALATION_KEYWORD.value
        },
        {
            "name": "Malayalam escalation keyword",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "എനിക്ക് ഒരു ടെക്നീഷ്യൻ വേണം"}],
                "previous_issues": []
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.ESCALATION_KEYWORD.value
        },
        {
            "name": "Repeated issue",
            "params": {
                "failed_steps": 1,
                "total_steps": 3,
                "issue_type": "internet_down",
                "sub_issues": [],
                "confidence": 0.8,
                "customer_info": {"technical_level": "medium", "patience_level": "medium"},
                "conversation_history": [{"user": "My internet is not working again"}],
                "previous_issues": [
                    {"issue_type": "internet_down", "timestamp": (datetime.now() - timedelta(days=2)).isoformat()},
                    {"issue_type": "internet_down", "timestamp": (datetime.now() - timedelta(days=5)).isoformat()}
                ]
            },
            "expected_escalation": True,
            "expected_reason": EscalationReason.REPEATED_ISSUE.value
        }
    ]
    
    # Run test cases
    passed = 0
    failed = 0
    
    for tc in test_cases:
        print(f"\n--- Testing: {tc['name']} ---")
        
        # Create escalation manager
        manager = EscalationManager()
        
        # Call should_escalate with test parameters
        params = tc["params"]
        result = manager.should_escalate(
            failed_steps=params["failed_steps"],
            total_steps=params["total_steps"],
            issue_type=params["issue_type"],
            sub_issues=params["sub_issues"],
            confidence=params["confidence"],
            customer_info=params["customer_info"],
            conversation_history=params["conversation_history"],
            previous_issues=params.get("previous_issues", [])
        )
        
        # Check if result matches expected
        if result == tc["expected_escalation"]:
            if result:  # If escalation happened, check reason
                reasons = manager.get_escalation_reasons()
                if tc.get("expected_reason") in reasons:
                    print(f"✅ PASS: Got expected escalation with reason: {reasons}")
                    passed += 1
                else:
                    print(f"❌ FAIL: Got escalation but with wrong reason: {reasons}, expected: {tc.get('expected_reason')}")
                    failed += 1
            else:
                print("✅ PASS: Correctly did not escalate")
                passed += 1
        else:
            print(f"❌ FAIL: Expected escalation={tc['expected_escalation']}, got={result}")
            if result:
                print(f"Escalation reasons: {manager.get_escalation_reasons()}")
            failed += 1
    
    # Print summary
    print(f"\n===== TEST SUMMARY =====")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return passed == len(test_cases)

def test_escalation_priority():
    """Test the escalation priority determination"""
    print("\n===== TESTING ESCALATION PRIORITY =====")
    
    # Create test cases for priority
    test_cases = [
        {
            "name": "High priority - VIP customer",
            "reasons": [EscalationReason.VIP_CUSTOMER, EscalationReason.MULTIPLE_FAILURES],
            "expected_priority": "high"
        },
        {
            "name": "High priority - Business customer",
            "reasons": [EscalationReason.BUSINESS_CUSTOMER],
            "expected_priority": "high"
        },
        {
            "name": "High priority - Area outage",
            "reasons": [EscalationReason.AREA_OUTAGE],
            "expected_priority": "high"
        },
        {
            "name": "Medium priority - Hardware issue",
            "reasons": [EscalationReason.HARDWARE_ISSUE],
            "expected_priority": "medium"
        },
        {
            "name": "Medium priority - Multiple failures",
            "reasons": [EscalationReason.MULTIPLE_FAILURES],
            "expected_priority": "medium"
        },
        {
            "name": "Medium priority - Repeated issue",
            "reasons": [EscalationReason.REPEATED_ISSUE],
            "expected_priority": "medium"
        },
        {
            "name": "Normal priority - Low confidence",
            "reasons": [EscalationReason.LOW_CONFIDENCE],
            "expected_priority": "normal"
        },
        {
            "name": "Normal priority - Steps exhausted",
            "reasons": [EscalationReason.STEPS_EXHAUSTED],
            "expected_priority": "normal"
        }
    ]
    
    # Run test cases
    passed = 0
    failed = 0
    
    for tc in test_cases:
        print(f"\n--- Testing: {tc['name']} ---")
        
        # Create escalation manager and set reasons
        manager = EscalationManager()
        manager.escalation_reasons = tc["reasons"]
        
        # Get priority
        priority = manager.get_escalation_priority()
        
        # Check if priority matches expected
        if priority == tc["expected_priority"]:
            print(f"✅ PASS: Got expected priority: {priority}")
            passed += 1
        else:
            print(f"❌ FAIL: Expected priority={tc['expected_priority']}, got={priority}")
            failed += 1
    
    # Print summary
    print(f"\n===== PRIORITY TEST SUMMARY =====")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return passed == len(test_cases)

def test_custom_criteria():
    """Test customizing escalation criteria"""
    print("\n===== TESTING CUSTOM CRITERIA =====")
    
    # Create custom criteria
    custom_criteria = EscalationCriteria(
        max_failed_steps=1,  # Lower threshold
        max_total_steps=3,   # Lower threshold
        min_confidence_threshold=0.7,  # Higher threshold
        max_troubleshooting_time_minutes=5  # Lower threshold
    )
    
    # Create manager with custom criteria
    manager = EscalationManager(custom_criteria)
    
    # Test case that should escalate with custom criteria but not with default
    test_case = {
        "failed_steps": 1,
        "total_steps": 3,
        "issue_type": "internet_down",
        "sub_issues": [],
        "confidence": 0.65,  # Below custom threshold but above default
        "customer_info": {"technical_level": "medium", "patience_level": "medium"},
        "conversation_history": [{"user": "My internet is not working"}],
        "previous_issues": []
    }
    
    # Check with custom criteria (should escalate)
    result_custom = manager.should_escalate(**test_case)
    
    # Check with default criteria (should not escalate)
    manager_default = EscalationManager()
    result_default = manager_default.should_escalate(**test_case)
    
    # Verify results
    if result_custom and not result_default:
        print("✅ PASS: Custom criteria correctly triggered escalation when default did not")
        return True
    else:
        print(f"❌ FAIL: Custom criteria test failed. Custom result: {result_custom}, Default result: {result_default}")
        return False

def main():
    """Run all tests"""
    print("\n===== ESCALATION MANAGER TESTS =====")
    
    # Run all tests
    criteria_test = test_escalation_criteria()
    priority_test = test_escalation_priority()
    custom_test = test_custom_criteria()
    
    # Overall result
    if criteria_test and priority_test and custom_test:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED ❌")
        return 1

if __name__ == "__main__":
    main() 