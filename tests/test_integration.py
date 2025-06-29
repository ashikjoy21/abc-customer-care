#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from troubleshooting_engine import TroubleshootingEngine, TroubleshootingStep
from call_memory_enhanced import CallMemoryEnhanced
from exotel_bot_enhanced import ExotelBotEnhanced

class TestIntegration(unittest.TestCase):
    """Test the integration of TroubleshootingEngine, CallMemoryEnhanced, and ExotelBotEnhanced"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mocks for dependencies
        self.mock_db = MagicMock()
        self.mock_websocket = AsyncMock()
        
        # Create a mock for the text_to_speech function
        self.mock_tts_patcher = patch('utils.text_to_speech')
        self.mock_tts = self.mock_tts_patcher.start()
        self.mock_tts.return_value = b'mock_audio_data'
        
        # Create a mock for the transcriber
        self.mock_transcriber = MagicMock()
        
        # Set up the bot with mocks
        self.bot = ExotelBotEnhanced()
        self.bot.db = self.mock_db
        self.bot.websocket = self.mock_websocket
        
        # Mock the troubleshooting engine
        self.mock_engine = MagicMock()
        self.bot.call_memory.troubleshooting_engine = self.mock_engine
    
    def tearDown(self):
        """Clean up after tests"""
        self.mock_tts_patcher.stop()
    
    async def test_phone_number_validation(self):
        """Test phone number validation flow"""
        # Mock database responses
        self.mock_db.get_customer_by_phone = AsyncMock()
        self.mock_db.get_customer_by_phone.return_value = {"customer_id": "cust123"}
        
        self.mock_db.get_customer_details = AsyncMock()
        self.mock_db.get_customer_details.return_value = {
            "customer_id": "cust123",
            "name": "Test Customer",
            "plan": "Fiber Pro",
            "area_id": "area123"
        }
        
        self.mock_db.check_area_issue = AsyncMock()
        self.mock_db.check_area_issue.return_value = None
        
        # Test validation
        is_valid, customer_info = await self.bot.validate_phone_number("1234567890")
        
        # Verify
        self.assertTrue(is_valid)
        self.assertEqual(customer_info["name"], "Test Customer")
        self.assertEqual(self.bot.call_memory.customer_name, "Test Customer")
        self.assertEqual(self.bot.call_memory.phone_number, "1234567890")
    
    async def test_handle_dtmf_phone_collection(self):
        """Test DTMF handling for phone collection"""
        # Mock phone collector
        self.bot.phone_collector.add_digit = MagicMock()
        self.bot.phone_collector.is_complete = MagicMock(return_value=True)
        self.bot.phone_collector.get_number = MagicMock(return_value="1234567890")
        
        # Mock validate_phone_number
        self.bot.validate_phone_number = AsyncMock()
        self.bot.validate_phone_number.return_value = (True, {
            "name": "Test Customer",
            "plan": "Fiber Pro"
        })
        
        # Mock play_message
        self.bot.play_message = AsyncMock()
        
        # Call handle_dtmf
        await self.bot.handle_dtmf("5")
        
        # Verify
        self.bot.phone_collector.add_digit.assert_called_once_with("5")
        self.bot.validate_phone_number.assert_called_once()
        self.bot.play_message.assert_called_once()
        self.assertFalse(self.bot.waiting_for_phone)
    
    async def test_on_transcription_issue_classification(self):
        """Test transcription handling with issue classification"""
        # Set up
        self.bot.call_active = True
        self.bot.waiting_for_phone = False
        
        # Mock transcript enhancer
        self.bot.transcript_enhancer = MagicMock()
        self.bot.transcript_enhancer.enhance = MagicMock(return_value="enhanced text")
        
        # Mock call memory methods
        self.bot.call_memory.classify_issue = MagicMock(return_value="internet_down")
        self.bot.call_memory.start_troubleshooting = MagicMock()
        
        # Create a mock step
        mock_step = MagicMock()
        mock_step.id = "root"
        mock_step.malayalam = "മലയാളം പ്രശ്നം?"
        mock_step.english = "What's the issue?"
        self.bot.call_memory.start_troubleshooting.return_value = mock_step
        
        # Mock play_message
        self.bot.play_message = AsyncMock()
        
        # Call on_transcription
        await self.bot.on_transcription("ഇന്റർനെറ്റ് പ്രശ്നം")
        
        # Verify
        self.bot.call_memory.classify_issue.assert_called_once()
        self.bot.call_memory.start_troubleshooting.assert_called_once()
        self.bot.play_message.assert_called_once_with(mock_step.malayalam)
        self.bot.call_memory.add_troubleshooting_step.assert_called_once()
    
    async def test_on_transcription_next_step(self):
        """Test transcription handling with next step"""
        # Set up
        self.bot.call_active = True
        self.bot.waiting_for_phone = False
        
        # Mock transcript enhancer
        self.bot.transcript_enhancer = MagicMock()
        self.bot.transcript_enhancer.enhance = MagicMock(return_value="enhanced text")
        
        # Set current issue type
        self.bot.call_memory.current_issue_type = "internet_down"
        
        # Mock call memory methods
        mock_step = MagicMock()
        mock_step.id = "next_step"
        mock_step.malayalam = "അടുത്ത നിർദ്ദേശം"
        mock_step.english = "Next instruction"
        self.bot.call_memory.get_next_step = MagicMock(return_value=(mock_step, False))
        
        # Mock play_message
        self.bot.play_message = AsyncMock()
        
        # Call on_transcription
        await self.bot.on_transcription("മോഡം റീസ്റ്റാർട്ട് ചെയ്തു")
        
        # Verify
        self.bot.call_memory.get_next_step.assert_called_once_with("enhanced text")
        self.bot.play_message.assert_called_once_with(mock_step.malayalam)
        self.bot.call_memory.add_troubleshooting_step.assert_called_once()
    
    async def test_on_transcription_escalation(self):
        """Test transcription handling with escalation"""
        # Set up
        self.bot.call_active = True
        self.bot.waiting_for_phone = False
        
        # Mock transcript enhancer
        self.bot.transcript_enhancer = MagicMock()
        self.bot.transcript_enhancer.enhance = MagicMock(return_value="enhanced text")
        
        # Set current issue type
        self.bot.call_memory.current_issue_type = "internet_down"
        
        # Mock call memory methods
        self.bot.call_memory.get_next_step = MagicMock(return_value=(None, True))
        
        # Mock play_message and _send_call_summary
        self.bot.play_message = AsyncMock()
        self.bot._send_call_summary = AsyncMock()
        
        # Call on_transcription
        await self.bot.on_transcription("ഇപ്പോഴും പ്രവർത്തിക്കുന്നില്ല")
        
        # Verify
        self.bot.call_memory.get_next_step.assert_called_once()
        self.assertEqual(self.bot.call_memory.status.value, "escalated")
        self.bot.play_message.assert_called_once()
        self.bot._send_call_summary.assert_called_once()
    
    async def test_send_call_summary(self):
        """Test sending call summary"""
        # Mock call memory methods
        self.bot.call_memory.generate_summary = MagicMock(return_value={
            "call_id": "test_call",
            "phone_number": "1234567890",
            "customer_name": "Test Customer",
            "duration_seconds": 120,
            "status": "escalated",
            "issue_type": "internet_down",
            "escalation_reasons": ["Too many failed steps"]
        })
        
        self.bot.call_memory.get_troubleshooting_summary = MagicMock(return_value={
            "steps_attempted": 3,
            "steps_succeeded": 1,
            "steps_failed": 2
        })
        
        # Call _send_call_summary
        await self.bot._send_call_summary()
        
        # Verify
        self.bot.call_memory.generate_summary.assert_called_once()
        self.bot.call_memory.get_troubleshooting_summary.assert_called_once()


if __name__ == "__main__":
    # Run tests
    unittest.main()