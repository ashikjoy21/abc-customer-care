import logging
import os
import json
import redis
from typing import Any, Dict, List, Optional
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Global instance for singleton pattern
_bot_instance = None

class TelegramBotManager:
    """
    Manages Telegram bot operations for operator notifications and call reporting.
    """
    def __init__(self) -> None:
        self.is_running: bool = False
        self.logger = logging.getLogger(__name__)
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.operator_chat_id = os.getenv("TELEGRAM_OPERATOR_CHAT_ID")
        self.application = None
        self.bot = None  # Direct bot instance for sending messages
        
        # Initialize Redis client
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.logger.info("✅ Redis connected successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None

    @staticmethod
    def get_instance():
        """Get singleton instance of TelegramBotManager"""
        global _bot_instance
        if _bot_instance is None:
            _bot_instance = TelegramBotManager()
        return _bot_instance

    def _generate_incident_id(self, incident_type: str, location: str) -> str:
        """Generate a simple incident ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
        type_prefix = incident_type[:3].upper()
        location_prefix = location[:3].upper()
        return f"INC-{type_prefix}-{location_prefix}-{timestamp}"

    async def start(self) -> None:
        """Start the Telegram bot."""
        if not self.bot_token:
            self.logger.warning("No Telegram bot token found. Running in stub mode.")
            self.is_running = True
            return

        if not self.redis_client:
            self.logger.error("Cannot start bot: Redis connection failed")
            raise RuntimeError("Redis connection failed")

        try:
            # Initialize direct bot instance for sending messages without polling
            self.bot = Bot(token=self.bot_token)
            
            # Test connection
            me = await self.bot.get_me()
            self.logger.info(f"Application started")
            
            # Delete webhook to ensure clean start
            await self.bot.delete_webhook()
            
            self.is_running = True
            self.logger.info("Telegram bot started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Telegram bot: {e}")
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Stop the Telegram bot."""
        self.is_running = False
        self.logger.info("Telegram bot stopped")
        
        # Clear the singleton instance
        global _bot_instance
        _bot_instance = None

    async def _get_active_incidents(self) -> List[Dict[str, Any]]:
        """Get all active incidents from Redis."""
        if not self.redis_client:
            self.logger.error("Cannot get incidents: Redis not connected")
            return []

        try:
            # Get all incident keys
            incident_keys = self.redis_client.keys("incident:*")
            active_incidents = []
            
            for key in incident_keys:
                incident_data = self.redis_client.hgetall(key)
                if incident_data.get("status") == "active":
                    # Generate a simple incident ID if not exists
                    if "simple_id" not in incident_data:
                        simple_id = self._generate_incident_id(
                            incident_data.get("type", "unknown"),
                            incident_data.get("location", "unknown")
                        )
                        self.redis_client.hset(key, "simple_id", simple_id)
                        incident_data["simple_id"] = simple_id
                    else:
                        incident_data["simple_id"] = incident_data["simple_id"]
                    
                    incident_data["id"] = key
                    active_incidents.append(incident_data)
            
            return active_incidents
        except Exception as e:
            self.logger.error(f"Error getting active incidents: {e}")
            return []

    async def _incidents_command(self, update: Update, context) -> None:
        """Handle /incidents command to show active incidents."""
        active_incidents = await self._get_active_incidents()
        
        if not active_incidents:
            await update.message.reply_text("✅ No active incidents at the moment.")
            return

        message = "🚨 *Active Incidents*\n\n"
        keyboard = []
        
        for incident in active_incidents:
            message += (
                f"*ID:* `{incident['simple_id']}`\n"
                f"*Type:* {incident['type'].title()}\n"
                f"*Location:* {incident['location']}\n"
                f"*Affected Areas:* {incident['affected_areas']}\n"
                f"*Services:* {incident['affected_services']}\n"
                f"*Reported:* {incident['created_at']}\n\n"
            )
            keyboard.append([
                InlineKeyboardButton(
                    f"Resolve {incident['simple_id']}",
                    callback_data=f"resolve_{incident['id']}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    async def _resolve_command(self, update: Update, context) -> None:
        """Handle /resolve command to resolve an incident."""
        if not context.args:
            await update.message.reply_text(
                "Please provide an incident ID to resolve.\n"
                "Use /incidents to see active incidents."
            )
            return

        incident_id = context.args[0]
        try:
            # Update incident status
            self.redis_client.hset(incident_id, "status", "resolved")
            self.redis_client.hset(incident_id, "resolved_at", datetime.utcnow().isoformat())
            
            await update.message.reply_text(
                f"✅ Incident {incident_id} has been resolved."
            )
        except Exception as e:
            self.logger.error(f"Error resolving incident: {e}")
            await update.message.reply_text(
                "❌ Failed to resolve incident. Please try again."
            )

    async def _handle_callback(self, update: Update, context) -> None:
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("resolve_"):
            incident_id = query.data.split("_")[1]
            try:
                # Update incident status
                self.redis_client.hset(incident_id, "status", "resolved")
                self.redis_client.hset(incident_id, "resolved_at", datetime.utcnow().isoformat())
                
                await query.edit_message_text(
                    f"✅ Incident has been resolved.\n"
                    f"Use /incidents to see remaining active incidents."
                )
            except Exception as e:
                self.logger.error(f"Error resolving incident: {e}")
                await query.edit_message_text(
                    "❌ Failed to resolve incident. Please try again."
                )

    async def _status_command(self, update: Update, context) -> None:
        """Handle /status command to show bot and system status."""
        active_incidents = await self._get_active_incidents()
        
        status_message = (
            f"🤖 *Bot Status*\n"
            f"Status: {'✅ Running' if self.is_running else '❌ Stopped'}\n\n"
            f"🚨 *Active Incidents*\n"
        )
        
        if active_incidents:
            status_message += f"Found {len(active_incidents)} active incidents:\n\n"
            for incident in active_incidents:
                status_message += (
                    f"• *ID:* `{incident['simple_id']}`\n"
                    f"  Type: {incident['type'].title()}\n"
                    f"  Location: {incident['location']}\n"
                    f"  Affected: {incident['affected_services']}\n"
                    f"  Reported: {incident['created_at']}\n\n"
                )
        else:
            status_message += "✅ No active incidents"
            
        await update.message.reply_text(
            status_message,
            parse_mode="Markdown"
        )

    async def _help_command(self, update: Update, context) -> None:
        """Handle /help command."""
        help_text = (
            "🤖 *Available Commands*\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Check bot and system status\n"
            "/incidents - List active incidents\n"
            "/resolve <incident_id> - Resolve an incident\n\n"
            "You can also use the inline buttons in the /incidents command to resolve incidents."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def send_call_report(
        self,
        phone: Optional[str],
        issue: str,
        call_summary: str,
        recent_transcripts: List[str],
        customer_info: Dict[str, Any],
        call_status: str,
        resolution: str,
        duration: int,
        was_resolved: bool,
        troubleshooting_steps: List[str] = None,
        caller_phone: Optional[str] = None
    ) -> None:
        """Send a call report to the operator."""
        if not self.bot_token or not self.operator_chat_id:
            self.logger.warning("Cannot send call report: Telegram bot not configured")
            return

        try:
            # Use the instance's bot object instead of creating a new one
            if not self.bot:
                self.bot = Bot(token=self.bot_token)
            
            # Format duration
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}m {seconds}s"
            
            # Escape Markdown special characters to prevent parsing errors
            def escape_markdown(text):
                if not text:
                    return "Unknown"
                # Escape special Markdown characters: _ * [ ] ( ) ~ ` > # + - = | { } . !
                special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                for char in special_chars:
                    text = text.replace(char, f"\\{char}")
                return text
            
            # Format the message without Markdown in critical fields
            message = (
                f"📞 Call Report\n\n"
            )
            
            # Add phone numbers section
            if caller_phone:
                message += f"Called From: {caller_phone}\n"
            if phone:
                message += f"Registered Phone: {phone}\n"
            if not caller_phone and not phone:
                message += "Phone: Unknown\n"
                
            message += (
                f"Status: {call_status}\n"
                f"Duration: {duration_str}\n"
                f"Resolved: {'Yes' if was_resolved else 'No'}\n\n"
            )
            
            # Add complete customer info if available
            if customer_info:
                message += "Customer Info:\n"
                message += f"Name: {escape_markdown(customer_info.get('Customer Name', customer_info.get('name', 'Unknown')))}\n"
                message += f"Provider: {escape_markdown(customer_info.get('Provider', customer_info.get('isp', 'Unknown')))}\n"
                message += f"Region: {escape_markdown(customer_info.get('Region', 'Unknown'))}\n"
                message += f"Plan: {escape_markdown(customer_info.get('Current Plan', customer_info.get('plan', 'Unknown')))}\n"
                message += f"Operator: {escape_markdown(customer_info.get('Operator', customer_info.get('operator', 'Unknown')))}\n"
                message += f"Username: {escape_markdown(customer_info.get('User Name', customer_info.get('username', 'Unknown')))}\n"
                message += f"Address: {escape_markdown(customer_info.get('Address', 'Unknown'))}\n"
                message += f"Subscriber Code: {escape_markdown(customer_info.get('Subscriber Code', 'Unknown'))}\n\n"
            
            # Add issue section
            message += f"Issue:\n{escape_markdown(issue)}\n\n"
            
            # Add steps tried section (from troubleshooting_steps if available, otherwise from transcripts)
            message += "Steps Tried:\n"
            if troubleshooting_steps and len(troubleshooting_steps) > 0:
                for step in troubleshooting_steps[:5]:  # Limit to 5 steps
                    message += f"• {escape_markdown(step)}\n"
            elif recent_transcripts:
                for transcript in recent_transcripts[:3]:
                    message += f"• {escape_markdown(transcript)}\n"
            else:
                message += "No troubleshooting steps recorded\n"
            message += "\n"
            
            # Add summary section
            message += f"Summary:\n{escape_markdown(call_summary)}\n\n"
            
            # Add resolution
            message += f"Resolution:\n{escape_markdown(resolution)}"
            
            # Add customer statements if they're different from troubleshooting steps
            if recent_transcripts and (not troubleshooting_steps or len(troubleshooting_steps) == 0):
                message += "\n\nKey Customer Statements:\n"
                for transcript in recent_transcripts[:3]:
                    message += f"• {escape_markdown(transcript)}\n"
            
            # Send message without parse_mode to avoid Markdown parsing errors
            await self.bot.send_message(
                chat_id=self.operator_chat_id,
                text=message
            )
            self.logger.info(f"Call report sent for phone: {phone}")
            
        except Exception as e:
            self.logger.error(f"Failed to send call report: {e}")
            self.logger.error(f"Exception details: {str(e)}")
            # Try sending a simplified message if the formatted one failed
            try:
                simple_message = f"Call report for {phone}: {issue} - {resolution}"
                if not self.bot:
                    self.bot = Bot(token=self.bot_token)
                await self.bot.send_message(
                    chat_id=self.operator_chat_id,
                    text=simple_message
                )
                self.logger.info("Sent simplified call report after error")
            except Exception as e2:
                self.logger.error(f"Failed to send simplified call report: {e2}")

    async def _start_command(self, update, context):
        """Handle /start command."""
        await update.message.reply_text(
            "Welcome to the Customer Support Bot! Use /help to see available commands."
        )

    async def _handle_message(self, update, context):
        """Handle regular text messages."""
        await update.message.reply_text(
            "I'm a support bot. Please use /help to see available commands."
        ) 