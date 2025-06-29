import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from call_flow import (
    CallStatus,
    TroubleshootingStep,
    CallMemory,
    ExotelBot,
    PhoneNumberCollector
)

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_transcriber():
    return Mock()

@pytest.fixture
def bot(mock_db):
    """Create bot instance with mocked dependencies"""
    bot = ExotelBot()
    bot.db = mock_db
    return bot

def test_call_memory_initialization():
    """Test CallMemory initialization"""
    call_id = "test_call_123"
    memory = CallMemory(call_id=call_id)
    
    assert memory.call_id == call_id
    assert memory.phone_number is None
    assert memory.customer_name is None
    assert memory.status == CallStatus.ACTIVE
    assert len(memory.troubleshooting_steps) == 0

def test_call_memory_add_troubleshooting_step():
    """Test adding troubleshooting steps"""
    memory = CallMemory(call_id="test")
    step = "Check internet connection"
    result = "Connection is working"
    
    memory.add_troubleshooting_step(step, result)
    
    assert len(memory.troubleshooting_steps) == 1
    assert memory.troubleshooting_steps[0].step == step
    assert memory.troubleshooting_steps[0].result == result
    assert isinstance(memory.troubleshooting_steps[0].timestamp, datetime)

def test_call_memory_generate_summary():
    """Test call summary generation"""
    memory = CallMemory(
        call_id="test",
        phone_number="1234567890",
        customer_name="Test User"
    )
    memory.add_troubleshooting_step("Step 1", "Result 1")
    
    summary = memory.generate_summary()
    
    assert summary["call_id"] == "test"
    assert summary["phone_number"] == "1234567890"
    assert summary["customer_name"] == "Test User"
    assert summary["status"] == CallStatus.ACTIVE.value
    assert len(summary["troubleshooting_steps"]) == 1
    assert summary["troubleshooting_steps"][0]["step"] == "Step 1"
    assert summary["troubleshooting_steps"][0]["result"] == "Result 1"

def test_phone_number_collector():
    """Test phone number collection"""
    collector = PhoneNumberCollector()
    collector.start_collection()
    
    # Test valid number
    is_complete, phone, error = collector.add_digit("1")
    assert not is_complete
    assert phone is None
    assert error is None
    
    # Add remaining digits
    for digit in "234567890":
        is_complete, phone, error = collector.add_digit(digit)
    
    assert is_complete
    assert phone == "1234567890"
    assert error is None
    
    # Test reset
    collector.start_collection()
    collector.add_digit("1")
    is_complete, phone, error = collector.add_digit("*")
    assert not is_complete
    assert phone is None
    assert error == "ഫോൺ നമ്പർ റീസെറ്റ് ചെയ്തു. വീണ്ടും നൽകുക."

@pytest.mark.asyncio
async def test_bot_handle_start_message(bot):
    """Test handling start message"""
    data = {
        "type": "start",
        "call_id": "test_call_123"
    }
    
    with patch.object(bot, 'play_message') as mock_play:
        mock_play.return_value = {"type": "audio", "data": "test"}
        response = await bot.handle_message(data)
        
        assert response == {"type": "audio", "data": "test"}
        assert bot.call_memory is not None
        assert bot.call_memory.call_id == "test_call_123"
        mock_play.assert_called_once_with(
            "സ്വാഗതം! ദയവായി നിങ്ങളുടെ ഫോൺ നമ്പർ നൽകുക."
        )

@pytest.mark.asyncio
async def test_bot_handle_end_message(bot):
    """Test handling end message"""
    bot.call_memory = CallMemory(call_id="test")
    bot.transcriber = Mock()
    
    data = {"type": "end"}
    
    with patch.object(bot, '_send_call_summary') as mock_send:
        response = await bot.handle_message(data)
        
        assert response is None
        bot.transcriber.stop.assert_called_once()
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_bot_handle_dtmf_valid_number(bot):
    """Test handling DTMF for a valid phone number"""
    bot.call_memory = CallMemory(call_id="test")
    bot.db.get_customer_by_phone.return_value = {
        "Customer Name": "Test User",
        "User Name": "testuser",
        "Current Plan": "Test Service",
        "Region": "Test Region",
        "Provider": "Test Provider",
        "Operator": "Test Operator",
        "NickName": "testnick"
    }
    
    with patch.object(bot, 'play_message') as mock_play:
        mock_play.return_value = {"type": "audio", "data": "test"}
        
        # Add all digits
        for digit in "1234567890":
            response = await bot.handle_dtmf(digit)
        
        assert response == {"type": "audio", "data": "test"}
        assert bot.call_memory.phone_number == "1234567890"
        assert bot.call_memory.customer_name == "Test User"
        mock_play.assert_called_with("നമസ്കാരം Test User! എന്താണ് പ്രശ്നം?") 