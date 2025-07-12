import os
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
from telegram_notifier import TelegramBotManager

# Load environment variables
load_dotenv()

# Configure router
router = APIRouter()

# Initialize telegram bot manager for notifications
telegram_bot = None

async def get_telegram_bot():
    """Get or initialize the telegram bot."""
    global telegram_bot
    if telegram_bot is None:
        # Use the singleton pattern to avoid multiple instances
        telegram_bot = TelegramBotManager.get_instance()
        await telegram_bot.start()
    return telegram_bot

async def format_passthru_notification(data: Dict[str, Any]) -> str:
    """Format the notification message for Telegram."""
    ivr_option_desc = {
        "2": "Support Staff",
        "3": "Technical Team",
        "4": "Billing Department"
    }
    
    # Extract digits and remove quotes if present
    digits = data.get("digits") or data.get("Digits") or ""
    if digits and (digits.startswith('"') and digits.endswith('"')):
        digits = digits.strip('"')
    
    ivr_routed_to = ivr_option_desc.get(digits, "Unknown Department")
    
    # Format timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get caller phone from multiple possible field names
    caller_phone = data.get("From") or data.get("CallFrom") or "Unknown"
    call_sid = data.get("CallSid") or "Unknown"
    
    message = (
        f"🔄 *CALL ROUTED TO HUMAN STAFF*\n\n"
        f"*Time:* {timestamp}\n"
        f"*From:* `{caller_phone}`\n"
        f"*Call ID:* `{call_sid}`\n"
        f"*IVR Option:* {digits} ({ivr_routed_to})\n"
    )
    
    return message

@router.get("/exotel/passthru")
async def exotel_passthru(request: Request):
    """
    Handle Exotel passthru requests for IVR options.
    
    This endpoint receives data from Exotel when a caller selects
    an IVR option and routes the call to a human operator.
    
    Query Parameters:
    - From/CallFrom: Caller's phone number
    - CallSid: Unique call ID
    - digits/Digits: IVR option selected by caller
    """
    # Get query parameters
    query_params = dict(request.query_params)
    
    # Log all parameters for debugging
    logger.info(f"Received Exotel passthru request with all params: {query_params}")
    
    # Extract required parameters - handle multiple possible field names
    caller_phone = query_params.get("From") or query_params.get("CallFrom")
    call_sid = query_params.get("CallSid")
    digits = query_params.get("digits") or query_params.get("Digits")
    
    # Clean up digits parameter if it has quotes
    if digits and (digits.startswith('"') and digits.endswith('"')):
        digits = digits.strip('"')
    
    logger.info(f"Extracted parameters: caller_phone={caller_phone}, call_sid={call_sid}, digits={digits}")
    
    # Process IVR options 2, 3, or 4
    if digits in ["2", "3", "4"]:
        try:
            # Get telegram bot instance
            bot = await get_telegram_bot()
            logger.info(f"Telegram bot initialized: {bot is not None}")
            
            # Create customer info dict with available data
            customer_info = {
                "phone_number": caller_phone,
                "call_id": call_sid
            }
            
            # Format notification
            notification = await format_passthru_notification(query_params)
            logger.info(f"Formatted notification: {notification}")
            
            # Determine department based on option
            department = "human staff"
            if digits == "2":
                department = "Support Staff"
            elif digits == "3":
                department = "Technical Team"
            elif digits == "4":
                department = "Billing Department"
            
            # Send notification using the existing send_call_report method
            logger.info("Attempting to send Telegram notification...")
            await bot.send_call_report(
                phone=caller_phone,
                issue=f"IVR Option {digits} Selected",
                call_summary=f"Customer selected IVR option {digits} to speak with {department}",
                recent_transcripts=[],
                customer_info=customer_info,
                call_status="routed",
                resolution=f"Routed to {department}",
                duration=0,  # No call duration available
                was_resolved=False,
                troubleshooting_steps=[],
                caller_phone=caller_phone
            )
            
            # Log success
            logger.info(f"Successfully sent Telegram notification for CallSid={call_sid}")
            
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Error sending Telegram notification: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    else:
        logger.info(f"Ignoring request with digits={digits} - not a supported IVR option")
    
    # Always return success to Exotel
    return JSONResponse(content={"status": "success"}) 